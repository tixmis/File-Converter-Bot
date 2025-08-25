import os
import sys
import logging
import threading
import pyrogram
from pyrogram import Client, filters
from pyrogram.types import Message, ReplyKeyboardRemove

# Import your custom modules (make sure these files exist)
try:
    from buttons import IMGboard  # Make sure this exists
    from helperfunctions import (
        saveMsg, getSavedMsg, removeSavedMsg, saverec, gettorfile,
        colorizeimage, negetivetopostive, readf, sendphoto, senddoc,
        sendvideo, transcript, speak, increaseres, extract, compile,
        scan, runpro, bgremove, follow, other
    )
    # Add other imports as needed
    IMG_TEXT = "JPG, PNG, WEBP, BMP, etc."  # Define this or import from your module
except ImportError as e:
    print(f"Warning: Could not import some modules: {e}")
    # Define fallbacks or exit
    IMGboard = None
    IMG_TEXT = "JPG, PNG, WEBP, BMP, etc."

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def validate_environment_variables():
    """Validate and retrieve environment variables with clear error messages."""
    errors = []
    
    # Get TOKEN
    token = os.environ.get("TOKEN", "").strip()
    if not token:
        errors.append("❌ TOKEN environment variable is missing or empty")
    
    # Get API_ID
    api_id_str = os.environ.get("ID", "").strip()
    if not api_id_str:
        errors.append("❌ ID environment variable is missing or empty")
    else:
        try:
            api_id = int(api_id_str)
            if api_id <= 0:
                errors.append("❌ ID must be a positive integer")
        except ValueError:
            errors.append(f"❌ ID must be an integer, got: '{api_id_str}'")
            api_id = None
    
    # Get API_HASH
    api_hash = os.environ.get("HASH", "").strip()
    if not api_hash:
        errors.append("❌ HASH environment variable is missing or empty")
    
    if errors:
        logger.error("Environment validation failed:")
        for error in errors:
            logger.error(error)
        sys.exit(1)
    
    return token, api_id, api_hash

# Initialize environment variables
try:
    TOKEN, API_ID, API_HASH = validate_environment_variables()
    logger.info("✅ Environment variables validated successfully")
except Exception as e:
    logger.error(f"❌ Failed to validate environment variables: {e}")
    sys.exit(1)

# Initialize Pyrogram client
try:
    app = Client(
        "file_converter_bot",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=TOKEN,
        workdir="."
    )
    logger.info("✅ Pyrogram client initialized")
except Exception as e:
    logger.error(f"❌ Failed to initialize Pyrogram client: {e}")
    sys.exit(1)

# Basic command handlers
@app.on_message(filters.command("start"))
async def start_command(client, message: Message):
    """Handle /start command."""
    await message.reply_text(
        "🤖 **File Converter Bot**\n\n"
        "Welcome! Send me any file and I'll help you convert it.\n\n"
        "**Supported formats:**\n"
        "• Images (JPG, PNG, WEBP, etc.)\n"
        "• Videos (MP4, AVI, MOV, etc.)\n"
        "• Audio (MP3, WAV, OGG, etc.)\n"
        "• Documents (PDF, DOC, etc.)\n"
        "• Stickers (WEBP, TGS)\n\n"
        "Use /help for more information."
    )
    logger.info(f"Start command executed by user {message.from_user.id}")

@app.on_message(filters.command("help"))
async def help_command(client, message: Message):
    """Handle /help command."""
    await message.reply_text(
        "🆘 **Help - File Converter Bot**\n\n"
        "**Available Commands:**\n"
        "• /start - Start the bot\n"
        "• /help - Show this help message\n"
        "• /cancel - Cancel current operation\n"
        "• /rename - Rename files\n\n"
        "**How to use:**\n"
        "1. Send me any file\n"
        "2. Choose the format to convert to\n"
        "3. Wait for the conversion to complete\n\n"
        "**Special Features:**\n"
        "• Colorize images\n"
        "• Upscale images\n"
        "• Remove backgrounds\n"
        "• Text recognition (OCR)\n"
        "• Speech to text\n"
        "• Text to speech"
    )

