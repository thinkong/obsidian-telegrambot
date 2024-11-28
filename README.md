# Telegram to Markdown Bot

This bot saves incoming Telegram messages as markdown files in a specified directory. I use it to save messages from my Telegram group chat to a local directory. That local directory is part of my obsidian vault and I can use it to create a markdown file for messages daily. So basically it is used like a journal. If someone uses it, any kind of feedback is welcome.

## Setup Instructions

1. Set up a virtual environment:
   ```
   python -m venv venv
   ```

2. Activate the virtual environment:
   - Windows:
     ```
     .\venv\Scripts\activate
     ```
   - Linux/Mac:
     ```
     source venv/bin/activate
     ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a Telegram Bot:
   - Open Telegram and search for "@BotFather"
   - Send "/newbot" to create a new bot
   - Follow the instructions to set a name and username for your bot
   - BotFather will give you a token - save this for later

5. Run the bot:
   ```
   python bot.py
   ```
   On first run, you'll be asked to:
   - Enter your Telegram bot token
   - Specify the directory where markdown files should be saved

Your bot will then start running and save all received messages as markdown files.

## Development

To deactivate the virtual environment when you're done:
```
deactivate
```
