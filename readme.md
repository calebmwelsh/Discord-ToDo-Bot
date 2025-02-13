# ToDoBot  

ToDoBot is a lightweight Discord bot that helps you manage your tasks and checklists interactively. You can create, view, add tasks, mark tasks as complete, and share checklists with other users.  

---

## Features  

- Create checklists interactively  
- Add tasks to checklists  
- View tasks in a checklist  
- Mark tasks as complete  
- Clear all tasks in a checklist  
- Share checklists with other users  

---

## Setup  

### Prerequisites  

- Python 3.10 or higher  
- Discord Bot (To set up a Discord bot, follow the instructions in this [README](https://github.com/PointCloudLibrary/discord-bot/blob/master/README.md))  
- Docker (optional, for containerized deployment)  

---

### Installation  

1. Clone the repository:  
  ```bash  
  git clone https://github.com/calebmwelsh/Discord-ToDoBot.git  
  cd Discord-ToDoBot  
  ```  

---

### Running Locally  

1. Prepare the configuration file:  
   Locate the `config.toml.temp` file in the project directory, open it, and replace the placeholder `DiscordBotToken` value with your bot's token. For example:  
   ```toml  
   [General]  
   DiscordBotToken = "your-discord-bot-token"  
   ```  

2. After editing, rename the file to `config.toml` by removing the `.temp` extension.  

3. Install the required dependencies:  
  ```bash  
  pip install -r requirements.txt  
  ```  

4. Run the bot:  
  ```bash  
  python main.py  
  ```  

---

### Running with Docker Compose  

Save the following as `docker-compose.yml` (recommended for easier management):  

```yaml  
version: '3.8'

services:
  discord-bot:
    image: kdidtech/discord-todo-bot:latest
    environment:
      - DISCORD_BOT_TOKEN=your-discord-bot-token-here
    volumes:
      - ./data/:/app/data/
    restart: always 
```

1. Replace `your-discord-bot-token-here` with your actual Discord bot token.  
2. (Optional) Replace `your-checklist-directory` with your actual directory location where your chechlists.json file is.
3. Start the bot using Docker Compose:

   ```bash
   docker-compose up -d
   ```

4. Verify the bot is running:

   ```bash
   docker-compose ps
   ```
---

This will automatically pull the latest image of the bot, set up the environment variables, and ensure the bot restarts automatically if it stops or the system reboots.  

---

## Usage  

### Commands  

- `@ToDoBot create`: Create a new checklist interactively.  
- `@ToDoBot add`: Add tasks to a checklist interactively.  
- `@ToDoBot view`: View tasks in a checklist interactively.  
- `@ToDoBot check`: Mark tasks as complete interactively.  
- `@ToDoBot clear`: Clear all tasks in a checklist interactively.  
- `@ToDoBot share`: Share a checklist with other users interactively.  
- `@ToDoBot lists`: View all your checklists.  

---

### Example  

To create a new checklist, mention the bot and use the `create` command:  
  ```  
  @ToDoBot create  
  ```  
Follow the prompts to provide the checklist name and add tasks.  

---

## License  

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.  

---

## Contributing  

Contributions are welcome! Please open an issue or submit a pull request.  

---

## Acknowledgments  

- [discord.py](https://discordpy.readthedocs.io/) - Python library for Discord API  
- [toml](https://pypi.org/project/toml/) - Python library for TOML parsing  

---

With `kdidtech/discord-todo-bot`, managing your to-do lists on Discord has never been easier. Whether you're using Docker Compose or the command line, this bot provides a reliable and efficient way to keep your tasks organized and your productivity on track. 🚀  