@app.on_message(filters.command("cancel"))
async def cancel_command(client, message: Message):
    """Handle /cancel command."""
    try:
        removeSavedMsg(message)
        await message.reply_text("❌ Operation cancelled.", reply_markup=ReplyKeyboardRemove())
    except:
        await message.reply_text("❌ No operation to cancel.")

# Sticker handler
@app.on_message(filters.sticker)
async def sticker_handler(client, message: Message):
    """Handle sticker messages."""
    try:
        saveMsg(message, "STICKER")
        
        if not message.sticker.is_animated and not message.sticker.is_video:
            format_type = "WEBP 📷"
        else:
            format_type = "TGS 📷"
            
        await message.reply_text(
            f'Detected Extension: {format_type}\n'
            f'__Now send extension to Convert to...\n\n'
            f'--**Available formats**-- \n\n{IMG_TEXT}\n\n'
            f'**SPECIAL** 🎁\n'
            f'__Colorize, Positive, Upscale & Scan__\n\n'
            f'{message.from_user.mention} __choose or click /cancel to Cancel or use /rename to Rename',
            reply_markup=IMGboard,
            reply_to_message_id=message.id
        )
        logger.info(f"Sticker received from user {message.from_user.id}")
    except Exception as e:
        logger.error(f"Error handling sticker: {e}")
        await message.reply_text("❌ Error processing sticker. Please try again.")

# Text message handler for conversions
@app.on_message(filters.text & ~filters.command(["start", "help", "cancel", "rename"]))
async def text_handler(client, message: Message):
    """Handle text messages for file conversion."""
    try:
        # Handle Telegram links
        if "https://t.me/" in message.text:
            threading.Thread(target=lambda: saverec(message), daemon=True).start()
            return

        # Handle magnet links
        if message.text.startswith("magnet:?"):
            oldm = await message.reply_text('Processing...', reply_to_message_id=message.id)
            threading.Thread(target=lambda: gettorfile(message, oldm), daemon=True).start()
            return

        # Handle conversion commands
        nmessage, msg_type = getSavedMsg(message)
        if nmessage:
            removeSavedMsg(message)
            try:
                await app.delete_messages(message.chat.id, message_ids=nmessage.id + 1)
            except:
                pass

            # Handle special commands
            special_commands = {
                "COLOR": lambda: colorizeimage(nmessage, None),
                "POSITIVE": lambda: negetivetopostive(nmessage, None),
                "READ": lambda: readf(nmessage, None),
                "SENDPHOTO": lambda: sendphoto(nmessage, None),
                "SENDDOC": lambda: senddoc(nmessage, None),
                "SENDVID": lambda: sendvideo(nmessage, None),
                "SpeechToText": lambda: transcript(nmessage, None),
                "TextToSpeech": lambda: speak(nmessage, None),
                "UPSCALE": lambda: increaseres(nmessage, None),
                "EXTRACT": lambda: extract(nmessage, None),
                "COMPILE": lambda: compile(nmessage, None),
                "SCAN": lambda: scan(nmessage, None),
                "RUN": lambda: runpro(nmessage, None),
                "BG REMOVE": lambda: bgremove(nmessage, None)
            }

            if message.text in special_commands:
                oldm = await message.reply_text(
                    'Processing...',
                    reply_markup=ReplyKeyboardRemove(),
                    reply_to_message_id=nmessage.id
                )
                threading.Thread(target=special_commands[message.text], daemon=True).start()
                return

            # Handle file conversion
            inputt = get_file_name(nmessage, msg_type)
            if not inputt:
                await message.reply_text(
                    'Not in any Supported Format, Contact the Developer',
                    reply_to_message_id=nmessage.id,
                    reply_markup=ReplyKeyboardRemove()
                )
                return

            newext = message.text.lower()
            oldext = inputt.split(".")[-1]

            if oldext.upper() == newext.upper():
                await message.reply_text(
                    "Nice try, Don't choose same Extension",
                    reply_to_message_id=nmessage.id,
                    reply_markup=ReplyKeyboardRemove()
                )
            else:
                msg = await message.reply_text(
                    f'Converting from {oldext.upper()} to {newext.upper()}',
                    reply_to_message_id=nmessage.id,
                    reply_markup=ReplyKeyboardRemove()
                )
                threading.Thread(
                    target=lambda: follow(nmessage, inputt, newext, oldext, msg),
                    daemon=True
                ).start()

        else:
            # Handle other text messages
            if str(message.from_user.id) == str(message.chat.id):
                if len(message.text.split("\n")) == 1:
                    threading.Thread(target=lambda: other(message), daemon=True).start()
                else:
                    saveMsg(message, "TEXT")
                    await message.reply_text(
                        'for Text messages, You can use **/make** to Create a File from it.\n'
                        '(first line of text will be truncated and used as filename)',
                        reply_to_message_id=message.id
                    )

    except Exception as e:
        logger.error(f"Error handling text message: {e}")
        await message.reply_text("❌ An error occurred. Please try again.")

