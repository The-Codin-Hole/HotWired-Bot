import aiohttp
import random

from discord import Color, Embed, Member
from discord.ext.commands import Cog, Context, command
from discord.ext import tasks

from bot import config
from bot.core.bot import Bot

from .hangman import HangmanGame
from .tic_tac_toe import TTT_Game
from .more_games import Connect4, Blackjack, Blackjack_players


class Games(Cog):
    """We all love playing games."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.blackjack_list = []
        self.blackjack_updater.start()

    def cog_unload(self) -> None:
        self.blackjack_updater.cancel()

    @tasks.loop(seconds=5)
    async def blackjack_updater(self) -> None:
        new = []
        for black in self.blackjack_list:
            if black.current_state == 1:
                await black.updater()
            elif black.current_state == -1:
                continue
            new.append(black)
        self.blackjack_list = new

    @command(ignore_extra=True)
    async def blackjack(self, ctx: Context, cost: int = 5) -> None:
        """
        Rules: if it's your turn, press the button corresponding to the column in which you want to place the card.
        If you want to split (play on one more column, up to a max of 3, press :regional_indicator_3:).  If you want to stop, press :x:.
        To win, you must score more than the dealer, but no more than 21 (each card's value is its pip value,
        except for faces, which are worth 10 points, and the Ace, which is worth either 1 or 11).
        An Ace plus a face is called a blackjack and beats a 21
        """
        if cost < 0:
            await ctx.send("You can't bet negative money")
        players, money_dict = await Blackjack_players(ctx.author, 100, cost, delete_message_after=True).prompt(ctx)
        if not players:
            return await ctx.send("Nobody wants to play")
        await Blackjack(players, money_dict, cost, clear_reactions_after=True).prompt(ctx)

    @command(aliases=["c4"])
    async def connect4(self, ctx: Context, member: Member) -> None:
        """Play connect 4 with a friend"""
        winner = await Connect4(ctx.author, member, clear_reactions_after=True).prompt(ctx)
        if winner:
            await ctx.send(f"{winner.mention} won !")
        else:
            await ctx.send("Game cancelled")

    @command()
    async def hangman(self, ctx: Context) -> None:
        """Play game of Hangman."""
        hangman_game = HangmanGame.random(ctx)
        await hangman_game.play()

    @command(aliases=["ttt", "tictactoe"])
    async def tic_tac_toe(self, ctx: Context, opponent: Member = None) -> None:
        """Play a game of Tic-Tac-Toe."""
        game = TTT_Game(ctx.author, opponent, clear_reactions_after=True)
        await game.start(ctx)

    @command()
    async def roll(self, ctx: Context, min_limit: int = 1, max_limit: int = 10) -> None:
        """Roll a random number."""
        if max_limit - min_limit > 2:
            number = random.randint(min_limit, max_limit)
            embed = Embed(title="Random Roll", color=Color.blurple(), description=f"The random number is: {number}")
            await ctx.send(embed=embed)
        else:
            embed = Embed(title="Random Roll", color=Color.red(), description="Please specify numbers with difference of **at least 2**")
            await ctx.send(embed=embed)

    @command(aliases=["8ball"])
    async def ball8(self, ctx: Context, *, question: str) -> None:
        """Ask the all-knowing 8ball your burning questions."""
        reply_type = random.randint(1, 3)

        if reply_type == 1:
            answer = random.choice(config.POSITIVE_REPLIES)
        elif reply_type == 2:
            answer = random.choice(config.NEGATIVE_REPLIES)
        elif reply_type == 3:
            answer = random.choice(config.ERROR_REPLIES)

        embed = Embed(title="Magic 8-ball", color=Color.blurple())
        embed.add_field(name="Question", value=question)
        embed.add_field(name="Answer", value=answer)

        await ctx.send(embed=embed)

    @command(aliases=["pokesearch"])
    async def pokemon(self, ctx: Context, pokemon: str) -> None:
        """
        Fetches data about a given pokemon eg. `pokemon pikachu`.
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://pokeapi.co/api/v2/pokemon/{pokemon}") as resp:
                data = await resp.json()

        pokemon_embed = Embed(
            title=f"{pokemon.capitalize()} Info",
            color=Color.blurple()
        )

        ability_names = [f"`{ability['ability']['name']}`" for ability in data["abilities"]]
        pokemon_types = [f"`{ptype_raw['type']['name']}`" for ptype_raw in data["types"]]
        base_stat_names = ["Hp", "Attack", "Defence", "Special-Attack", "Special-Defence", "Speed"]
        base_stats_zip = zip(base_stat_names, data["stats"])
        base_stats = [f"**{stat_name}**: `{str(base_stat_dict['base_stat'])}`" for stat_name, base_stat_dict in base_stats_zip]

        pokemon_embed.set_thumbnail(url=data["sprites"]["front_default"])
        pokemon_embed.add_field(name="❯❯Base Stats", value="\n ".join(base_stats))
        pokemon_embed.add_field(name="❯❯Type", value="\n".join(pokemon_types))
        pokemon_embed.add_field(name="❯❯Weight", value=f"`{str(data['weight'])}`")
        pokemon_embed.add_field(name="❯❯Abilities", value="\n".join(ability_names), inline=True)

        await ctx.send(embed=pokemon_embed)

    @command(aliases=["wyr"])
    async def wouldyourather(self, ctx: Context) -> None:
        """Would you rather?."""
        strings = config.talk_games["wyr"]
        choices = len(strings)
        i = random.randint(0, choices - 1)

        embed = Embed(
            title="Would you rather?",
            description=f"Would you rather ..{strings[i]}",
            color=Color.dark_magenta()
        )
        await ctx.send(embed=embed)

    @command(aliases=["havei"])
    async def haveiever(self, ctx: Context) -> None:
        """Have i Ever?."""
        strings = config.talk_games["nhie"]
        choices = len(strings)
        i = random.randint(0, choices - 1)

        embed = Embed(
            title="Have I ever?",
            description=f"Have you ever ..{strings[i]}",
            color=Color.dark_magenta()
        )
        await ctx.send(embed=embed)

    @command()
    async def truth(self, ctx: Context, *, user: Member) -> None:
        """Ask a truth question to a random user."""
        strings = config.talk_games["truths"]
        str_len = len(strings)
        random_truth = random.randint(0, str_len - 1)

        # TODO: choose only non-offline users
        member_len = len(ctx.guild.members)
        random_user = random.randint(0, member_len - 1)
        name = ctx.guild.members[random_user].mention

        embed = Embed(
            title=f"{ctx.author.name} asked {user.name}",
            description=strings[random_truth].format(name=name),
            color=Color.dark_magenta()
        )
        await ctx.send(embed=embed)

    @command()
    async def dare(self, ctx: Context, *, user: Member) -> None:
        """Dare someone."""
        strings = config.talk_games["dares"]
        str_len = len(strings)
        random_dare = random.randint(0, str_len - 1)

        # TODO: choose only non-offline users
        member_len = len(ctx.guild.members)
        random_user = random.randint(0, member_len - 1)
        name = ctx.guild.members[random_user].mention

        embed = Embed(
            title=f"{ctx.author.name} dared {user.name}",
            description=strings[random_dare].format(name=name),
            color=Color.dark_magenta()
        )
        await ctx.send(embed=embed)
