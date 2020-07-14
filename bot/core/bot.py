import os
from datetime import datetime

import asyncpg
from discord import Color, Embed
from discord.ext.commands import Bot
from loguru import logger

from bot import config

DATABASE = {
    "host": "127.0.0.1",
    "database": os.getenv("DATABASE_NAME"),
    "user": os.getenv("DATABASE_USER"),
    "password": os.getenv("DATABASE_PASSWORD"),
    "min_size": int(os.getenv("POOL_MIN", "20")),
    "max_size": int(os.getenv("POOL_MAX", "100")),
}


class Bot(Bot):
    def __init__(self, extensions: list, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.extension_list = extensions
        self.initial_call = True

    async def on_ready(self) -> None:
        if self.initial_call:
            self.initial_call = False

            # connect to the database
            self.pool = await asyncpg.create_pool(**DATABASE)

            # Log new connection
            self.log_channel = self.get_channel(config.log_channel)
            embed = Embed(
                title="Bot Connection",
                description="New connection initialized.",
                timestamp=datetime.utcnow(),
                color=Color.dark_teal()
            )
            await self.log_channel.send(embed=embed)

            # Load all extensions
            for extension in self.extension_list:
                try:
                    self.load_extension(extension)
                    logger.debug(f"Cog {extension} loaded.")
                except Exception as e:
                    logger.error(f"Cog {extension} failed to load with {type(e)}: {e}")
        else:
            embed = Embed(
                title="Bot Connection",
                description="Connection re-initialized.",
                timestamp=datetime.utcnow(),
                color=Color.dark_teal()
            )
            await self.log_channel.send(embed=embed)

        logger.info("Bot is ready")

    async def close(self) -> None:
        await super().close()
        # In case bot doesn't get to on_ready
        if hasattr(self, "pool"):
            await self.pool.close()
