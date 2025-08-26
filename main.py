#!/usr/bin/env python3
"""
Telegram File Converter Bot - Main Application
"""

import os
import sys
import logging
import threading
import pyrogram
from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardRemove

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ==================== ENVIRONMENT CONFIGURATION ====================
def load_config():
    """Load and validate environment variables"""
    config = {}
    
    # Required environment variables
    required_vars = {
        'TOKEN': 'Telegram Bot API Token',
        'ID': 'Telegram API ID', 
        'HASH': 'Telegram API Hash'
    }
    
    missing_vars = []
    
    logger.info("=" * 50)
    logger.info("Loading environment variables...")
    logger.info("=" * 50)
    
    for var_name, description in required_vars.items():
        value = os.environ.get(var_name, '').strip()
        
        if not value:
            missing_vars.append(f"{var_name} ({description})")
            logger.error(f"❌ {var_name} is missing or empty")
        else:
            # Mask sensitive values in logs
            if var_name in ['TOKEN', 'HASH']:
                masked = value[:5] + "..." + value[-5:] if len(value) > 10 else "***"
                logger.info(f"✅ {var_name} loaded: {masked}")
            else:
                logger.info(f"✅ {var_name} loaded: {value}")
            config[var_name] = value
    
    if missing_vars:
        logger.error("=" * 50)
        logger.error("CRITICAL: Missing required environment variables:")
        for var in missing_vars:
            logger.error(f"  - {var}")
        logger.error("=" * 50)
        logger.error("Set these in Railway: Dashboard → Variables → Add variables")
        sys.exit(1)
    
    # Convert ID to integer
    try:
        config['ID'] = int(config['ID'])
        logger.info(f"✅ API ID converted to integer: {config['ID']}")
    except ValueError:
        logger.error(f"❌ API ID must be a number, got: {config['ID']}")
        sys.exit(1)
    
    return config

# Load configuration
try:
    CONFIG = load_config()
except Exception as e:
    logger.error(f"Failed to load configuration: {e}")
    sys.exit(1)

# ==================== INITIALIZE PYROGRAM CLIENT ====================
app = Client(
    "file_converter_bot",
    api_id=CONFIG['ID'],
    api_hash=CONFIG['HASH'],
    bot_token=CONFIG['TOKEN']
)

# ==================== IMPORT HELPER MODULES ====================
try:
    from buttons import (
        IMGboard, AUDIOboard, VIDEOboard, 
        LBWboard, TXTboard, FFboard, Helpboard
    )
    logger.info("✅ Buttons module imported")
except ImportError as e:
    logger.warning(f"⚠️ Buttons module not found: {e}")
    IMGboard = AUDIOboard = VIDEOboard = LBWboard = TXTboard = FFboard = Helpboard = None

try:
    from helperfunctions import (
        saveMsg, getSavedMsg, removeSavedMsg,
        colorizeimage, negetivetopostive, readf, sendphoto,
        senddoc, sendvideo, transcript, speak, increaseres,
        extract, compile, scan, runpro, bgremove, follow,
        saverec, gettorfile, other
    )
    logger.info("✅ Helper functions imported")
except ImportError as e:
    logger.warning(f"⚠️ Some helper functions not found: {e}")
    # Create placeholder functions
    def saveMsg(message, msg_type): pass
    def getSavedMsg(message): return None, None
    def removeSavedMsg(message): pass
    def colorizeimage(message, oldm): pass
    def negetivetopostive(message, oldm): pass
    def readf(message, oldm): pass
    def sendphoto(message, oldm): pass
    def senddoc(message, oldm): pass
    def sendvideo(message, oldm): pass
    def transcript(message, oldm): pass
    def speak(message, oldm): pass
    def increaseres(message, oldm): pass
    def extract(message, oldm): pass
    def compile(message, oldm): pass
    def scan(message, oldm): pass
    def runpro(message, oldm): pass
    def bgremove(message, oldm): pass
    def follow(message, inputt, newext, oldext, msg): pass
    def saverec(message): pass
    def gettorfile(message, oldm): pass
    def other(message): pass

# ==================== CONSTANTS ====================
IMG_TEXT = """
JPG, PNG, WEBP, TIFF, TGA, BMP, ICO, SVG, 
GIF (for static images)
"""

AUDIO_TEXT = """
MP3, AAC, FLAC, WAV, OGG, OPUS, M4A
"""

VIDEO_TEXT = """
MP4, MKV, AVI, MOV, WMV, FLV, WEBM
"""

# ==================== COMMAND HANDLERS ====================
@app.on_message(filters.command("start"))
async def start_command(client, message):
    """Handle /start command"""
    try:
        welcome_text = (
            f"👋 Welcome {message.from_user.first_name}!\n\n"
            "I'm a File Converter Bot. Send me any file and I'll help you convert it.\n\n"
            "Use /help for more information."
        )
        await message.reply_text(welcome_text, reply_markup=Helpboard if Helpboard else None)
        logger.info(f"Start command from user {message.from_user.id}")
    except Exception as e:
        logger.error(f"Error in start command: {e}")

