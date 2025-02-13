import asyncio
import os

import discord
from discord.ext.commands import Bot as BotBase
from discord.ext.commands import Cog, command

from utils.funcs import *


class Check(Cog):
    """
    Cog that manages the 'check' command for marking tasks as complete.
    """
    def __init__(self, bot: BotBase) -> None:
        self.bot = bot

    @command(name="check", help="Mark one or more tasks as complete.")
    async def check_task(self, ctx):
        user_id = str(ctx.author.id)
        # Track the previous error message
        prev_error_msg = None  

        # Main loop to allow retries
        while True:
            # Check if the user has any checklists
            if user_id not in self.bot.checklists or not self.bot.checklists[user_id]:
                embed = discord.Embed(
                    title="No Checklists Saved 🛑",
                    description="You don't have any checklists. Please create one first using `@ToDoBot create`.",
                    color=discord.Color.red()
                )
                self.bot.logger.info(f"User {user_id} has no checklists saved.")
                await send_basic_message(self.bot.logger, ctx, embed=embed)
                return

            # List the checklists to choose from
            checklist_names = list(self.bot.checklists[user_id].keys())
            reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']

            init_embed = discord.Embed(
                title="Select a Checklist to Mark Tasks as Complete ✨",
                description="Please select a checklist by reacting with the corresponding emoji.\n\n"
                            + "\n".join([f"{reactions[i]} - {checklist_names[i]}" for i in range(len(checklist_names))]),
                color=discord.Color.blue()
            )
            init_embed.set_footer(text="You have 60 seconds to respond.")
            checklist_message = await ctx.send(embed=init_embed)

            for i in range(len(checklist_names)):
                await checklist_message.add_reaction(reactions[i])

            def checklist_check(reaction, user):
                return user == ctx.author and reaction.message.id == checklist_message.id and reaction.emoji in reactions[:len(checklist_names)]

            try:
                reaction, _ = await self.bot.wait_for('reaction_add', check=checklist_check, timeout=60.0)

                # Delete any previous error message (if still lingering)
                if prev_error_msg is not None:
                    try:
                        await prev_error_msg.delete()
                    except Exception as e:
                        self.bot.logger.error(f"Failed to delete previous error message: {e}")
                    prev_error_msg = None

                selected_index = reactions.index(reaction.emoji)
                list_name = checklist_names[selected_index]
                tasks = self.bot.checklists[user_id][list_name]

                # Paginate tasks
                tasks_per_page = 10
                task_pages = [
                    tasks[i:i + tasks_per_page] for i in range(0, len(tasks), tasks_per_page)
                ]
                page_index = 0

                # Check if tasks are empty
                if not tasks:
                    error_embed = discord.Embed(
                        title="Task List Empty ⚠️",
                        description="No tasks in checklist. Please try again.",
                        color=discord.Color.red()
                    )
                    prev_error_msg = await ctx.send(embed=error_embed)
                    await delete_messages(self.bot.logger, checklist_message)
                    continue  # Restart the loop to allow the user to select a different checklist

                # Embed for task selection
                def update_embed():
                    task_descriptions = [
                        f"{i + 1 + page_index * tasks_per_page}. {'✅' if task['completed'] else '❌'} {task['task']}"
                        for i, task in enumerate(task_pages[page_index])
                    ]
                    embed = discord.Embed(
                        title=f"Tasks in **{list_name}**",
                        description="\n".join(task_descriptions),
                        color=discord.Color.blue()
                    )
                    embed.set_footer(text="Use reactions to navigate and toggle tasks. ✅ to confirm.")
                    return embed

                async def update_reactions():
                    """Updates reactions on the task message based on the current page."""
                    await task_message.clear_reactions()
                    for i in range(len(task_pages[page_index])):
                        await task_message.add_reaction(reactions[i])
                    if len(task_pages) > 1:
                        if page_index > 0:
                            await task_message.add_reaction('⬅️')  # Left arrow
                        if page_index < len(task_pages) - 1:
                            await task_message.add_reaction('➡️')  # Right arrow
                    await task_message.add_reaction('✅')  # Submit button

                task_message = await ctx.send(embed=update_embed())
                await update_reactions()

                def task_check(reaction, user):
                    valid_reactions = reactions[:len(task_pages[page_index])] + ['⬅️', '➡️', '✅']
                    return user == ctx.author and reaction.message.id == task_message.id and reaction.emoji in valid_reactions

                while True:
                    try:
                        reaction, _ = await self.bot.wait_for('reaction_add', check=task_check, timeout=60.0)

                        if reaction.emoji == '➡️' and page_index < len(task_pages) - 1:  # Next page
                            page_index += 1
                            await task_message.edit(embed=update_embed())
                            await update_reactions()

                        elif reaction.emoji == '⬅️' and page_index > 0:  # Previous page
                            page_index -= 1
                            await task_message.edit(embed=update_embed())
                            await update_reactions()

                        elif reaction.emoji == '✅':  # Submit selected tasks
                            save_checklists(self.bot.checklist_file_name, self.bot.checklists)
                            confirmation_embed = discord.Embed(
                                title="Tasks Updated",
                                description="The following tasks have been updated:\n" +
                                            "\n".join([f"{'✅' if task['completed'] else '❌'} {task['task']}" for task in tasks]),
                                color=discord.Color.green()
                            )
                            await send_basic_message(self.bot.logger, ctx, embed=confirmation_embed)
                            await delete_messages(self.bot.logger, checklist_message, task_message, prev_error_msg)
                            return  

                        else:
                            # Toggle the completion status of the task
                            task_index = reactions.index(reaction.emoji) + page_index * tasks_per_page
                            if task_index < len(tasks):
                                tasks[task_index]['completed'] = not tasks[task_index]['completed']

                                # Update the embed to reflect the toggled status
                                await task_message.edit(embed=update_embed())
                                await reaction.remove(ctx.author)

                    except asyncio.TimeoutError:
                        timeout_embed = discord.Embed(
                            title="Timeout ⚠️",
                            description="You took too long to respond. Task completion canceled.",
                            color=discord.Color.orange()
                        )
                        await send_basic_message(self.bot.logger, ctx, embed=timeout_embed)
                        await delete_messages(self.bot.logger, checklist_message, task_message, prev_error_msg)
                        return  

            except asyncio.TimeoutError:
                timeout_embed = discord.Embed(
                    title="Timeout ⚠️",
                    description="You took too long to select a checklist. Task completion canceled.",
                    color=discord.Color.orange()
                )
                await send_basic_message(self.bot.logger, ctx, embed=timeout_embed)
                await delete_messages(self.bot.logger, checklist_message, prev_error_msg)
                return  


    @Cog.listener()
    async def on_ready(self: Cog) -> None:
        # if bot is ready 
        if not self.bot.ready:
            # ready up cog
            self.bot.cogs_ready.ready_up(__name__.split(".")[-1])


async def setup(bot: BotBase) -> None:
    """
    Adds cog to bot
    """
    await bot.add_cog(Check(bot))