import asyncio
import json
import os

import discord
from discord.ext import commands

# Check for the environment variable for the Discord bot token
DISCORD_TOKEN = os.getenv('DISCORD_BOT_TOKEN', None)

if DISCORD_TOKEN is None:
    # If the environment variable isn't set, fall back to the .toml configuration file
    from utils import settings
    try:
        DISCORD_TOKEN = settings.config["General"]["DiscordBotToken"]
    # If the token is still not set, raise an error
    except TypeError:
        raise TypeError(
            "Discord bot token not found. Please set the DISCORD_BOT_TOKEN environment variable "
            "or ensure it is correctly defined in the .toml configuration file under [General]."
        )
    except AttributeError:
        raise ValueError(
            "Configuration file is not properly loaded. Please check your .toml file format."
        )
    
print(DISCORD_TOKEN)

# Enable intents
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

# Bot initialization using mentions
bot = commands.Bot(command_prefix=commands.when_mentioned_or("<ToDoBot> "), description="A ToDo bot with persistent checklists.", intents=intents)

# Directory and file to store checklist data
DATA_DIR = "data"
DATA_FILE = os.path.join(DATA_DIR, "checklists.json")

# Ensure the data directory exists
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Load existing checklists from the file, or initialize an empty dictionary
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as file:
        todo_checklists = json.load(file)
else:
    todo_checklists = {}

# Save checklists to the file
def save_checklists():
    with open(DATA_FILE, "w") as file:
        json.dump(todo_checklists, file, indent=4)

@bot.event
async def on_ready():
    print(f"Bot is online as {bot.user.name}!")
    
    
@bot.tree.command(name="hello", description="IDK")
async def say_hello(interaction: discord.Interaction):
    await interaction.response.send_message("Yoooooo")


