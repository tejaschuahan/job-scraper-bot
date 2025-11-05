"""
Interactive Telegram Job Scraper Bot
Asks user for job role and automatically scrapes related positions
"""

import asyncio
import logging
import os
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters
)
from job_scraper import JobScraper
import yaml

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
ASKING_ROLE, CONFIRMING = range(2)

# Job role mappings with related roles
JOB_ROLE_MAPPINGS = {
    'data analyst': [
        'data analyst',
        'business analyst',
        'business intelligence analyst',
        'BI analyst',
        'insights analyst',
        'reporting analyst',
        'analytics engineer'
    ],
    'data scientist': [
        'data scientist',
        'machine learning engineer',
        'AI engineer',
        'research scientist',
        'quantitative analyst',
        'decision scientist',
        'statistical analyst'
    ],
    'data engineer': [
        'data engineer',
        'analytics engineer',
        'big data engineer',
        'ETL developer',
        'data platform engineer',
        'database engineer'
    ],
    'business analyst': [
        'business analyst',
        'data analyst',
        'product analyst',
        'operations analyst',
        'process analyst',
        'systems analyst',
        'functional analyst'
    ],
    'financial analyst': [
        'financial analyst',
        'finance analyst',
        'investment analyst',
        'risk analyst',
        'credit analyst',
        'quantitative analyst',
        'treasury analyst'
    ],
    'product analyst': [
        'product analyst',
        'product manager',
        'business analyst',
        'data analyst',
        'growth analyst',
        'metrics analyst'
    ],
    'marketing analyst': [
        'marketing analyst',
        'digital marketing analyst',
        'market research analyst',
        'growth analyst',
        'performance analyst',
        'SEO analyst'
    ],
    'operations analyst': [
        'operations analyst',
        'business analyst',
        'process analyst',
        'supply chain analyst',
        'logistics analyst',
        'operational excellence analyst'
    ],
    'power bi developer': [
        'power bi developer',
        'business intelligence developer',
        'BI developer',
        'tableau developer',
        'data visualization specialist',
        'reporting developer'
    ],
    'tableau developer': [
        'tableau developer',
        'power bi developer',
        'business intelligence developer',
        'data visualization specialist',
        'BI developer',
        'analytics developer'
    ]
}

# Predefined role suggestions
ROLE_KEYBOARD = [
    ['Data Analyst', 'Data Scientist'],
    ['Data Engineer', 'Business Analyst'],
    ['Financial Analyst', 'Product Analyst'],
    ['Marketing Analyst', 'Operations Analyst'],
    ['Power BI Developer', 'Tableau Developer'],
    ['Custom Role (Type your own)']
]


