from discord import Embed, Color
from discord.ext.commands import Cog, Context, command, Bot, cooldown, BucketType
from .utils.constants import Emojis
import aiohttp

BAD_RESPONSES = {
    404: "Issue/pull request not Found! Please enter a valid PR Number!",
    403: "Rate limit is hit! Please try again later!"
}


class Github(Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.session = aiohttp.ClientSession()

    @classmethod
    def generate_description(cls, description: str, stars: str, forks: str, command: str) -> str:
        return f"*{description}*\nStars: {stars} Forks: {forks}\n Command: {command}"

    @command()
    @cooldown(1, 5, type=BucketType.user)
    async def issue(self, ctx: Context, number: int, repository: str = "HotWired-Bot", user: str = "The-Codin-Hole") -> None:
        """Command to retrieve issues from a GitHub repository."""
        url = f"https://api.github.com/repos/{user}/{repository}/issues/{number}"
        merge_url = f"https://api.github.com/repos/{user}/{repository}/pulls/{number}/merge"

        async with self.session.get(url) as resp:
            json_data = await resp.json()

        if resp.status in BAD_RESPONSES:
            await ctx.send(f"ERROR CODE : [{str(resp.status)}] {BAD_RESPONSES.get(resp.status)}")
            return

        if "issues" in json_data.get("html_url"):
            if json_data.get("state") == "open":
                icon_url = Emojis.issue
            else:
                icon_url = Emojis.issue_closed
        else:
            async with self.session.get(merge_url) as m:
                if json_data.get("state") == "open":
                    icon_url = Emojis.pull_request
                elif m.status == 204:
                    icon_url = Emojis.merge
                else:
                    icon_url = Emojis.pull_request_closed

        issue_url = json_data.get("html_url")
        description_text = f"[{repository}] #{number} {json_data.get('title')}"
        resp = Embed(
            colour=Color.bright_green(),
            description=f"{icon_url} [{description_text}]({issue_url})"
        )
        resp.set_author(name="GitHub", url=issue_url)
        await ctx.send(embed=resp)

    @command(aliases=["ghrepo"])
    @cooldown(1, 5, type=BucketType.user)
    async def github(self, ctx: Context, repo: str) -> None:
        """
        This command uses the GitHub API, and is limited
        to 1 use per 5 seconds to comply with the rules.
        """
        embed = Embed(color=Color.blue())
        async with await self.session.get(
            f"https://api.github.com/repos/{repo}"
        ) as r:
            if r.status == 200:
                r = await r.json()

                if r["description"] == "":
                    desc = "No description provided."
                else:
                    desc = r["description"]

                stars = r["stargazers_count"]
                forks = r["forks_count"]
                cmd = f'git clone {r["clone_url"]}'
                embed.title = f"{repo} on GitHub"
                embed.description = self.generate_description(desc, stars, forks, cmd)
            elif r.status == 404:
                embed.title = "Oh No!"
                embed.description = "That repository doesn't seem to exist, or is private. Are you sure you typed it correctly?"

            await ctx.send(embed=embed)


def setup(bot: Bot) -> None:
    bot.add_cog(Github(bot))
