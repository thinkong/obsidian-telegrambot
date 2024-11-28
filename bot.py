import os
import json
import logging
from datetime import datetime
from pathlib import Path
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

CONFIG_FILE = "config.json"

def load_config():
    """Load configuration from config.json"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return None

def save_config(config):
    """Save configuration to config.json"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

def first_time_setup():
    """Run first-time setup to gather necessary information"""
    print("Welcome to Telegram to Markdown Bot!")
    print("\nFirst-time setup:")
    
    # Get bot token
    token = input("\nPlease enter your Telegram bot token: ").strip()
    
    # Get save directory
    while True:
        save_dir = input("\nEnter the full path where markdown files should be saved: ").strip()
        save_dir = os.path.expanduser(save_dir)
        
        try:
            # Create directory if it doesn't exist
            Path(save_dir).mkdir(parents=True, exist_ok=True)
            # Test if we can write to it
            test_file = Path(save_dir) / "test.txt"
            test_file.touch()
            test_file.unlink()
            break
        except Exception as e:
            print(f"Error: Could not write to directory: {e}")
            continue
    
    config = {
        "token": token,
        "save_directory": save_dir
    }
    
    save_config(config)
    return config

def get_unique_filename(directory: Path, filename: str) -> str:
    """
    Generate a unique filename by adding a counter if the file already exists.
    Example: file.txt -> file (1).txt -> file (2).txt
    """
    if not (directory / filename).exists():
        return filename
        
    name, ext = os.path.splitext(filename)
    counter = 1
    
    while (directory / "{}({}){}".format(name, counter, ext)).exists():
        counter += 1
        
    return "{}({}){}".format(name, counter, ext)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages"""
    message = update.message
    logger.info("Received message: %s", message.message_id)
    
    # Create filename using only timestamp
    timestamp = datetime.now().strftime("%Y%m%d")
    filename = "{}.md".format(timestamp)
    file_path = Path(context.bot_data["save_directory"]) / filename
    
    # Create YAML header for new files
    yaml_header = """---
date: {}
type: telegram-messages
---

""".format(datetime.now().strftime("%Y-%m-%d"))
    
    # Create attachments directory for this date if needed
    attachments_dir = Path(context.bot_data["save_directory"]) / "attachments" / timestamp
    attachments_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Attachments directory: %s", str(attachments_dir))
    
    # Handle any files or media
    file_references = []
    
    # Get message text (could be caption if it's a media message)
    message_text = message.text or message.caption or ""
    
    # Handle photos
    if message.photo:
        logger.info("Processing photo...")
        try:
            # Get the largest photo (last item in the list)
            photo = message.photo[-1]
            photo_file = await photo.get_file()
            photo_ext = "jpg"  # Telegram usually sends photos as JPEG
            photo_filename = "photo_{}.{}".format(datetime.now().strftime('%H%M%S'), photo_ext)
            # Get unique filename
            photo_filename = get_unique_filename(attachments_dir, photo_filename)
            photo_path = attachments_dir / photo_filename
            logger.info("Downloading photo to: %s", str(photo_path))
            
            # Download the file
            await photo_file.download_to_drive(str(photo_path))
            logger.info("Photo downloaded successfully")
            
            # Add markdown image reference using forward slashes
            rel_path = "./attachments/{}/{}".format(timestamp, photo_filename)
            file_references.append("![Photo]({})".format(rel_path))
        except Exception as e:
            logger.error("Error downloading photo: %s", str(e), exc_info=True)
            await message.reply_text("⚠️ Failed to save photo: {}".format(str(e)))
    
    # Handle documents/files
    if message.document:
        logger.info("Processing document...")
        try:
            doc = message.document
            doc_file = await doc.get_file()
            doc_filename = doc.file_name if doc.file_name else "file_{}".format(datetime.now().strftime('%H%M%S'))
            # Get unique filename
            doc_filename = get_unique_filename(attachments_dir, doc_filename)
            doc_path = attachments_dir / doc_filename
            logger.info("Downloading document to: %s", str(doc_path))
            
            # Download the file
            await doc_file.download_to_drive(str(doc_path))
            logger.info("Document downloaded successfully")
            
            # Add markdown file reference using forward slashes
            rel_path = "./attachments/{}/{}".format(timestamp, doc_filename)
            file_references.append("[{}]({})".format(doc_filename, rel_path))
        except Exception as e:
            logger.error("Error downloading document: %s", str(e), exc_info=True)
            await message.reply_text("⚠️ Failed to save document: {}".format(str(e)))
    
    # Create message content with timestamp and sender
    message_content = """[{timestamp}] {sender}: {text}

{attachments}
""".format(
        timestamp=datetime.now().strftime("%H:%M:%S"),
        sender=message.from_user.username or message.from_user.first_name,
        text=message_text,
        attachments="\n".join(file_references)
    )
    
    # If file exists, append to it, otherwise create new file with YAML header
    if file_path.exists():
        with open(file_path, "a", encoding="utf-8") as f:
            f.write("\n" + message_content)
    else:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(yaml_header + message_content)
    
    # Acknowledge receipt with file info
    if file_references:
        await message.reply_text("Message and {} attachment(s) saved! ✅".format(len(file_references)))
    else:
        await message.reply_text("Message saved! ✅")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error("Error occurred: %s", str(context.error))

def main():
    # Load or create configuration
    config = load_config()
    if not config:
        config = first_time_setup()
    
    # Create application
    application = Application.builder().token(config["token"]).build()
    
    # Store save directory in bot_data
    application.bot_data["save_directory"] = config["save_directory"]
    
    # Add handlers - now handling all types of messages
    application.add_handler(MessageHandler(
        filters.ALL,  # This will catch all types of messages
        handle_message
    ))
    application.add_error_handler(error_handler)
    
    # Start the bot
    logger.info("Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
