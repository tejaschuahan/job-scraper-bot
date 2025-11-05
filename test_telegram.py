"""Quick test script to verify Telegram credentials"""
import asyncio
from telegram import Bot
from telegram.error import TelegramError
import yaml

async def test_telegram():
    # Load config
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    bot_token = config['telegram']['bot_token']
    chat_id = config['telegram']['chat_id']
    
    print(f"🤖 Testing Telegram bot...")
    print(f"Bot Token: {bot_token[:20]}...")
    print(f"Chat ID: {chat_id}")
    
    try:
        bot = Bot(token=bot_token)
        
        # Get bot info
        me = await bot.get_me()
        print(f"\n✅ Bot connected successfully!")
        print(f"Bot Username: @{me.username}")
        print(f"Bot Name: {me.first_name}")
        
        # Send test message
        print(f"\n📤 Sending test message...")
        message = await bot.send_message(
            chat_id=chat_id,
            text="🎉 **Job Scraper Bot Test**\n\nYour bot is configured correctly and ready to run!\n\nYou will receive job notifications here.",
            parse_mode='Markdown'
        )
        
        print(f"✅ Test message sent successfully!")
        print(f"Message ID: {message.message_id}")
        print(f"\n🎯 Everything looks good! You can now run the job scraper.")
        
    except TelegramError as e:
        print(f"\n❌ Telegram Error: {e}")
        if "Unauthorized" in str(e):
            print("➡️  Check your bot token - it might be invalid")
        elif "Chat not found" in str(e):
            print("➡️  Check your chat ID - make sure you've started a conversation with the bot first")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_telegram())
    if not success:
        print("\n⚠️  Please fix the errors above before running the job scraper.")