# Command: Create an empty checklist interactively with retry functionality
@bot.command(name="create", help="Create a new checklist interactively.")
async def create_list(ctx):
    # Initialize user ID and their checklists
    user_id = str(ctx.author.id)
    if user_id not in todo_checklists:
        todo_checklists[user_id] = {}

    while True:
        # Send an embed requesting the checklist name
        embed = discord.Embed(
            title="Create a New Checklist ✏️",
            description="Please provide the `name` of your new checklist. Type `cancel` to exit.",
            color=discord.Color.blue()
        )
        embed.set_footer(text="You have 60 seconds to respond.")
        await ctx.send(embed=embed)

        # Function to check the response
        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel

        try:
            # Wait for user input
            response = await bot.wait_for('message', check=check, timeout=60.0)
            list_name = response.content.strip()
            
            # Edge case handling for empty responses - Discord doesnt allow empty message but jic
            if not list_name:
                embed = discord.Embed(
                    title="Invalid Input ⚠️",
                    description="You didn't provide a name for the checklist. Please try again.",
                    color=discord.Color.orange()
                )
                await ctx.send(embed=embed)
                continue  # Prompt the user again without continuing to the next steps

            # Handle cancellation
            if list_name.lower() == "cancel":
                cancel_embed = discord.Embed(
                    title="Checklist Creation Canceled ⚠️",
                    description="You canceled the checklist creation process.",
                    color=discord.Color.orange()
                )
                await ctx.send(embed=cancel_embed)
                # Exit the loop if cancelation occurs
                return

            # Check if the checklist already exists
            if list_name in todo_checklists[user_id]:
                # Send an embed for checklist already exists
                embed = discord.Embed(
                    title="Checklist Already Exists 🛑",
                    description=f"The checklist **{list_name}** already exists! Please try a different name.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
            else:
                # Create the checklist
                todo_checklists[user_id][list_name] = []
                save_checklists()  # Save to file

                # Send a success embed
                embed = discord.Embed(
                    title="Checklist Created ✅",
                    description=f"Successfully created a new checklist: **{list_name}**",
                    color=discord.Color.green()
                )
                await ctx.send(embed=embed)
                # Exit the loop once the checklist is successfully created
                return  

        except asyncio.TimeoutError:
            # Handle timeout
            timeout_embed = discord.Embed(
                title="Timeout ⚠️",
                description="You took too long to respond. Checklist Creation Canceled ⚠️",
                color=discord.Color.orange()
            )
            await ctx.send(embed=timeout_embed)
            # Exit the loop if timeout is achieved
            return

# Command: Add tasks interactively to a checklist with reaction-based selection
@bot.command(name="add", help="Add one or more tasks interactively to a checklist.")
async def add_task_interactively(ctx):
    # Initialize user ID and their checklists
    user_id = str(ctx.author.id)
    if user_id not in todo_checklists:
        todo_checklists[user_id] = {}

    # Check if user has any checklists to select from
    if not todo_checklists[user_id]:
        # Create an embed with the list of checklists
        embed = discord.Embed(
            title="No Checklists Saved 🛑",
            description="You don't have any checklists. Please create one first using `@ToDoBot create`.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    # Prepare the checklist names and corresponding reactions
    checklist_names = list(todo_checklists[user_id].keys())
    reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣']  # Max 5 checklists can be selected

    # Create an embed with the list of checklists
    embed = discord.Embed(
        title="Select a Checklist ✏️",
        description="Please select a checklist from the list below by reacting with the corresponding emoji.\n\n"
                    + "\n".join([f"{reactions[i]} - {checklist_names[i]}" for i in range(len(checklist_names))]),
        color=discord.Color.blue()
    )
    embed.set_footer(text="You have 60 seconds to respond.")
    message = await ctx.send(embed=embed)

    # Add reactions for user to select the checklist
    for i in range(len(checklist_names)):
        await message.add_reaction(reactions[i])

    # Reaction check function
    def reaction_check(reaction, user):
        return user == ctx.author and reaction.message.id == message.id and reaction.emoji in reactions[:len(checklist_names)]

    try:
        # Wait for the user to react
        reaction, _ = await bot.wait_for('reaction_add', check=reaction_check, timeout=60.0)
        
        # Find the checklist selected based on the reaction
        selected_index = reactions.index(reaction.emoji)
        list_name = checklist_names[selected_index]
        
        # Proceed to task addition process
        embed = discord.Embed(
                title=f"✅ You selected the checklist: **{list_name}**",
                color=discord.Color.blue()
            )
        await ctx.send(embed=embed)

        # Prompt the user for tasks to add
        while True:
            # Task addition prompt
            embed = discord.Embed(
                title=f"Add Tasks to: **{list_name}** ✏️",
                description="Please provide the tasks you want to add, separated by commas. Type `cancel` to exit.",
                color=discord.Color.blue()
            )
            embed.set_footer(text="You have 60 seconds to respond.")
            await ctx.send(embed=embed)

            # Message check function
            def message_check(message):
                return message.author == ctx.author and message.channel == ctx.channel

            try:
                # Wait for user input (tasks)
                response = await bot.wait_for('message', check=message_check, timeout=60.0)
                task_input = response.content.strip()

                # Handle cancellation
                if task_input.lower() == "cancel":
                    cancel_embed = discord.Embed(
                        title="Task Addition Canceled ⚠️",
                        description="You canceled the task addition process.",
                        color=discord.Color.orange()
                    )
                    await ctx.send(embed=cancel_embed)
                    return

                # Edge case handling for empty responses
                if not task_input:
                    embed = discord.Embed(
                        title="Invalid Input ⚠️",
                        description="You didn't provide any tasks. Please try again.",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=embed)
                    continue  # Retry the process if no tasks were provided

                # Split tasks by commas and clean up
                task_list = [task.strip() for task in task_input.split(",") if task.strip()]
                if not task_list:
                    embed = discord.Embed(
                        title="No Valid Tasks ⚠️",
                        description="No valid tasks were provided. Please try again.",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=embed)
                    continue  # Retry if no tasks are valid

                # Add tasks to the checklist
                for task in task_list:
                    todo_checklists[user_id][list_name].append({"task": task, "completed": False})

                save_checklists()  # Save data to file

                # Send success message with added tasks
                added_tasks = "\n".join([f"- {task}" for task in task_list])
                embed = discord.Embed(
                    title="Tasks Added ✅",
                    description=f"Successfully added the following tasks to **{list_name}**:\n{added_tasks}",
                    color=discord.Color.green()
                )
                await ctx.send(embed=embed)
                return  # Exit the loop once tasks are successfully added

            except asyncio.TimeoutError:
                timeout_embed = discord.Embed(
                    title="Timeout ⚠️",
                    description="You took too long to respond. Task addition canceled.",
                    color=discord.Color.orange()
                )
                await ctx.send(embed=timeout_embed)
                return

    except asyncio.TimeoutError:
        timeout_embed = discord.Embed(
            title="Timeout ⚠️",
            description="You took too long to select a checklist. Task addition canceled.",
            color=discord.Color.orange()
        )
        await ctx.send(embed=timeout_embed)
        return


@bot.command(name="check", help="Mark one or more tasks as complete.")
async def check_task(ctx):
    user_id = str(ctx.author.id)

    # Check if the user has any checklists
    if user_id not in todo_checklists or not todo_checklists[user_id]:
        embed = discord.Embed(
            title="No Checklists Saved 🛑",
            description="You don't have any checklists. Please create one first using `@ToDoBot create`.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    # List the checklists to choose from
    checklist_names = list(todo_checklists[user_id].keys())
    reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']

    embed = discord.Embed(
        title="Select a Checklist to Mark Tasks as Complete ✨",
        description="Please select a checklist by reacting with the corresponding emoji.\n\n"
                    + "\n".join([f"{reactions[i]} - {checklist_names[i]}" for i in range(len(checklist_names))]),
        color=discord.Color.blue()
    )
    embed.set_footer(text="You have 60 seconds to respond.")
    checklist_message = await ctx.send(embed=embed)

    for i in range(len(checklist_names)):
        await checklist_message.add_reaction(reactions[i])

    def checklist_check(reaction, user):
        return user == ctx.author and reaction.message.id == checklist_message.id and reaction.emoji in reactions[:len(checklist_names)]

    try:
        reaction, _ = await bot.wait_for('reaction_add', check=checklist_check, timeout=60.0)

        selected_index = reactions.index(reaction.emoji)
        list_name = checklist_names[selected_index]
        tasks = todo_checklists[user_id][list_name]

        # Paginate tasks
        tasks_per_page = 10
        task_pages = [
            tasks[i:i + tasks_per_page] for i in range(0, len(tasks), tasks_per_page)
        ]
        page_index = 0

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
            reaction, _ = await bot.wait_for('reaction_add', check=task_check, timeout=60.0)

            if reaction.emoji == '➡️' and page_index < len(task_pages) - 1:  # Next page
                page_index += 1
                await task_message.edit(embed=update_embed())
                await update_reactions()

            elif reaction.emoji == '⬅️' and page_index > 0:  # Previous page
                page_index -= 1
                await task_message.edit(embed=update_embed())
                await update_reactions()

            elif reaction.emoji == '✅':  # Submit selected tasks
                save_checklists()  # Save data to file
                confirmation_embed = discord.Embed(
                    title="Tasks Updated",
                    description="The following tasks have been updated:\n" +
                                "\n".join([f"{'✅' if task['completed'] else '❌'} {task['task']}" for task in tasks]),
                    color=discord.Color.green()
                )
                await ctx.send(embed=confirmation_embed)
                break

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
        await ctx.send(embed=timeout_embed)



@bot.command(name="view", help="View tasks in a checklist interactively.")
async def view_tasks(ctx):
    user_id = str(ctx.author.id)

    # Check if the user has any checklists
    if user_id not in todo_checklists or not todo_checklists[user_id]:
        embed = discord.Embed(
            title="No Checklists Found 🛑",
            description="You don't have any checklists. Please create one first using `@ToDoBot create`.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    # List the checklists to choose from
    checklist_names = list(todo_checklists[user_id].keys())
    reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']  # 1-10 reactions

    # Create an embed with the checklist names
    embed = discord.Embed(
        title="Select a Checklist to View Tasks ✨",
        description="Please select a checklist by reacting with the corresponding emoji.\n\n"
                    + "\n".join([f"{reactions[i]} - {checklist_names[i]}" for i in range(len(checklist_names))]),
        color=discord.Color.blue()
    )
    embed.set_footer(text="You have 60 seconds to respond.")
    checklist_message = await ctx.send(embed=embed)

    # Add reactions for the checklists
    for i in range(len(checklist_names)):
        await checklist_message.add_reaction(reactions[i])

    def checklist_check(reaction, user):
        return user == ctx.author and reaction.message.id == checklist_message.id and reaction.emoji in reactions[:len(checklist_names)]

    try:
        # Wait for the user to select a checklist
        reaction, _ = await bot.wait_for('reaction_add', check=checklist_check, timeout=60.0)

        # Determine the selected checklist
        selected_index = reactions.index(reaction.emoji)
        list_name = checklist_names[selected_index]
        tasks = todo_checklists[user_id][list_name]

        if not tasks:
            # If no tasks in the selected checklist, inform the user
            embed = discord.Embed(
                title=f"No Tasks in **{list_name}** 📋",
                description="This checklist has no tasks yet. Please add tasks using `@ToDoBot add`.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            return

        # Display tasks if present
        task_descriptions = [
            f"{i + 1}. {'✅' if task['completed'] else '❌'} {task['task']}" 
            for i, task in enumerate(tasks)
        ]

        # Embed for task display (show all tasks on one page)
        embed = discord.Embed(
            title=f"Tasks in **{list_name}**",
            description="\n".join(task_descriptions),
            color=discord.Color.blue()
        )
        embed.set_footer(text="✅ Task statuses displayed.")
        await ctx.send(embed=embed)

    except asyncio.TimeoutError:
        timeout_embed = discord.Embed(
            title="Timeout ⚠️",
            description="You took too long to respond. Task view canceled.",
            color=discord.Color.orange()
        )
        await ctx.send(embed=timeout_embed)




# Command: View all lists
@bot.command(name="lists", help="View all your checklists.")
async def view_lists(ctx):
    user_id = str(ctx.author.id)
    if user_id in todo_checklists and todo_checklists[user_id]:
        embed = discord.Embed(
            title="Your Checklists",
            description="Here are all your checklists:",
            color=discord.Color.green(),
        )
        for list_name in todo_checklists[user_id].keys():
            embed.add_field(name=list_name, value="Use `@ToDoBot view` to see tasks.", inline=False)
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            title="No Checklists 🛑",
            description="You don't have any lists yet! Create one using `@ToDoBot create`.",
            color=discord.Color.red(),
        )
        await ctx.send(embed=embed)


# Command: Clear all tasks in a checklist (interactive)
@bot.command(name="clear", help="Clear all tasks in a checklist. Usage: @ToDoBot clear")
async def clear_tasks(ctx):
    user_id = str(ctx.author.id)

    # Check if the user has any checklists
    if user_id not in todo_checklists or not todo_checklists[user_id]:
        embed = discord.Embed(
            title="No Checklists Found 🛑",
            description="You don't have any checklists. Please create one first.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    # List the user's checklists
    checklist_names = list(todo_checklists[user_id].keys())
    reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']  # 1-10 reactions

    embed = discord.Embed(
        title="Select a Checklist to Clear Tasks ✨",
        description="Please select a checklist by reacting with the corresponding emoji.\n\n"
                    + "\n".join([f"{reactions[i]} - {checklist_names[i]}" for i in range(len(checklist_names))]),
        color=discord.Color.blue()
    )
    embed.set_footer(text="You have 60 seconds to respond.")
    checklist_message = await ctx.send(embed=embed)

    # Add reactions for the checklists
    for i in range(len(checklist_names)):
        await checklist_message.add_reaction(reactions[i])

    def checklist_check(reaction, user):
        return user == ctx.author and reaction.message.id == checklist_message.id and reaction.emoji in reactions[:len(checklist_names)]

    try:
        # Wait for the user to select a checklist
        reaction, _ = await bot.wait_for('reaction_add', check=checklist_check, timeout=60.0)

        # Determine the selected checklist
        selected_index = reactions.index(reaction.emoji)
        list_name = checklist_names[selected_index]

        # Confirm with the user that they want to clear all tasks
        embed = discord.Embed(
            title=f"Clear All Tasks in **{list_name}**",
            description="Are you sure you want to clear all tasks in this checklist? React with ✅ to confirm, ❌ to cancel.",
            color=discord.Color.orange()
        )
        # Send the confirmation embed
        message = await ctx.send(embed=embed)

        # Add reactions for confirmation
        await message.add_reaction('✅')
        await message.add_reaction('❌')

        def check(reaction, user):
            return user == ctx.author and reaction.message.id == message.id and reaction.emoji in ['✅', '❌']

        try:
            # Wait for the user to react
            reaction, _ = await bot.wait_for('reaction_add', check=check, timeout=60.0)

            if reaction.emoji == '✅':  # User confirmed the action
                todo_checklists[user_id][list_name] = []  # Clear all tasks in the checklist
                save_checklists()  # Save data to file

                confirmation_embed = discord.Embed(
                    title="Tasks Cleared 🗑️",
                    description=f"All tasks in **{list_name}** have been cleared!",
                    color=discord.Color.green()
                )
                await ctx.send(embed=confirmation_embed)

            elif reaction.emoji == '❌':  # User canceled the action
                cancel_embed = discord.Embed(
                    title="Action Canceled",
                    description="The task clearing has been canceled.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=cancel_embed)

        except asyncio.TimeoutError:
            # Timeout if no reaction was received in 60 seconds
            timeout_embed = discord.Embed(
                title="Timeout ⚠️",
                description="You took too long to respond. The task clearing has been canceled.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=timeout_embed)

    except asyncio.TimeoutError:
        # Timeout if no reaction was received in 60 seconds for selecting a checklist
        timeout_embed = discord.Embed(
            title="Timeout ⚠️",
            description="You took too long to select a checklist. Task clearing canceled.",
            color=discord.Color.orange()
        )
        await ctx.send(embed=timeout_embed)

        
        
@bot.command(name="share", help="Share a checklist with multiple users interactively.")
async def share_checklist(ctx):
    user_id = str(ctx.author.id)

    # Check if the user has any checklists
    if user_id not in todo_checklists or not todo_checklists[user_id]:
        embed = discord.Embed(
            title="No Checklists Found 🛑",
            description="You don't have any checklists. Please create one first using `@ToDoBot create`.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    # List the checklists to choose from
    checklist_names = list(todo_checklists[user_id].keys())
    reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']  # 1-10 reactions

    # Create an embed with the checklist names
    embed = discord.Embed(
        title="Select a Checklist to Share ✨",
        description="Please select a checklist by reacting with the corresponding emoji.\n\n"
                    + "\n".join([f"{reactions[i]} - {checklist_names[i]}" for i in range(len(checklist_names))]),
        color=discord.Color.blue()
    )
    embed.set_footer(text="You have 60 seconds to respond.")
    checklist_message = await ctx.send(embed=embed)

    # Add reactions for the checklists
    for i in range(len(checklist_names)):
        await checklist_message.add_reaction(reactions[i])

    def checklist_check(reaction, user):
        return user == ctx.author and reaction.message.id == checklist_message.id and reaction.emoji in reactions[:len(checklist_names)]

    try:
        # Wait for the user to select a checklist
        reaction, _ = await bot.wait_for('reaction_add', check=checklist_check, timeout=60.0)

        # Determine the selected checklist
        selected_index = reactions.index(reaction.emoji)
        list_name = checklist_names[selected_index]

        # Prompt the user to mention the users they want to share with
        mention_prompt = discord.Embed(
            title=f"Share Checklist **{list_name}**",
            description="Please mention the user(s) you want to share this checklist with. Separate mentions with spaces.\nExample: @user1 @user2",
            color=discord.Color.green()
        )
        mention_message = await ctx.send(embed=mention_prompt)

        def mention_check(message):
            return message.author == ctx.author and message.channel == ctx.channel

        # Wait for the user to provide the mentions
        mention_message = await bot.wait_for('message', check=mention_check, timeout=60.0)

        mentions = mention_message.content.split()
        mentions = [mention for mention in mentions if mention.startswith("<@") and mention.endswith(">")]

        if not mentions:
            await ctx.send("⚠️ No valid mentions found. The checklist won't be shared.")
            return

        # Share the checklist with the mentioned users
        shared_with = []  # Keep track of successfully shared users
        errors = []  # Track users who couldn't receive the checklist

        for mention in mentions:
            user_id_to_share = mention.strip("<@!>")  # Extract user ID from mention format
            recipient_id = str(user_id_to_share)

            # Initialize the recipient's checklists if not present
            if recipient_id not in todo_checklists:
                todo_checklists[recipient_id] = {}

            # Check if the recipient already has a checklist with the same name
            if list_name in todo_checklists[recipient_id]:
                errors.append(mention)
            else:
                todo_checklists[recipient_id][list_name] = todo_checklists[user_id][list_name]
                shared_with.append(mention)

        # Save the updated data
        save_checklists()

        # Send feedback to the user
        if shared_with:
            shared_embed = discord.Embed(
                title="Checklist Shared Successfully ✅",
                description=f"Checklist **{list_name}** has been shared with the following users:\n{', '.join(shared_with)}",
                color=discord.Color.green()
            )
            await ctx.send(embed=shared_embed)

        if errors:
            error_embed = discord.Embed(
                title="⚠️ Checklist Sharing Error",
                description=f"Couldn't share **{list_name}** with the following users due to a checklist name conflict:\n{', '.join(errors)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=error_embed)

    except asyncio.TimeoutError:
        timeout_embed = discord.Embed(
            title="Timeout ⚠️",
            description="You took too long to respond. Checklist sharing canceled.",
            color=discord.Color.orange()
        )
        await ctx.send(embed=timeout_embed)
        
# Run the bot 
bot.run(DISCORD_TOKEN)

