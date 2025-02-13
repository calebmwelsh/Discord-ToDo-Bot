import asyncio
import os

import discord
from discord.ext.commands import Bot as BotBase
from discord.ext.commands import Cog, command

from utils.funcs import delete_messages, save_checklists, send_basic_message


class Create(Cog):
    """
    Cog that manages interactive checklist creation.
    """
    def __init__(self, bot: BotBase) -> None:
        self.bot = bot

    @command(name="create", help="Create a new checklist interactively.")
    async def create_list(self, ctx):
        user_id = str(ctx.author.id)
        if user_id not in self.bot.checklists:
            self.bot.checklists[user_id] = {}

        # Variable to store the last error message (if any)
        prev_error_msg = None

        while True:
            # Send an interactive prompt asking for the checklist name.
            prompt_embed = discord.Embed(
                title="Create a New Checklist ✏️",
                description="Please provide the `name` of your new checklist. Type `cancel` to exit.",
                color=discord.Color.blue()
            )
            prompt_embed.set_footer(text="You have 60 seconds to respond.")
            prompt_message = await ctx.send(embed=prompt_embed)
            if prompt_message is None:
                self.bot.logger.error("Failed to send the checklist creation prompt.")
                return

            # Check that the response comes from the same author and channel.
            def check(message):
                return message.author == ctx.author and message.channel == ctx.channel

            try:
                response = await self.bot.wait_for('message', check=check, timeout=60.0)
                list_name = response.content.strip()

                # Delete any lingering error message immediately.
                if prev_error_msg is not None:
                    try:
                        await prev_error_msg.delete()
                    except Exception as e:
                        self.bot.logger.error(f"Failed to delete previous error message: {e}")
                    prev_error_msg = None

                # Handle empty input (edge case)
                if not list_name:
                    invalid_embed = discord.Embed(
                        title="Invalid Input ⚠️",
                        description="You didn't provide a name for the checklist. Please try again.",
                        color=discord.Color.orange()
                    )
                    prev_error_msg = await ctx.send(embed=invalid_embed)
                    await delete_messages(self.bot.logger, prompt_message, response, wait=0)
                    continue

                # Handle cancellation
                if list_name.lower() == "cancel":
                    cancel_embed = discord.Embed(
                        title="Checklist Creation Canceled ⚠️",
                        description="You canceled the checklist creation process.",
                        color=discord.Color.orange()
                    )
                    await send_basic_message(self.bot.logger, ctx, embed=cancel_embed)
                    await delete_messages(self.bot.logger, prompt_message, response, wait=0)
                    return

                # Check if the checklist already exists
                if list_name in self.bot.checklists[user_id]:
                    exists_embed = discord.Embed(
                        title="Checklist Already Exists 🛑",
                        description=f"The checklist **{list_name}** already exists! Please try a different name.",
                        color=discord.Color.red()
                    )
                    prev_error_msg = await ctx.send(embed=exists_embed)
                    await delete_messages(self.bot.logger, prompt_message, response, wait=0)
                    continue

                # Create the new checklist if all validations pass.
                self.bot.checklists[user_id][list_name] = []
                save_checklists(self.bot.checklist_file_name, self.bot.checklists)

                success_embed = discord.Embed(
                    title="Checklist Created ✅",
                    description=f"Successfully created a new checklist: **{list_name}**",
                    color=discord.Color.green()
                )
                await send_basic_message(self.bot.logger, ctx, embed=success_embed, wait=30)
                await delete_messages(self.bot.logger, prompt_message, response, wait=0)
                # Clean up any previous error message.
                if prev_error_msg is not None:
                    try:
                        await prev_error_msg.delete()
                    except Exception as e:
                        self.bot.logger.error(f"Failed to delete previous error message: {e}")
                    prev_error_msg = None
                return

            except asyncio.TimeoutError:
                timeout_embed = discord.Embed(
                    title="Timeout ⚠️",
                    description="You took too long to respond. Checklist Creation Canceled ⚠️",
                    color=discord.Color.orange()
                )
                await send_basic_message(self.bot.logger, ctx, embed=timeout_embed, wait=30)
                await delete_messages(self.bot.logger, prompt_message, wait=0)
                self.bot.logger.error("Timeout waiting for checklist name response.")
                return

    @Cog.listener()
    async def on_ready(self) -> None:
        # Ready up the cog when the bot is ready.
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up(__name__.split(".")[-1])

async def setup(bot: BotBase) -> None:
    """
    Adds the Create cog to the bot.
    """
    await bot.add_cog(Create(bot))
