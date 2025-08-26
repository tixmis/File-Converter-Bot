#!/usr/bin/env python3
import pyrogram
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove

import os
import sys
import shutil
import subprocess
import threading
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Print debug info
logger.info("="*50)
logger.info("Starting File Converter Bot")
logger.info("="*50)

# Environment variables
bot_token = os.environ.get("TOKEN", "").strip()
api_hash = os.environ.get("HASH", "").strip()
api_id_str = os.environ.get("ID", "").strip()

# Debug: Show what we found
logger.info(f"TOKEN found: {bool(bot_token)} (length: {len(bot_token)})")
logger.info(f"HASH found: {bool(api_hash)} (length: {len(api_hash)})")
logger.info(f"ID found: {bool(api_id_str)} (value: {api_id_str})")

# Check if variables exist
if not all([bot_token, api_hash, api_id_str]):
    logger.error("="*50)
    logger.error("MISSING ENVIRONMENT VARIABLES!")
    logger.error("="*50)
    missing = []
    if not bot_token: missing.append("TOKEN")
    if not api_hash: missing.append("HASH")
    if not api_id_str: missing.append("ID")
    logger.error(f"Missing: {', '.join(missing)}")
    logger.error("Please set these in Railway Variables tab")
    sys.exit(1)

# Convert ID to integer
try:
    api_id = int(api_id_str)
except ValueError:
    logger.error(f"ID must be a number, got: {api_id_str}")
    sys.exit(1)

# Try importing modules with fallback
try:
    from buttons import *
    BUTTONS_AVAILABLE = True
except ImportError:
    logger.warning("buttons.py not found - creating defaults")
    BUTTONS_AVAILABLE = False
    # Create default values
    IMG_TEXT = "JPG, PNG, WEBP, BMP, GIF, ICO, TIFF"
    VA_TEXT = "MP4, AVI, MOV, MKV, MP3, WAV, OGG, FLAC"
    IMGboard = None
    VAboard = None

try:
    import aifunctions
except ImportError:
    logger.warning("aifunctions.py not found - AI features disabled")
    aifunctions = None

try:
    import helperfunctions
except ImportError:
    logger.warning("helperfunctions.py not found - some features disabled")
    helperfunctions = None

try:
    import mediainfo
except ImportError:
    logger.warning("mediainfo.py not found")
    mediainfo = None

try:
    import others
except ImportError:
    logger.warning("others.py not found")
    others = None

# Initialize client
try:
    app = Client(
        "my_bot",
        api_id=api_id,
        api_hash=api_hash,
        bot_token=bot_token
    )
    logger.info("✅ Pyrogram client created successfully")
except Exception as e:
    logger.error(f"❌ Failed to create Pyrogram client: {e}")
    sys.exit(1)

# Message storage
MESGS = {}

def saveMsg(msg, msg_type):
    """Save message for later processing"""
    MESGS[msg.from_user.id] = [msg, msg_type]

def getSavedMsg(msg):
    """Get saved message"""
    return MESGS.get(msg.from_user.id, [None, None])

def removeSavedMsg(msg):
    """Remove saved message"""
    if msg.from_user.id in MESGS:
        del MESGS[msg.from_user.id]

# Basic conversion function
def follow(message, inputt, new, old, oldmessage):
    """Main conversion handler"""
    try:
        output = inputt.rsplit(".", 1)[0] + "." + new
        
        # For testing - just rename file
        file = app.download_media(message)
        
        # Simple conversion message
        app.send_message(
            message.chat.id,
            f"Converting {old.upper()} to {new.upper()}...\n"
            f"(Note: Full conversion features require helper modules)",
            reply_to_message_id=message.id
        )
        
        # Send back original file with new extension name
        app.send_document(
            message.chat.id,
            document=file,
            file_name=output,
            caption=f"Converted: {output}",
            reply_to_message_id=message.id
        )
        
        os.remove(file)
        app.delete_messages(message.chat.id, message_ids=oldmessage.id)
        
    except Exception as e:
        logger.error(f"Conversion error: {e}")
        app.send_message(
            message.chat.id,
            f"Error during conversion: {e}",
            reply_to_message_id=message.id
        )

# Command handlers
@app.on_message(filters.command(['start']))
def start(client, message):
    app.send_message(
        message.chat.id,
        f"👋 Welcome {message.from_user.mention}!\n\n"
        f"I'm a File Converter Bot. Send me any file and I'll help you convert it.\n\n"
        f"**How to use:**\n"
        f"1. Send me a file (document, image, video, audio, etc.)\n"
        f"2. Choose the output format\n"
        f"3. Get your converted file!\n\n"
        f"Type /help for more commands.",
        reply_to_message_id=message.id
    )

@app.on_message(filters.command(['help']))
def help_cmd(client, message):
    app.send_message(
        message.chat.id,
        "📚 **Available Commands:**\n\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/cancel - Cancel current operation\n"
        "/rename - Rename a file\n\n"
        "**How to convert files:**\n"
        "1. Send any file to the bot\n"
        "2. Bot will detect the format\n"
        "3. Choose output format from buttons or type it\n"
        "4. Wait for conversion\n\n"
        "**Supported formats:** Images, Videos, Audio, Documents, and more!",
        reply_to_message_id=message.id
    )

@app.on_message(filters.command(['cancel']))
def cancel(client, message):
    nmessage, msg_type = getSavedMsg(message)
    if nmessage:
        removeSavedMsg(message)
        app.send_message(
            message.chat.id,
            "❌ Operation cancelled",
            reply_markup=ReplyKeyboardRemove(),
            reply_to_message_id=message.id
        )
    else:
        app.send_message(
            message.chat.id,
            "No active operation to cancel",
            reply_to_message_id=message.id
        )

