#!/usr/bin/env python3
"""
Blinko Telegram Bot - A minimal bot for sending notes to Blinko

Commands:
- /configure <token> - Set Blinko API token
- /note <text> - Create a note
- /blinko <text> - Create a blinko
- /status - Check configuration
- /reset - Remove configuration

Reply to your own /note or /blinko messages to update them.

Usage:
1. Set BOT_TOKEN and BLINKO_BASE_URL in .env
2. Run: python3 bot.py
3. Configure bot with /configure <your_blinko_token>
4. Send notes with /note or /blinko commands
"""

import os
import logging
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    ContextTypes, filters
)
from dotenv import load_dotenv
from storage import UserStorage
from blinko_api import BlinkoAPI
import re

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class BlinkoTelegramBot:
    """Main Telegram bot class for Blinko integration."""
    
    def __init__(self):
        self.bot_token = os.getenv('BOT_TOKEN')
        self.blinko_base_url = os.getenv('BLINKO_BASE_URL', 'https://your-blinko-instance.com/api/v1')
        self.encryption_key = os.getenv('ENCRYPTION_KEY')
        self.database_path = os.getenv('DATABASE_PATH', './bot_data.db')
        
        if not self.bot_token:
            raise ValueError("BOT_TOKEN environment variable is required")
        
        # Initialize storage and API
        self.storage = UserStorage(self.database_path, self.encryption_key)
        self.blinko_api = BlinkoAPI(self.blinko_base_url)
        
        # Initialize application
        self.application = Application.builder().token(self.bot_token).build()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up command and message handlers."""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("configure", self.configure_command))
        self.application.add_handler(CommandHandler("note", self.note_command))
        self.application.add_handler(CommandHandler("blinko", self.blinko_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("reset", self.reset_command))
        
        # Message handler for replies to bot messages (for updates)
        self.application.add_handler(MessageHandler(
            filters.REPLY & filters.TEXT & ~filters.COMMAND, 
            self.handle_reply_update
        ))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        user = update.effective_user
        welcome_message = f"""
🎉 *Welcome to Blinko Telegram Bot!*

Hello {user.first_name}! I help you save notes to your Blinko server.

*Quick Setup:*
1. Get your Blinko API token
2. Use `/configure <your_token>` to set it up
3. Start sending notes with `/note` or `/blinko`

*Commands:*
• `/configure <token>` - Set your API token
• `/note <text>` - Save a note
• `/blinko <text>` - Save a blinko
• `/status` - Check configuration
• `/reset` - Remove stored token
• `/help` - Show help

💡 *Tip:* Reply to your own `/note` or `/blinko` messages to update them!

Ready to get started? Use `/configure` with your Blinko token!
        """
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_text = """
🤖 *Blinko Telegram Bot Help*

*Configuration:*
• `/configure <token>` - Set your Blinko API token
• `/status` - Check current configuration
• `/reset` - Remove stored configuration

*Creating Notes:*
• `/note This is my note` - Create a note
• `/blinko Remember to call mom` - Create a blinko

*Updating Notes:*
• Reply to your own note/blinko messages with new content to update them

*Examples:*
• `/note Buy groceries: milk, bread, eggs`
• `/blinko Meeting with team at 3 PM tomorrow`
• `/note #idea New feature for the app`

