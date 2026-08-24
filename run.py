#!/usr/bin/env python3
"""
Casino Bot - Main entry point.
Starts both the Telegram bot and the FastAPI server.

Usage:
    python run.py                    # Run both bot + API
    python run.py --bot-only         # Bot only
    python run.py --api-only         # API only (for testing)
"""

import asyncio
import sys
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from bot import register_handlers
from api.server import app
import config

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_bot():
    """Run the Telegram bot."""
    bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
    dp = Dispatcher()

    register_handlers(dp)

    logger.info("Bot starting...")
    await dp.start_polling(bot)


async def run_api():
    """Run the FastAPI server."""
    import uvicorn
    config_uvicorn = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
    server = uvicorn.Server(config_uvicorn)

    logger.info("API starting on port 8000...")
    await server.serve()


async def main():
    """Run both bot and API concurrently."""
    if "--bot-only" in sys.argv:
        await run_bot()
    elif "--api-only" in sys.argv:
        await run_api()
    else:
        # Run both
        logger.info("Starting Casino Bot (bot + API)...")
        await asyncio.gather(
            run_bot(),
            run_api()
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