class InteractiveJobBot:
    def __init__(self, config_path: str = 'config.yaml'):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.scraper = None
        self.active_searches = {}  # Store active search tasks per user
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command - welcome message"""
        user = update.effective_user
        await update.message.reply_text(
            f"👋 Hi {user.first_name}!\n\n"
            f"I'm your personal **Job Scraper Bot**. I'll help you find job opportunities "
            f"across multiple job sites in India!\n\n"
            f"🔍 I can search for:\n"
            f"• Data Analyst & related roles\n"
            f"• Data Scientist & ML Engineer roles\n"
            f"• Data Engineer & Big Data roles\n"
            f"• Business Analyst & related roles\n"
            f"• And many more...\n\n"
            f"Use /search to start finding jobs!\n"
            f"Use /stop to stop your active search\n"
            f"Use /status to check your current search",
            parse_mode='Markdown'
        )
    
    async def search_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start job search conversation"""
        reply_markup = ReplyKeyboardMarkup(ROLE_KEYBOARD, one_time_keyboard=True, resize_keyboard=True)
        
        await update.message.reply_text(
            "🎯 **What job role are you looking for?**\n\n"
            "Select from the options below or type your own custom role:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        return ASKING_ROLE
    
    async def receive_role(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive job role from user"""
        user_input = update.message.text.strip()
        
        # Handle custom role option
        if user_input == "Custom Role (Type your own)":
            await update.message.reply_text(
                "✍️ Please type the job role you're looking for:\n"
                "(e.g., 'Software Engineer', 'HR Manager', 'DevOps Engineer')",
                reply_markup=ReplyKeyboardRemove()
            )
            return ASKING_ROLE
        
        # Store user's choice
        context.user_data['job_role'] = user_input.lower()
        
        # Get related roles
        related_roles = self.get_related_roles(user_input.lower())
        context.user_data['related_roles'] = related_roles
        
        # Show confirmation with related roles
        roles_text = "\n".join([f"  • {role.title()}" for role in related_roles])
        
        await update.message.reply_text(
            f"✅ Got it! I'll search for **{user_input}**\n\n"
            f"📋 I'll also include these related roles:\n{roles_text}\n\n"
            f"🌍 Location: India (Bangalore, Mumbai, Delhi, Hyderabad, etc.)\n"
            f"🌐 Sites: LinkedIn, TimesJobs, Remotive, Naukri, Foundit, and more\n\n"
            f"⏰ I'll scrape jobs every 5 minutes and send you new opportunities!\n\n"
            f"Ready to start? Type 'YES' to begin or 'NO' to cancel.",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode='Markdown'
        )
        
        return CONFIRMING
    
    async def confirm_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Confirm and start scraping"""
        user_response = update.message.text.strip().upper()
        
        if user_response not in ['YES', 'Y', 'START', 'OK']:
            await update.message.reply_text(
                "❌ Search cancelled. Use /search to start again."
            )
            return ConversationHandler.END
        
        user_id = update.effective_user.id
        job_role = context.user_data.get('job_role')
        related_roles = context.user_data.get('related_roles', [])
        
        await update.message.reply_text(
            f"🚀 Starting job search for **{job_role.title()}**!\n\n"
            f"🔄 Running first scrape now... (this may take 30-60 seconds)\n"
            f"⏱️ After that, I'll check every 5 minutes for new jobs.\n\n"
            f"📬 You'll receive notifications for each new job found!\n\n"
            f"Use /stop to stop the search anytime.",
            parse_mode='Markdown'
        )
        
        # Start background scraping task
        task = asyncio.create_task(
            self.run_continuous_scraping(user_id, related_roles, context.bot)
        )
        self.active_searches[user_id] = {
            'task': task,
            'role': job_role,
            'queries': related_roles
        }
        
        return ConversationHandler.END
    
    def get_related_roles(self, job_role: str):
        """Get related job roles based on user input"""
        # Normalize input
        job_role = job_role.lower().strip()
        
        # Check if exact match in mappings
        if job_role in JOB_ROLE_MAPPINGS:
            return JOB_ROLE_MAPPINGS[job_role]
        
        # Check if input contains key role names
        for key, roles in JOB_ROLE_MAPPINGS.items():
            if key in job_role or job_role in key:
                return roles
        
        # If no match, create a basic list with the input and variations
        base_roles = [job_role]
        
        # Add common variations
        if 'analyst' in job_role:
            if 'data' not in job_role:
                base_roles.append(f"data {job_role}")
            if 'business' not in job_role:
                base_roles.append(f"business {job_role}")
        
        if 'engineer' in job_role:
            if 'data' not in job_role:
                base_roles.append(f"data {job_role}")
        
        if 'developer' in job_role:
            base_roles.append(job_role.replace('developer', 'engineer'))
        
        return base_roles[:5]  # Limit to 5 roles
    
    async def run_continuous_scraping(self, user_id: int, queries: list, bot):
        """Run continuous scraping for a user"""
        try:
            # Load configuration
            with open('config.yaml', 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # Override with environment variables if available
            if os.getenv('TELEGRAM_BOT_TOKEN'):
                config['telegram']['bot_token'] = os.getenv('TELEGRAM_BOT_TOKEN')
            if os.getenv('TELEGRAM_CHAT_ID'):
                config['telegram']['chat_id'] = os.getenv('TELEGRAM_CHAT_ID')
            
            # Override telegram config to send to this specific user
            config['telegram']['chat_id'] = str(user_id)
            
            # Initialize scraper with modified config
            scraper = JobScraper(config)
            
            # Create aiohttp session for scraping
            import aiohttp
            from job_scraper import UserAgentRotator
            timeout = aiohttp.ClientTimeout(total=30)
            connector = aiohttp.TCPConnector(
                limit=config.get('scraping', {}).get('connection_pool_size', 10),
                limit_per_host=5
            )
            scraper.session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                headers={'User-Agent': UserAgentRotator.get_random()}
            )
            
            cycle_count = 0
            
            while True:
                cycle_count += 1
                logger.info(f"Running scraping cycle {cycle_count} for user {user_id}")
                
                try:
                    # Run scraping cycle
                    await scraper.run_scraping_cycle(queries)
                    
                    # Send status update every 10 cycles
                    if cycle_count % 10 == 0:
                        total_jobs = len(scraper.seen_jobs)
                        await bot.send_message(
                            chat_id=user_id,
                            text=f"📊 Status Update (Cycle {cycle_count})\n"
                                 f"💾 Total jobs tracked: {total_jobs}\n"
                                 f"✅ Bot is running smoothly!\n\n"
                                 f"Use /stop to stop the search."
                        )
                    
                except Exception as e:
                    logger.error(f"Error in scraping cycle for user {user_id}: {e}")
                    await bot.send_message(
                        chat_id=user_id,
                        text=f"⚠️ Error in scraping cycle: {str(e)}\n"
                             f"Will retry in next cycle..."
                    )
                
                # Wait for next cycle (5 minutes)
                interval = scraper.config.get('scraping', {}).get('interval', 300)
                await asyncio.sleep(interval)
                
        except asyncio.CancelledError:
            logger.info(f"Scraping stopped for user {user_id}")
            # Close the session
            if scraper.session:
                await scraper.session.close()
            await bot.send_message(
                chat_id=user_id,
                text="🛑 Job search stopped successfully!"
            )
        except Exception as e:
            logger.error(f"Fatal error in scraping for user {user_id}: {e}")
            # Close the session
            if scraper.session:
                await scraper.session.close()
            await bot.send_message(
                chat_id=user_id,
                text=f"❌ Fatal error: {str(e)}\n"
                     f"Please use /search to start a new search."
            )
    
    async def stop_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Stop active job search"""
        user_id = update.effective_user.id
        
        if user_id not in self.active_searches:
            await update.message.reply_text(
                "❌ No active search found.\n"
                "Use /search to start a new job search."
            )
            return
        
        # Cancel the task
        search_info = self.active_searches[user_id]
        search_info['task'].cancel()
        
        del self.active_searches[user_id]
        
        await update.message.reply_text(
            f"🛑 Stopped searching for **{search_info['role'].title()}** jobs.\n\n"
            f"Use /search to start a new search anytime!",
            parse_mode='Markdown'
        )
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check current search status"""
        user_id = update.effective_user.id
        
        if user_id not in self.active_searches:
            await update.message.reply_text(
                "ℹ️ No active search running.\n"
                "Use /search to start finding jobs!"
            )
            return
        
        search_info = self.active_searches[user_id]
        queries_text = "\n".join([f"  • {q.title()}" for q in search_info['queries']])
        
        await update.message.reply_text(
            f"🔄 **Active Search Status**\n\n"
            f"🎯 Main Role: {search_info['role'].title()}\n"
            f"📋 Searching for:\n{queries_text}\n\n"
            f"✅ Bot is actively running!\n"
            f"📬 You'll receive notifications for new jobs.\n\n"
            f"Use /stop to stop the search.",
            parse_mode='Markdown'
        )
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel conversation"""
        await update.message.reply_text(
            "❌ Cancelled. Use /search to start again.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show help message"""
        await update.message.reply_text(
            "🤖 **Job Scraper Bot - Help**\n\n"
            "**Commands:**\n"
            "/start - Welcome message\n"
            "/search - Start a new job search\n"
            "/stop - Stop your active search\n"
            "/status - Check your current search status\n"
            "/help - Show this help message\n\n"
            "**How it works:**\n"
            "1️⃣ Use /search and tell me what job you want\n"
            "2️⃣ I'll automatically search related roles\n"
            "3️⃣ You'll get notifications for new jobs every 5 minutes\n"
            "4️⃣ Use /stop when you want to stop\n\n"
            "**Supported Sites:**\n"
            "LinkedIn, TimesJobs, Remotive, Naukri, Foundit, Shine, and more!\n\n"
            "**Location:** India (all major cities)",
            parse_mode='Markdown'
        )
    
    def run(self):
        """Run the bot"""
        token = self.config['telegram']['bot_token']
        
        # Create application
        application = Application.builder().token(token).build()
        
        # Conversation handler for job search
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('search', self.search_command)],
            states={
                ASKING_ROLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_role)],
                CONFIRMING: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.confirm_search)],
            },
            fallbacks=[CommandHandler('cancel', self.cancel)],
        )
        
        # Add handlers
        application.add_handler(CommandHandler('start', self.start))
        application.add_handler(conv_handler)
        application.add_handler(CommandHandler('stop', self.stop_command))
        application.add_handler(CommandHandler('status', self.status_command))
        application.add_handler(CommandHandler('help', self.help_command))
        
        # Start the bot
        logger.info("🤖 Interactive Job Scraper Bot started!")
        logger.info("Waiting for users to start job searches...")
        
        application.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    """Main entry point"""
    bot = InteractiveJobBot('config.yaml')
    bot.run()


if __name__ == '__main__':
    main()