Need help? Make sure you've configured your token first!
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def configure_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /configure command to set user token."""
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name
        
        if not context.args:
            await update.message.reply_text(
                "❗ Please provide your Blinko API token.\n\n"
                "Usage: `/configure <your_blinko_token>`\n\n"
                "You can find your API token in your Blinko settings.",
                parse_mode='Markdown'
            )
            return
        
        token = ' '.join(context.args).strip()
        
        if len(token) < 10:
            await update.message.reply_text(
                "❗ The token seems too short. Please check and try again."
            )
            return
        
        # Test the token before storing
        await update.message.reply_text("🔄 Testing your token...")
        
        test_result = self.blinko_api.test_token(token)
        
        if not test_result['success']:
            if test_result['error'] == 'unauthorized':
                await update.message.reply_text(
                    "❌ *Invalid Token*\n\n"
                    "The provided token is not valid. Please check:\n"
                    "• Token is copied correctly\n"
                    "• Token has not expired\n"
                    "• You have proper permissions",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    f"❌ *Connection Error*\n\n"
                    f"Failed to connect to Blinko server:\n{test_result['message']}\n\n"
                    "Please check your Blinko server URL and try again.",
                    parse_mode='Markdown'
                )
            return
        
        # Store the token
        if self.storage.store_user_token(user_id, username, token):
            await update.message.reply_text(
                "✅ *Configuration Successful!*\n\n"
                "Your Blinko token has been set and verified.\n"
                "You can now send notes using `/note` or `/blinko`!\n\n"
                f"Example: `/note This is my first note`",
                parse_mode='Markdown'
            )
            logger.info(f"User {user_id} ({username}) configured successfully")
        else:
            await update.message.reply_text(
                "❌ Failed to store your configuration. Please try again."
            )
    
    async def note_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /note command to create notes."""
        await self._create_note(update, context, note_type=0, type_name="note")
    
    async def blinko_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /blinko command to create blinkos."""
        await self._create_note(update, context, note_type=1, type_name="blinko")
    
    async def _create_note(self, update: Update, context: ContextTypes.DEFAULT_TYPE, note_type: int, type_name: str):
        """Create a note with the specified type."""
        user_id = update.effective_user.id
        
        # Check if user has configured token
        token = self.storage.get_user_token(user_id)
        if not token:
            await update.message.reply_text(
                "❗ *Token Not Configured*\n\n"
                "You must configure your Blinko token first.\n"
                "Use `/configure <your_token>` to get started.",
                parse_mode='Markdown'
            )
            return
        
        # Get note content
        if not context.args:
            await update.message.reply_text(
                f"📝 Please provide {type_name} content.\n\n"
                f"Usage: `/{type_name} <your content>`\n"
                f"Example: `/{type_name} Remember to call the dentist`",
                parse_mode='Markdown'
            )
            return
        
        note_content = ' '.join(context.args).strip()
        
        if not note_content:
            await update.message.reply_text(f"❗ {type_name.title()} content cannot be empty.")
            return
        
        # Show typing indicator
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
        
        # Create the note
        result = self.blinko_api.create_note(token, note_content, note_type)
        
        if result['success']:
            note_info = ""
            if 'note_id' in result:
                note_info = f" (ID: {result['note_id']})"
            
            # Send response and store message mapping for reply-to-update functionality
            sent_message = await update.message.reply_text(
                f"✅ *{type_name.title()} Added to Blinko!*{note_info}\n\n"
                f"📝 {note_content[:100]}{'...' if len(note_content) > 100 else ''}",
                parse_mode='Markdown'
            )
            
            # Store the mapping between this telegram message and the blinko note
            if 'note_id' in result and result['note_id']:
                self.storage.store_note_message(
                    user_id, 
                    sent_message.message_id, 
                    update.effective_chat.id, 
                    str(result['note_id']), 
                    note_type
                )
            
            logger.info(f"{type_name.title()} (type {note_type}) created successfully for user {user_id}: ID {result.get('note_id', 'unknown')}")
        else:
            if result['error'] == 'unauthorized':
                await update.message.reply_text(
                    "❌ *Authentication Failed*\n\n"
                    "Your token appears to be invalid or expired.\n"
                    "Please reconfigure with `/configure <new_token>`",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    f"❌ *Failed to Add {type_name.title()}*\n\n"
                    f"Error: {result['message']}\n\n"
                    "Please try again or check your configuration.",
                    parse_mode='Markdown'
                )
            logger.error(f"Failed to create {type_name} for user {user_id}: {result['message']}")
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command to show configuration status."""
        user_id = update.effective_user.id
        config = self.storage.get_user_config(user_id)
        
        if not config:
            await update.message.reply_text(
                "❌ *Not Configured*\n\n"
                "You haven't set up your Blinko token yet.\n"
                "Use `/configure <your_token>` to get started.",
                parse_mode='Markdown'
            )
            return
        
        # Test current token
        test_result = self.blinko_api.test_token(config['token'])
        status_emoji = "✅" if test_result['success'] else "❌"
        status_text = "Active" if test_result['success'] else "Invalid/Expired"
        
        status_message = f"""
{status_emoji} *Configuration Status*

👤 *User:* {config['username']}
🔑 *Token:* {status_text}
🌐 *Blinko URL:* {self.blinko_base_url}
📅 *Configured:* {config['created_at'][:10]}

{f"⚠️ Token issue: {test_result['message']}" if not test_result['success'] else "🎉 Ready to send notes!"}
        """
        
        await update.message.reply_text(status_message, parse_mode='Markdown')
    
    async def reset_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /reset command to remove user configuration."""
        user_id = update.effective_user.id
        
        if self.storage.remove_user_token(user_id):
            await update.message.reply_text(
                "✅ *Configuration Removed*\n\n"
                "Your Blinko token has been deleted from our secure storage.\n"
                "Use `/configure <token>` to set it up again.",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "❌ Failed to remove configuration or no configuration found."
            )
    
    async def handle_reply_update(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle replies to bot messages for updating notes/blinkos."""
        user_id = update.effective_user.id
        
        # Check if user has configured token
        token = self.storage.get_user_token(user_id)
        if not token:
            await update.message.reply_text(
                "❗ *Token Not Configured*\n\n"
                "You must configure your Blinko token first.\n"
                "Use `/configure <your_token>` to get started.",
                parse_mode='Markdown'
            )
            return
        
        # Check if this is a reply to a bot message that contains a note
        reply_to_message = update.message.reply_to_message
        if not reply_to_message or reply_to_message.from_user.id != context.bot.id:
            return  # Not a reply to the bot
        
        # Check if we have a note mapping for this message
        note_info = self.storage.get_note_from_reply(
            user_id, 
            reply_to_message.message_id, 
            update.effective_chat.id
        )
        
        if not note_info:
            return  # No note mapping found
        
        new_content = update.message.text.strip()
        if not new_content:
            await update.message.reply_text("❗ Update content cannot be empty.")
            return
        
        # Show typing indicator
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
        
        # Update the note
        result = self.blinko_api.update_note(
            token, 
            note_info['note_id'], 
            new_content, 
            note_info['note_type']
        )
        
        type_name = "note" if note_info['note_type'] == 0 else "blinko"
        
        if result['success']:
            # Send confirmation and store new message mapping
            sent_message = await update.message.reply_text(
                f"✅ *{type_name.title()} Updated!*\n\n"
                f"📝 {new_content[:100]}{'...' if len(new_content) > 100 else ''}",
                parse_mode='Markdown'
            )
            
            # Store the new message mapping
            self.storage.store_note_message(
                user_id, 
                sent_message.message_id, 
                update.effective_chat.id, 
                note_info['note_id'], 
                note_info['note_type']
            )
            
            logger.info(f"{type_name.title()} updated successfully for user {user_id}: ID {note_info['note_id']}")
        else:
            if result['error'] == 'unauthorized':
                await update.message.reply_text(
                    "❌ *Authentication Failed*\n\n"
                    "Your token appears to be invalid or expired.\n"
                    "Please reconfigure with `/configure <new_token>`",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    f"❌ *Failed to Update {type_name.title()}*\n\n"
                    f"Error: {result['message']}\n\n"
                    "Please try again or check your configuration.",
                    parse_mode='Markdown'
                )
            logger.error(f"Failed to update {type_name} for user {user_id}: {result['message']}")
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors."""
        logger.error(f"Exception while handling an update: {context.error}")
    
    def run(self):
        """Start the bot."""
        self.application.add_error_handler(self.error_handler)
        
        logger.info("Starting Blinko Telegram Bot...")
        logger.info(f"Configured users: {self.storage.get_user_count()}")
        
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

def main():
    """Main function to run the bot."""
    try:
        bot = BlinkoTelegramBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise

if __name__ == '__main__':
    main()
