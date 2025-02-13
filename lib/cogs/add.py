import asyncio
import os

import discord
from discord.ext.commands import Bot as BotBase
from discord.ext.commands import Cog, command

from utils.funcs import delete_messages, save_checklists, send_basic_message


class Add(Cog):
    """
    Cog that manages the 'add' command for checklists.
    """
    def __init__(self, bot: BotBase) -> None:
        self.bot = bot

    # Command: Add tasks interactively to a checklist with reaction-based selection
    @command(name="add", help="Add one or more tasks interactively to a checklist.")
    async def add_task_interactively(self, ctx):
        try:
            # Initialize user ID and their checklists
            user_id = str(ctx.author.id)
            if user_id not in self.bot.checklists:
                self.bot.checklists[user_id] = {}

            # Check if user has any checklists to select from
            if not self.bot.checklists[user_id]:
                embed = discord.Embed(
                    title="No Checklists Saved 🛑",
                    description="You don't have any checklists. Please create one first using `@ToDoBot create`.",
                    color=discord.Color.red()
                )
                await send_basic_message(self.bot.logger, ctx, embed=embed)
                self.bot.logger.info(f"User {user_id} doesn't have any checklists saved.")
                return

            # Prepare the checklist names and corresponding reactions
            checklist_names = list(self.bot.checklists[user_id].keys())
            reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣']  # Max 5 checklists can be selected

            # Create an embed with the list of checklists
            init_embed = discord.Embed(
                title="Select a Checklist ✏️",
                description="Please select a checklist from the list below by reacting with the corresponding emoji.\n\n" +
                            "\n".join([f"{reactions[i]} - {checklist_names[i]}" for i in range(len(checklist_names))]),
                color=discord.Color.blue()
            )
            init_embed.set_footer(text="You have 60 seconds to respond.")
            init_message = await ctx.send(embed=init_embed)

            # Add reactions for user to select the checklist
            for i in range(len(checklist_names)):
                await init_message.add_reaction(reactions[i])

            # Reaction check function
            def reaction_check(reaction, user):
                return user == ctx.author and reaction.message.id == init_message.id and reaction.emoji in reactions[:len(checklist_names)]

            try:
                # Wait for the user to react
                reaction, _ = await self.bot.wait_for('reaction_add', check=reaction_check, timeout=60.0)
                
                # Find the checklist selected based on the reaction
                selected_index = reactions.index(reaction.emoji)
                list_name = checklist_names[selected_index]
                
                # Confirm selection to the user
                confirmation_embed = discord.Embed(
                    title=f"✅ You selected the checklist: **{list_name}**",
                    color=discord.Color.blue()
                )
                confirmation_message = await ctx.send(embed=confirmation_embed)

                # Inner loop: prompt the user for tasks to add
                prev_error_msg = None  # Track previous error message
                while True:
                    # Task addition prompt
                    prompt_embed = discord.Embed(
                        title=f"Add Tasks to: **{list_name}** ✏️",
                        description="Please provide the tasks you want to add, separated by commas. Type `cancel` to exit.",
                        color=discord.Color.blue()
                    )
                    prompt_embed.set_footer(text="You have 60 seconds to respond.")
                    tasks_message = await ctx.send(embed=prompt_embed)

                    # Message check function for task input
                    def message_check(message):
                        return message.author == ctx.author and message.channel == ctx.channel

                    try:
                        # Wait for user input (tasks)
                        response = await self.bot.wait_for('message', check=message_check, timeout=60.0)
                        task_input = response.content.strip()

                        # Delete any previous error message (if still lingering)
                        if prev_error_msg is not None:
                            try:
                                await prev_error_msg.delete()
                            except Exception as e:
                                self.bot.logger.error(f"Failed to delete previous error message: {e}")
                            prev_error_msg = None

                        # Handle cancellation
                        if task_input.lower() == "cancel":
                            cancel_embed = discord.Embed(
                                title="Task Addition Canceled ⚠️",
                                description="You canceled the task addition process.",
                                color=discord.Color.orange()
                            )
                            await send_basic_message(self.bot.logger, ctx, embed=cancel_embed)
                            await delete_messages(self.bot.logger, init_message, confirmation_message, tasks_message, response)
                            return

                        # Edge case handling for empty responses
                        if not task_input:
                            error_embed = discord.Embed(
                                title="Invalid Input ⚠️",
                                description="You didn't provide any tasks. Please try again.",
                                color=discord.Color.red()
                            )
                            prev_error_msg = await ctx.send(embed=error_embed)
                            await delete_messages(self.bot.logger, tasks_message, response)
                            continue  # Retry the process if no tasks were provided

                        # Split tasks by commas and clean up
                        task_list = [task.strip() for task in task_input.split(",") if task.strip()]
                        if not task_list:
                            error_embed = discord.Embed(
                                title="No Valid Tasks ⚠️",
                                description="No valid tasks were provided. Please try again.",
                                color=discord.Color.red()
                            )
                            prev_error_msg = await ctx.send(embed=error_embed)
                            await delete_messages(self.bot.logger, tasks_message, response)
                            continue  # Retry if no tasks are valid

                        # Add tasks to the checklist
                        for task in task_list:
                            self.bot.checklists[user_id][list_name].append({"task": task, "completed": False})

                        save_checklists(self.bot.checklist_file_name, self.bot.checklists)

                        # Send success message with added tasks
                        added_tasks = "\n".join([f"- {task}" for task in task_list])
                        success_embed = discord.Embed(
                            title="Tasks Added ✅",
                            description=f"Successfully added the following tasks to **{list_name}**:\n{added_tasks}",
                            color=discord.Color.green()
                        )
                        await send_basic_message(self.bot.logger, ctx, embed=success_embed)
                        await delete_messages(self.bot.logger, init_message, confirmation_message, tasks_message, response)
                        # Clean up any previous error message.
                        if prev_error_msg is not None:
                            try:
                                await prev_error_msg.delete()
                            except Exception as e:
                                self.bot.logger.error(f"Failed to delete previous error message: {e}")
                            prev_error_msg = None
                        return  # Exit the loop once tasks are successfully added

                    except asyncio.TimeoutError:
                        timeout_embed = discord.Embed(
                            title="Timeout ⚠️",
                            description="You took too long to respond. Task addition canceled.",
                            color=discord.Color.orange()
                        )
                        await send_basic_message(self.bot.logger, ctx, embed=timeout_embed)
                        await delete_messages(self.bot.logger, init_message, confirmation_message, tasks_message)
                        return

            except asyncio.TimeoutError:
                timeout_embed = discord.Embed(
                    title="Timeout ⚠️",
                    description="You took too long to select a checklist. Task addition canceled.",
                    color=discord.Color.orange()
                )
                await send_basic_message(self.bot.logger, ctx, embed=timeout_embed)
                await delete_messages(self.bot.logger, init_message)
                return

        except Exception as e:
            await send_basic_message(self.bot.logger, ctx, f"An error occurred while adding tasks: {e}")
            self.bot.logger.error(f"An error occurred in the 'add' command: {e}")

    @Cog.listener()
    async def on_ready(self: Cog) -> None:
        # Ready up the cog when the bot is ready.
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up(__name__.split(".")[-1])

async def setup(bot: BotBase) -> None:
    """
    Adds the Add cog to the bot.
    """
    await bot.add_cog(Add(bot))
