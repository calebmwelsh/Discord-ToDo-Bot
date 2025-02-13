import os
import discord
from discord.ext.commands import Bot as BotBase
from discord.ext.commands import Cog, command

from utils.funcs import *  # This imports send_basic_message and delete_messages among others


class List(Cog):
    """
    Cog that manages the list command.
    """
    def __init__(self, bot: BotBase) -> None:
        self.bot = bot

    @command(name="lists", help="View all your checklists.")
    async def view_lists(self, ctx):
        logger = self.bot.logger
        try:
            user_id = str(ctx.author.id)
            if user_id in self.bot.checklists and self.bot.checklists[user_id]:
                embed = discord.Embed(
                    title="Your Checklists",
                    description="Here are all your checklists:",
                    color=discord.Color.green(),
                )
                for list_name in self.bot.checklists[user_id].keys():
                    embed.add_field(
                        name=list_name, 
                        value="Use `@ToDoBot view` to see tasks.", 
                        inline=False
                    )
                await send_basic_message(logger, ctx, embed=embed, wait=60)
            else:
                embed = discord.Embed(
                    title="No Checklists 🛑",
                    description="You don't have any lists yet! Create one using `@ToDoBot create`.",
                    color=discord.Color.red(),
                )
                await send_basic_message(logger, ctx, embed=embed)
        except Exception as e:
            logger.error(f"Error in view_lists: {e}")
            error_embed = discord.Embed(
                title="Error",
                description="An error occurred while displaying your checklists.",
                color=discord.Color.red(),
            )
            await send_basic_message(logger, ctx, embed=error_embed)

    @Cog.listener()
    async def on_ready(self: Cog) -> None:
        # If the bot is ready, ready up this cog.
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up(__name__.split(".")[-1])


async def setup(bot: BotBase) -> None:
    """
    Adds the List cog to the bot.
    """
    await bot.add_cog(List(bot))