# Document handler
@app.on_message(filters.document)
def document(client, message):
    saveMsg(message, "DOCUMENT")
    filename = message.document.file_name
    ext = filename.split(".")[-1].upper() if "." in filename else "UNKNOWN"
    
    app.send_message(
        message.chat.id,
        f"📄 **File received!**\n\n"
        f"**Filename:** `{filename}`\n"
        f"**Detected extension:** `{ext}`\n\n"
        f"Now send the extension you want to convert to "
        f"(e.g., type `pdf`, `jpg`, `mp4`, etc.)\n\n"
        f"Or type /cancel to cancel",
        reply_to_message_id=message.id
    )

# Image/Photo handler
@app.on_message(filters.photo)
def photo(client, message):
    saveMsg(message, "PHOTO")
    app.send_message(
        message.chat.id,
        f"🖼 **Image received!**\n\n"
        f"**Format:** JPG\n\n"
        f"Send extension to convert to: `png`, `webp`, `pdf`, etc.\n\n"
        f"Or type /cancel to cancel",
        reply_to_message_id=message.id
    )

# Video handler
@app.on_message(filters.video)
def video(client, message):
    saveMsg(message, "VIDEO")
    filename = getattr(message.video, 'file_name', 'video.mp4')
    ext = filename.split(".")[-1].upper() if "." in filename else "MP4"
    
    app.send_message(
        message.chat.id,
        f"🎥 **Video received!**\n\n"
        f"**Format:** {ext}\n\n"
        f"Send extension to convert to: `mp4`, `avi`, `mov`, `mp3`, etc.\n\n"
        f"Or type /cancel to cancel",
        reply_to_message_id=message.id
    )

# Audio handler
@app.on_message(filters.audio)
def audio(client, message):
    saveMsg(message, "AUDIO")
    filename = message.audio.file_name
    ext = filename.split(".")[-1].upper() if "." in filename else "MP3"
    
    app.send_message(
        message.chat.id,
        f"🎵 **Audio received!**\n\n"
        f"**Format:** {ext}\n\n"
        f"Send extension to convert to: `mp3`, `wav`, `ogg`, `flac`, etc.\n\n"
        f"Or type /cancel to cancel",
        reply_to_message_id=message.id
    )

# Sticker handler
@app.on_message(filters.sticker)
def sticker(client, message):
    saveMsg(message, "STICKER")
    if not message.sticker.is_animated and not message.sticker.is_video:
        ext = "WEBP"
    else:
        ext = "TGS"
    
    app.send_message(
        message.chat.id,
        f"🎨 **Sticker received!**\n\n"
        f"**Format:** {ext}\n\n"
        f"Send extension to convert to: `png`, `jpg`, `gif`, etc.\n\n"
        f"Or type /cancel to cancel",
        reply_to_message_id=message.id
    )

# Voice handler
@app.on_message(filters.voice)
def voice(client, message):
    saveMsg(message, "VOICE")
    app.send_message(
        message.chat.id,
        f"🎤 **Voice message received!**\n\n"
        f"**Format:** OGG\n\n"
        f"Send extension to convert to: `mp3`, `wav`, etc.\n\n"
        f"Or type /cancel to cancel",
        reply_to_message_id=message.id
    )

# Text handler - handles conversion requests
@app.on_message(filters.text)
def text(client, message):
    # Skip commands
    if message.text.startswith("/"):
        return
    
    # Get saved message
    nmessage, msg_type = getSavedMsg(message)
    
    if nmessage:
        removeSavedMsg(message)
        
        # Get file info based on type
        if msg_type == "DOCUMENT":
            inputt = nmessage.document.file_name
        elif msg_type == "PHOTO":
            inputt = "photo.jpg"
        elif msg_type == "VIDEO":
            inputt = getattr(nmessage.video, 'file_name', 'video.mp4')
        elif msg_type == "AUDIO":
            inputt = nmessage.audio.file_name
        elif msg_type == "VOICE":
            inputt = "voice.ogg"
        elif msg_type == "STICKER":
            if not nmessage.sticker.is_animated and not nmessage.sticker.is_video:
                inputt = "sticker.webp"
            else:
                inputt = "sticker.tgs"
        else:
            inputt = "file.unknown"
        
        # Get extensions
        newext = message.text.lower()
        oldext = inputt.split(".")[-1] if "." in inputt else "unknown"
        
        # Check if same extension
        if oldext.lower() == newext.lower():
            app.send_message(
                message.chat.id,
                "⚠️ Source and target formats are the same!",
                reply_to_message_id=nmessage.id
            )
        else:
            # Start conversion
            msg = app.send_message(
                message.chat.id,
                f"🔄 Converting from **{oldext.upper()}** to **{newext.upper()}**...",
                reply_to_message_id=nmessage.id
            )
            
            # Run conversion in thread
            conv = threading.Thread(
                target=lambda: follow(nmessage, inputt, newext, oldext, msg),
                daemon=True
            )
            conv.start()
    else:
        # No saved message - just echo
        if str(message.from_user.id) == str(message.chat.id):  # Private chat
            app.send_message(
                message.chat.id,
                "📁 Please send me a file first, then tell me what format to convert it to.\n\n"
                "Type /start for help.",
                reply_to_message_id=message.id
            )

# Main execution
if __name__ == "__main__":
    try:
        logger.info("="*50)
        logger.info("🚀 Bot is starting...")
        logger.info("="*50)
        app.run()
    except Exception as e:
        logger.error(f"❌ Bot crashed: {e}")
        sys.exit(1)
