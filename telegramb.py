from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
import logging
import asyncio
from telethon.sync import TelegramClient
from telethon.tl.types import (
    InputMessagesFilterDocument,
    InputMessagesFilterPhotos,
    InputMessagesFilterVideo
)

# Set up logging with more details
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG  # Changed to DEBUG for more detailed logs
)
logger = logging.getLogger(__name__)

# Your credentials
BOT_TOKEN = "7629993174:AAEBM4ayUGGTIHk7ZA0Yj5_q70To0mRiYag"
API_ID = 22712496
API_HASH = '9afd3f1e0c388947c25e0200e1324340'
GROUP_USERNAME = 'genzthing'

async def search_files(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Search for files and videos with pagination."""
    keyword = update.message.text.lower()
    
    try:
        # Send initial processing message
        status_msg = await update.message.reply_text(
            "🔍 Starting search... Please wait."
        )

        # Create and start the client
        client = TelegramClient('user_session', API_ID, API_HASH)
        await client.start()

        try:
            if not await client.is_user_authorized():
                logger.info("Client not authorized. Please check console for authentication.")
                await status_msg.edit_text(
                    "Bot needs to be authenticated first. Please check console for instructions."
                )
                return

            found_media = []
            processed_count = 0
            batch_size = 1000  # Process messages in larger batches
            
            try:
                # Update status for document search
                await status_msg.edit_text("🔍 Searching for documents...")
                
                # Search documents with pagination
                async for msg in client.iter_messages(
                    GROUP_USERNAME,
                    limit=10000,  # Increased limit
                    filter=InputMessagesFilterDocument
                ):
                    processed_count += 1
                    
                    # Show progress every 500 messages
                    if processed_count % 500 == 0:
                        await status_msg.edit_text(f"🔍 Processed {processed_count} messages...")
                    
                    if msg.document:
                        try:
                            file_name = getattr(msg.document.attributes[0], 'file_name', 'Unnamed file')
                            if keyword in file_name.lower():
                                link = f"https://t.me/{GROUP_USERNAME}/{msg.id}"
                                found_media.append(f"📄 {file_name}\n🔗 {link}")
                                logger.info(f"Found document: {file_name}")
                        except Exception as e:
                            logger.error(f"Error processing document {msg.id}: {e}")
                            continue

                await status_msg.edit_text("🔍 Searching videos... Please wait.")
                
                # Get messages with videos
                async for msg in client.iter_messages(
                    GROUP_USERNAME,
                    limit=10000,  # Increased limit
                    filter=InputMessagesFilterVideo
                ):
                    processed_count += 1
                    logger.debug(f"Processing video message {msg.id}")
                    
                    if msg.video:
                        try:
                            file_name = getattr(msg.video.attributes[0], 'file_name', 'Unnamed video')
                            if keyword in file_name.lower():
                                link = f"https://t.me/{GROUP_USERNAME}/{msg.id}"
                                found_media.append(f"🎥 {file_name}\n🔗 {link}")
                                logger.info(f"Found video: {file_name}")
                        except Exception as e:
                            logger.error(f"Error processing video {msg.id}: {e}")
                            continue

                # Prepare response
                if found_media:
                    response = f"Found {len(found_media)} media files matching '{keyword}':\n\n"
                    
                    # Split response if too long
                    if len(found_media) > 50:
                        response += "\n\n".join(found_media[:50])
                        response += f"\n\n... and {len(found_media) - 50} more items."
                    else:
                        response += "\n\n".join(found_media)
                else:
                    response = "No media found matching your search term."

                response += f"\n\nProcessed {processed_count} messages."
                await status_msg.edit_text(response)

            except Exception as e:
                logger.error(f"Error during message processing: {e}", exc_info=True)
                raise

        finally:
            await client.disconnect()

    except Exception as e:
        logger.error(f"Error in search_files: {e}", exc_info=True)
        await status_msg.edit_text(
            "An error occurred while searching. Please try again."
        )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Welcome! Send me any keyword to search for files and videos in the group. "
        "I'll give you direct links to the media."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = """
Available commands:
/start - Start the bot
/help - Show this help message

Simply send me any keyword to search for:
- Documents (files) 📄
- Videos 🎥

I'll search file names and provide you with direct links!
    """
    await update.message.reply_text(help_text)

def main() -> None:
    """Start the bot."""
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, search_files)
    )

    print("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