@app.on_message(filters.command("help"))
async def help_command(client, message):
    """Handle /help command"""
    help_text = """
📚 **Help Menu**

**Commands:**
• /start - Start the bot
• /help - Show this help
• /cancel - Cancel current operation
• /rename - Rename file
• /make - Create file from text

**How to use:**
1. Send me any file (document, photo, video, audio, sticker)
2. Choose the output format
3. Wait for conversion
4. Download your converted file

**Supported Formats:**
• Images: JPG, PNG, WEBP, GIF, etc.
• Videos: MP4, MKV, AVI, etc.
• Audio: MP3, WAV, FLAC, etc.
• Documents: PDF, DOCX, TXT, etc.
    """
    await message.reply_text(help_text)
    logger.info(f"Help command from user {message.from_user.id}")

@app.on_message(filters.command("cancel"))
async def cancel_command(client, message):
    """Handle /cancel command"""
    removeSavedMsg(message)
    await message.reply_text("Operation cancelled.", reply_markup=ReplyKeyboardRemove())
    logger.info(f"Cancel command from user {message.from_user.id}")

# ==================== FILE HANDLERS ====================
@app.on_message(filters.document)
async def document_handler(client, message):
    """Handle document uploads"""
    saveMsg(message, "DOCUMENT")
    file_name = message.document.file_name
    file_ext = file_name.split(".")[-1].upper() if "." in file_name else "Unknown"
    
    await message.reply_text(
        f"📄 Detected Extension: **{file_ext}**\n"
        f"Now send the extension to convert to...\n\n"
        f"Available formats depend on file type.\n"
        f"Use /cancel to cancel operation.",
        reply_to_message_id=message.id
    )
    logger.info(f"Document received from user {message.from_user.id}: {file_name}")

@app.on_message(filters.photo)
async def photo_handler(client, message):
    """Handle photo uploads"""
    saveMsg(message, "PHOTO")
    await message.reply_text(
        f"📷 Detected: **PHOTO**\n"
        f"Now send extension to convert to...\n\n"
        f"--**Available formats**--\n\n{IMG_TEXT}\n\n"
        f"**SPECIAL** 🎁\n__Colorize, Positive, Upscale & Scan__\n\n"
        f"{message.from_user.mention} choose or click /cancel to Cancel",
        reply_markup=IMGboard if IMGboard else None,
        reply_to_message_id=message.id
    )
    logger.info(f"Photo received from user {message.from_user.id}")

@app.on_message(filters.audio | filters.voice)
async def audio_handler(client, message):
    """Handle audio/voice uploads"""
    msg_type = "AUDIO" if message.audio else "VOICE"
    saveMsg(message, msg_type)
    
    await message.reply_text(
        f"🎵 Detected: **{msg_type}**\n"
        f"Now send extension to convert to...\n\n"
        f"--**Available formats**--\n\n{AUDIO_TEXT}\n\n"
        f"{message.from_user.mention} choose or click /cancel to Cancel",
        reply_markup=AUDIOboard if AUDIOboard else None,
        reply_to_message_id=message.id
    )
    logger.info(f"{msg_type} received from user {message.from_user.id}")

@app.on_message(filters.video | filters.video_note)
async def video_handler(client, message):
    """Handle video/video note uploads"""
    msg_type = "VIDEO" if message.video else "VIDEO_NOTE"
    saveMsg(message, msg_type)
    
    await message.reply_text(
        f"🎥 Detected: **{msg_type}**\n"
        f"Now send extension to convert to...\n\n"
        f"--**Available formats**--\n\n{VIDEO_TEXT}\n\n"
        f"{message.from_user.mention} choose or click /cancel to Cancel",
        reply_markup=VIDEOboard if VIDEOboard else None,
        reply_to_message_id=message.id
    )
    logger.info(f"{msg_type} received from user {message.from_user.id}")

@app.on_message(filters.sticker)
async def sticker_handler(client, message):
    """Handle sticker uploads"""
    saveMsg(message, "STICKER")
    
    if not message.sticker.is_animated and not message.sticker.is_video:
        ext = "WEBP"
    else:
        ext = "TGS"
    
    await message.reply_text(
        f"🎨 Detected Extension: **{ext}**\n"
        f"Now send extension to convert to...\n\n"
        f"--**Available formats**--\n\n{IMG_TEXT}\n\n"
        f"**SPECIAL** 🎁\n__Colorize, Positive, Upscale & Scan__\n\n"
        f"{message.from_user.mention} choose or click /cancel to Cancel",
        reply_markup=IMGboard if IMGboard else None,
        reply_to_message_id=message.id
    )
    logger.info(f"Sticker received from user {message.from_user.id}")

