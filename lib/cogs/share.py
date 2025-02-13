import asyncio
import os

import discord
from discord import FFmpegPCMAudio
from discord.ext.commands import Bot as BotBase
from discord.ext.commands import Cog, command

from utils.funcs import *


class Share(Cog):
    """
    Cog that manages sharing a checklist interactively.
    """
    def __init__(self, bot: BotBase) -> None:
        self.bot = bot

    @command(name="share", help="Share a checklist with multiple users interactively.")
    async def share_checklist(self, ctx):
        prev_error_msg = None  # Track the previous error message
        try:
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

            # List the user's checklists and create reaction options
            checklist_names = list(self.bot.checklists[user_id].keys())
            reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']  # Supports up to 10 checklists

            embed = discord.Embed(
                title="Select a Checklist to Share ✨",
                description="Please select a checklist by reacting with the corresponding emoji.\n\n" +
                            "\n".join([f"{reactions[i]} - {checklist_names[i]}" for i in range(len(checklist_names))]),
                color=discord.Color.blue()
            )
            embed.set_footer(text="You have 60 seconds to respond.")
            # Use wait=0 so that the message persists for interaction.
            checklist_message = await ctx.send(embed=embed)
            
            if checklist_message is None:
                self.bot.logger.error("Failed to send checklist selection message.")
                return

            # Add reactions corresponding to each checklist
            for i in range(len(checklist_names)):
                try:
                    await checklist_message.add_reaction(reactions[i])
                except Exception as e:
                    self.bot.logger.error(f"Error adding reaction {reactions[i]}: {e}")

            def checklist_check(reaction, user):
                return (user == ctx.author and 
                        reaction.message.id == checklist_message.id and 
                        reaction.emoji in reactions[:len(checklist_names)])

            try:
                # Wait for the user to select a checklist
                reaction, _ = await self.bot.wait_for('reaction_add', check=checklist_check, timeout=60.0)
                selected_index = reactions.index(reaction.emoji)
                list_name = checklist_names[selected_index]

                while True:
                    # Prompt the user to mention the recipients
                    mention_prompt = discord.Embed(
                        title=f"Share Checklist **{list_name}**",
                        description=("Please mention the user(s) you want to share this checklist with. "
                                    "Separate mentions with spaces.\nExample: @user1 @user2"),
                        color=discord.Color.green()
                    )
                    mention_prompt.set_footer(text="You have 60 seconds to respond.")
                    mention_message = await ctx.send(embed=mention_prompt)
                    
                    if mention_message is None:
                        self.bot.logger.error("Failed to send the mention prompt.")
                        return

                    def mention_check(message):
                        return message.author == ctx.author and message.channel == ctx.channel

                    try:
                        # Wait for the user to provide the mentions
                        mention_response = await self.bot.wait_for('message', check=mention_check, timeout=60.0)
                        mentions = mention_response.content.split()
                        mentions = [mention for mention in mentions if mention.startswith("<@") and mention.endswith(">")]
                        
                        # Delete any previous error message before sending a new one
                        if prev_error_msg is not None:
                            try:
                                await prev_error_msg.delete()
                            except Exception as e:
                                self.bot.logger.error(f"Failed to delete previous error message: {e}")
                            prev_error_msg = None

                        if not mentions:
                            error_embed = discord.Embed(
                                title="⚠️ No Valid Mentions",
                                description=f"No valid mentions found for {mention_response.content.split()[0]}. The checklist won't be shared.",
                                color=discord.Color.red()
                            )
                            prev_error_msg = await ctx.send(embed=error_embed)
                            await delete_messages(self.bot.logger, mention_response, mention_message)
                            continue  # Restart the loop to allow the user to retry

                        # Share the checklist with each mentioned user
                        shared_with = []  # Users with whom sharing succeeded
                        errors = []       # Users for which a conflict occurred

                        for mention in mentions:
                            # Extract the recipient's user ID from the mention format
                            user_id_to_share = mention.strip("<@!>")
                            recipient_id = str(user_id_to_share)

                            # Initialize recipient's checklists if they don't exist
                            if recipient_id not in self.bot.checklists:
                                self.bot.checklists[recipient_id] = {}

                            # If a checklist with the same name exists for the recipient, record an error
                            if list_name in self.bot.checklists[recipient_id]:
                                errors.append(mention)
                            else:
                                self.bot.checklists[recipient_id][list_name] = self.bot.checklists[user_id][list_name]
                                shared_with.append(mention)

                        # Save the updated checklist data
                        save_checklists(self.bot.checklist_file_name, self.bot.checklists)

                        # Provide feedback to the user
                        if shared_with:
                            shared_embed = discord.Embed(
                                title="Checklist Shared Successfully ✅",
                                description=f"Checklist **{list_name}** has been shared with the following users:\n{', '.join(shared_with)}",
                                color=discord.Color.green()
                            )
                            await send_basic_message(self.bot.logger, ctx, embed=shared_embed)
                            await delete_messages(self.bot.logger, checklist_message, mention_message, mention_response)
                            
                        if errors:
                            error_embed = discord.Embed(
                                title="⚠️ Checklist Sharing Error",
                                description=("Couldn't share **{0}** with the following user(s) due to a checklist name conflict:\n"
                                            "{1}").format(list_name, ', '.join(errors)),
                                color=discord.Color.red()
                            )
                            await send_basic_message(self.bot.logger, ctx, embed=error_embed)
                            await delete_messages(self.bot.logger, checklist_message, mention_message, mention_response)
                            
                        return  

                    except asyncio.TimeoutError:
                        timeout_embed = discord.Embed(
                            title="Timeout ⚠️",
                            description="You took too long to provide mentions.  Checklist sharing canceled..",
                            color=discord.Color.orange()
                        )
                        await send_basic_message(self.bot.logger, ctx, embed=timeout_embed)
                        await delete_messages(self.bot.logger, checklist_message, mention_message, prev_error_msg)
                        self.bot.logger.error("Timeout during checklist sharing process.")
                        return 

            except asyncio.TimeoutError:
                timeout_embed = discord.Embed(
                    title="Timeout ⚠️",
                    description="You took too long to select a checklist. Checklist sharing canceled.",
                    color=discord.Color.orange()
                )
                await send_basic_message(self.bot.logger, ctx, embed=timeout_embed)
                await delete_messages(self.bot.logger, checklist_message, prev_error_msg)
                self.bot.logger.error("Timeout during checklist sharing process.")
                return

        except Exception as e:
            error_embed = discord.Embed(
                title="Error ⚠️",
                description=f"An error occurred while sharing the checklist: {e}",
                color=discord.Color.red()
            )
            await send_basic_message(self.bot.logger, ctx, embed=error_embed)
            self.bot.logger.error(f"An error occurred in the 'share' command: {e}")

    @Cog.listener()
    async def on_ready(self) -> None:
        # Ready up this cog when the bot is ready.
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up(__name__.split(".")[-1])

async def setup(bot: BotBase) -> None:
    """
    Adds the Share cog to the bot.
    """
    await bot.add_cog(Share(bot))