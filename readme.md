# ToDoBot

ToDoBot is a lightweight Discord bot that helps you manage your tasks and checklists interactively. You can create, view, add tasks, mark tasks as complete, and share checklists with other users.

## Features

- Create checklists interactively
- Add tasks to checklists
- View tasks in a checklist
- Mark tasks as complete
- Clear all tasks in a checklist
- Share checklists with other users

## Setup

### Prerequisites

- Python 3.10 or higher
- Discord Bot (To set up a Discord bot, follow the instructions in this [README](https://github.com/PointCloudLibrary/discord-bot/blob/master/README.md))
- Docker (optional, for containerized deployment)

### Installation

1. Clone the repository:

```bash
git clone https://github.com/calebmwelsh/Discord-ToDoBot.git
cd Discord-ToDoBot
```

### Running Locally

1. Prepare the configuration file:  
   Locate the `config.toml.temp` file in the project directory, open it, and replace the placeholder `DiscordBotToken` value with your bot's token. For example: 
   [General] DiscordBotToken = "your-discord-bot-token" 

2. After editing, rename the file to `config.toml` by removing the `.temp` extension.

3. Install the required dependencies:  
pip install -r requirements.txt

4. Run the bot:  
python main.py


### Running with Docker

1. Build the Docker image:  

```bash
docker build -t Discord-ToDoBot 
```

2. Run the Docker container:  

```bash
docker run -d --name Discord-ToDoBot
```

## Usage

### Commands

- `@ToDoBot create`: Create a new checklist interactively.
- `@ToDoBot add`: Add tasks to a checklist interactively.
- `@ToDoBot view`: View tasks in a checklist interactively.
- `@ToDoBot check`: Mark tasks as complete interactively.
- `@ToDoBot clear`: Clear all tasks in a checklist interactively.
- `@ToDoBot share`: Share a checklist with other users interactively.
- `@ToDoBot lists`: View all your checklists.

### Example

To create a new checklist, mention the bot and use the `create` command:

@ToDoBot create

Follow the prompts to provide the checklist name and add tasks.

## License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## Acknowledgments

- [discord.py](https://discordpy.readthedocs.io/) - Python library for Discord API
- [toml](https://pypi.org/project/toml/) - Python library for TOML parsing