# ==================== TEXT/CONVERSION HANDLER ====================
@app.on_message(filters.text & ~filters.command(["start", "help", "cancel", "rename", "make"]))
async def text_handler(client, message):
    """Handle text messages and conversion commands"""
    
    # Handle special URLs
    if "https://t.me/" in message.text:
        mf = threading.Thread(target=lambda: saverec(message), daemon=True)
        mf.start()
        return
    
    # Handle magnet links
    if message.text.startswith("magnet:?"):
        oldm = await message.reply_text('Processing...', reply_to_message_id=message.id)
        tf = threading.Thread(target=lambda: gettorfile(message, oldm), daemon=True)
        tf.start()
        return
    
    # Check for saved message (conversion process)
    nmessage, msg_type = getSavedMsg(message)
    
    if nmessage:
        removeSavedMsg(message)
        
        # Handle special operations
        special_ops = {
            "COLOR": (colorizeimage, "Processing"),
            "POSITIVE": (negetivetopostive, "Processing"),
            "READ": (readf, "Reading File"),
            "SENDPHOTO": (sendphoto, "Sending in Photo Format"),
            "SENDDOC": (senddoc, "Sending in Document Format"),
            "SENDVID": (sendvideo, "Sending in Stream Format"),
            "SpeechToText": (transcript, "Transcripting, takes long time for Long Files"),
            "TextToSpeech": (speak, "Generating Speech"),
            "UPSCALE": (increaseres, "Upscaling Your Image"),
            "EXTRACT": (extract, "Extracting File"),
            "COMPILE": (compile, "Compiling"),
            "SCAN": (scan, "Scanning"),
            "RUN": (runpro, "Running"),
            "BG REMOVE": (bgremove, "Background Removing")
        }
        
        if message.text in special_ops:
            func, status_msg = special_ops[message.text]
            oldm = await message.reply_text(
                status_msg, 
                reply_markup=ReplyKeyboardRemove(), 
                reply_to_message_id=nmessage.id
            )
            thread = threading.Thread(target=lambda: func(nmessage, oldm), daemon=True)
            thread.start()
            return
        
        # Handle file format conversion
        try:
            # Determine input file extension
            if msg_type == "DOCUMENT":
                inputt = nmessage.document.file_name
            elif msg_type == "AUDIO":
                inputt = nmessage.audio.file_name if nmessage.audio else "audio.ogg"
            elif msg_type == "VOICE":
                inputt = "voice.ogg"
            elif msg_type == "STICKER":
                if (not nmessage.sticker.is_animated) and (not nmessage.sticker.is_video):
                    inputt = (nmessage.sticker.set_name or "sticker") + ".webp"
                else:
                    inputt = (nmessage.sticker.set_name or "sticker") + ".tgs"
            elif msg_type == "VIDEO":
                inputt = nmessage.video.file_name if nmessage.video else "video.mp4"
            elif msg_type == "VIDEO_NOTE":
                inputt = "video_note.mp4"
            elif msg_type == "PHOTO":
                temp = await app.download_media(nmessage)
                inputt = temp.split("/")[-1] if temp else "photo.jpg"
                if temp and os.path.exists(temp):
                    os.remove(temp)
            else:
                await message.reply_text(
                    'Not in any Supported Format',
                    reply_to_message_id=nmessage.id,
                    reply_markup=ReplyKeyboardRemove()
                )
                return
            
            newext = message.text.lower()
            oldext = inputt.split(".")[-1] if "." in inputt else ""
            
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
                conv = threading.Thread(
                    target=lambda: follow(nmessage, inputt, newext, oldext, msg),
                    daemon=True
                )
                conv.start()
                
        except Exception as e:
            logger.error(f"Error in conversion: {e}")
            await message.reply_text(
                "An error occurred during conversion.",
                reply_markup=ReplyKeyboardRemove()
            )
    else:
        # Handle regular text messages
        if str(message.from_user.id) == str(message.chat.id):
            if len(message.text.split("\n")) == 1:
                ots = threading.Thread(target=lambda: other(message), daemon=True)
                ots.start()
            else:
                saveMsg(message, "TEXT")
                await message.reply_text(
                    'For Text messages, You can use **/make** to Create a File from it.\n'
                    '(first line of text will be truncated and used as filename)',
                    reply_to_message_id=message.id
                )

# ==================== MAIN EXECUTION ====================
def main():
    """Main function to run the bot"""
    logger.info("=" * 50)
    logger.info("🤖 Starting Telegram File Converter Bot")
    logger.info("=" * 50)
    
    try:
        logger.info("Bot Started Successfully!")
        app.run()
    except Exception as e:
        logger.error(f"❌ Failed to start bot: {e}")
        logger.error("Check your TOKEN, API_ID and API_HASH")
        sys.exit(1)

if __name__ == "__main__":
    main()