def get_file_name(nmessage, msg_type):
    """Get appropriate filename based on message type."""
    try:
        if msg_type == "DOCUMENT":
            return nmessage.document.file_name
        elif msg_type == "AUDIO":
            return nmessage.audio.file_name or "audio.mp3"
        elif msg_type == "VOICE":
            return "voice.ogg"
        elif msg_type == "STICKER":
            if (not nmessage.sticker.is_animated) and (not nmessage.sticker.is_video):
                return nmessage.sticker.set_name + ".webp"
            else:
                return nmessage.sticker.set_name + ".tgs"
        elif msg_type == "VIDEO":
            return nmessage.video.file_name or "video.mp4"
        elif msg_type == "VIDEO_NOTE":
            return "video_note.mp4"
        elif msg_type == "PHOTO":
            temp = app.download_media(nmessage)
            filename = temp.split("/")[-1]
            os.remove(temp)
            return filename
        else:
            return None
    except Exception as e:
        logger.error(f"Error getting filename: {e}")
        return None

# Handle all other file types
@app.on_message(filters.document | filters.audio | filters.video | filters.photo | filters.voice | filters.video_note)
async def file_handler(client, message: Message):
    """Handle file messages."""
    try:
        file_types = {
            message.document: ("DOCUMENT", "📄"),
            message.audio: ("AUDIO", "🎵"),
            message.video: ("VIDEO", "🎬"),
            message.photo: ("PHOTO", "📷"),
            message.voice: ("VOICE", "🎤"),
            message.video_note: ("VIDEO_NOTE", "📹")
        }
        
        file_type = None
        emoji = "📁"
        
        for file_obj, (type_name, type_emoji) in file_types.items():
            if file_obj:
                file_type = type_name
                emoji = type_emoji
                break
        
        if file_type:
            saveMsg(message, file_type)
            await message.reply_text(
                f'{emoji} **File received!**\n\n'
                f'File type: {file_type}\n'
                f'Now send the extension you want to convert to.\n\n'
                f'Available formats:\n{IMG_TEXT}\n\n'
                f'Or use special commands like COLOR, UPSCALE, etc.\n\n'
                f'Use /cancel to cancel or /help for more options.',
                reply_to_message_id=message.id
            )
            logger.info(f"{file_type} file received from user {message.from_user.id}")
        
    except Exception as e:
        logger.error(f"Error handling file: {e}")
        await message.reply_text("❌ Error processing file. Please try again.")

# Error handler
@app.on_message()
async def catch_all(client, message: Message):
    """Catch-all handler for unhandled message types."""
    if not any([message.text, message.document, message.audio, message.video, 
               message.photo, message.voice, message.video_note, message.sticker]):
        await message.reply_text(
            "🤔 I don't know how to handle this type of message.\n"
            "Please send me a file or use /help for available commands."
        )

def main():
    """Main function to start the bot."""
    try:
        logger.info("🚀 Starting File Converter Bot...")
        logger.info("✅ Bot initialized successfully")
        print("Bot Started")
        app.run()
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Bot crashed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
