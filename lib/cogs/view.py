import asyncio
import os

import discord
from discord.ext.commands import Bot as BotBase
from discord.ext.commands import Cog, command

from utils.funcs import *


class View(Cog):
    """
    Cog that manages viewing tasks in a checklist interactively.
    """
    def __init__(self, bot: BotBase) -> None:
        self.bot = bot

    @command(name="view", help="View tasks in a checklist interactively.")
    async def view_tasks(self, ctx):
        user_id = str(ctx.author.id)

        # Check if the user has any checklists
        if user_id not in self.bot.checklists or not self.bot.checklists[user_id]:
            embed = discord.Embed(
                title="No Checklists Found 🛑",
                description="You don't have any checklists. Please create one first using `@ToDoBot create`.",
                color=discord.Color.red()
            )
            await send_basic_message(self.bot.logger, ctx, embed=embed)
            return

        # List the checklists to choose from
        checklist_names = list(self.bot.checklists[user_id].keys())
        reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']  # Supports up to 10 reactions

        embed = discord.Embed(
            title="Select a Checklist to View Tasks ✨",
            description="Please select a checklist by reacting with the corresponding emoji.\n\n" +
                        "\n".join([f"{reactions[i]} - {checklist_names[i]}" for i in range(len(checklist_names))]),
            color=discord.Color.blue()
        )
        embed.set_footer(text="You have 60 seconds to respond.")
        checklist_message = await ctx.send(embed=embed)

        if checklist_message is None:
            self.bot.logger.error("Failed to send checklist selection message.")
            return

        # Add reactions for the checklists
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
            # Wait for the user to select a checklist
            reaction, _ = await self.bot.wait_for('reaction_add', check=checklist_check, timeout=60.0)
            selected_index = reactions.index(reaction.emoji)
            list_name = checklist_names[selected_index]
            tasks = self.bot.checklists[user_id][list_name]

            if not tasks:
                embed = discord.Embed(
                    title=f"No Tasks in **{list_name}** 📋",
                    description="This checklist has no tasks yet. Please add tasks using `@ToDoBot add`.",
                    color=discord.Color.orange()
                )
                await send_basic_message(self.bot.logger, ctx, embed=embed)
                await delete_messages(self.bot.logger, checklist_message)
                return

            # Prepare the task list for display
            task_descriptions = [
                f"{i + 1}. {'✅' if task['completed'] else '❌'} {task['task']}"
                for i, task in enumerate(tasks)
            ]

            embed = discord.Embed(
                title=f"Tasks in **{list_name}**",
                description="\n".join(task_descriptions),
                color=discord.Color.blue()
            )
            embed.set_footer(text="✅ Task statuses displayed.")
            await send_basic_message(self.bot.logger, ctx, embed=embed, wait=60)
            await delete_messages(self.bot.logger, checklist_message)
            

        except asyncio.TimeoutError:
            timeout_embed = discord.Embed(
                title="Timeout ⚠️",
                description="You took too long to respond. Task view canceled.",
                color=discord.Color.orange()
            )
            await send_basic_message(self.bot.logger, ctx, embed=timeout_embed)
            await delete_messages(self.bot.logger, checklist_message)
            self.bot.logger.error("Timeout during checklist selection for viewing tasks.")

    @Cog.listener()
    async def on_ready(self) -> None:
        # Ready up the cog when the bot is ready.
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up(__name__.split(".")[-1])


async def setup(bot: BotBase) -> None:
    """
    Adds the View cog to the bot.
    """
    await bot.add_cog(View(bot))
