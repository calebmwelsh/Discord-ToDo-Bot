import asyncio
import os

import discord
from discord import FFmpegPCMAudio
from discord.ext.commands import Bot as BotBase
from discord.ext.commands import Cog, command

from utils.funcs import *


class Clear(Cog):
    """
    Cog that manages the checklist-clearing command.
    """
    def __init__(self, bot: BotBase) -> None:
        self.bot = bot

    @command(name="clear", help="Clear all tasks in a checklist.")
    async def clear_tasks(self, ctx):
        user_id = str(ctx.author.id)
        prev_error_msg = None  # Track the previous error message

        # Check if the user has any checklists.
        if user_id not in self.bot.checklists or not self.bot.checklists[user_id]:
            embed = discord.Embed(
                title="No Checklists Found 🛑",
                description="You don't have any checklists. Please create one first.",
                color=discord.Color.red()
            )
            # This is a final message so we allow it to be auto-deleted after the default wait.
            await send_basic_message(self.bot.logger, ctx, embed=embed, wait=30)
            return

        # List the user's checklists
        checklist_names = list(self.bot.checklists[user_id].keys())
        reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']  # 1-10 reactions

        embed = discord.Embed(
            title="Select a Checklist to Clear Tasks ✨",
            description="Please select a checklist by reacting with the corresponding emoji.\n\n"
                        + "\n".join([f"{reactions[i]} - {checklist_names[i]}" for i in range(len(checklist_names))]),
            color=discord.Color.blue()
        )
        embed.set_footer(text="You have 60 seconds to respond.")
        
        checklist_message = await ctx.send(embed=embed)

        if checklist_message is None:
            self.bot.logger.error("Failed to send the checklist selection message.")
            return

        # Add emoji reactions corresponding to each checklist.
        for i in range(len(checklist_names)):
            try:
                await checklist_message.add_reaction(reactions[i])
            except Exception as e:
                self.bot.logger.error(f"Error adding reaction {reactions[i]}: {e}")

        def checklist_check(reaction, user):
            return (
                user == ctx.author and 
                reaction.message.id == checklist_message.id and 
                reaction.emoji in reactions[:len(checklist_names)]
            )

        try:
            # Wait for the user to select a checklist by reacting.
            reaction, _ = await self.bot.wait_for('reaction_add', check=checklist_check, timeout=60.0)
            selected_index = reactions.index(reaction.emoji)
            list_name = checklist_names[selected_index]

            # Ask for confirmation before clearing tasks.
            confirm_embed = discord.Embed(
                title=f"Clear All Tasks in **{list_name}**",
                description="Are you sure you want to clear all tasks in this checklist? React with ✅ to confirm, ❌ to cancel.",
                color=discord.Color.orange()
            )
            
            confirm_message = await ctx.send(embed=confirm_embed)
            
            if confirm_message is None:
                self.bot.logger.error("Failed to send the confirmation message.")
                return

            try:
                await confirm_message.add_reaction('✅')
                await confirm_message.add_reaction('❌')
            except Exception as e:
                self.bot.logger.error(f"Error adding confirmation reactions: {e}")
                return

            def confirm_check(reaction, user):
                return (
                    user == ctx.author and 
                    reaction.message.id == confirm_message.id and 
                    reaction.emoji in ['✅', '❌']
                )

            try:
                reaction, _ = await self.bot.wait_for('reaction_add', check=confirm_check, timeout=60.0)
                if reaction.emoji == '✅':
                    # Clear the selected checklist.
                    self.bot.checklists[user_id][list_name] = []
                    save_checklists(self.bot.checklist_file_name, self.bot.checklists)

                    cleared_embed = discord.Embed(
                        title="Tasks Cleared 🗑️",
                        description=f"All tasks in **{list_name}** have been cleared!",
                        color=discord.Color.green()
                    )
                    await send_basic_message(self.bot.logger, ctx, embed=cleared_embed)
                    await delete_messages(self.bot.logger, confirm_message, checklist_message)
                    
                    
                elif reaction.emoji == '❌':
                    cancel_embed = discord.Embed(
                        title="Action Canceled",
                        description="The task clearing has been canceled.",
                        color=discord.Color.red()
                    )
                    await send_basic_message(self.bot.logger, ctx, embed=cancel_embed)
                    await delete_messages(self.bot.logger, confirm_message, checklist_message)
                    
                    
            except asyncio.TimeoutError:
                timeout_embed = discord.Embed(
                    title="Timeout ⚠️",
                    description="You took too long to respond. The task clearing has been canceled.",
                    color=discord.Color.orange()
                )
                await send_basic_message(self.bot.logger, ctx, embed=timeout_embed)
                await delete_messages(self.bot.logger, confirm_message, checklist_message)
                self.bot.logger.error("Timeout waiting for confirmation reaction.")
                
        except asyncio.TimeoutError:
            timeout_embed = discord.Embed(
                title="Timeout ⚠️",
                description="You took too long to select a checklist. Task clearing canceled.",
                color=discord.Color.orange()
            )
            await send_basic_message(self.bot.logger, ctx, embed=timeout_embed)
            await delete_messages(self.bot.logger, checklist_message)
            self.bot.logger.error("Timeout waiting for checklist selection reaction.")

    @Cog.listener()
    async def on_ready(self) -> None:
        # Mark this cog as ready once the bot is up.
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up(__name__.split(".")[-1])


async def setup(bot: BotBase) -> None:
    """
    Adds the Clear cog to the bot.
    """
    await bot.add_cog(Clear(bot))