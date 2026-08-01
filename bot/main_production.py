"""
Production entrypoint — webhook mode via FastAPI + uvicorn.
Cocok untuk deployment di VPS dengan Cloudflare Zero Trust.

Jalankan:
    python -m bot.main_production
"""
import logging

from fastapi import FastAPI, Request
from telegram import Update
from uvicorn import Config, Server

from bot import config
from bot.main import build_app

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

fastapi_app = FastAPI(title="Disaster Response Bot")
telegram_app = None


@fastapi_app.on_event("startup")
async def startup():
    global telegram_app
    config.validate_config()
    telegram_app = build_app()
    await telegram_app.initialize()
    await telegram_app.start()
    
    if config.WEBHOOK_URL:
        webhook_url = f"{config.WEBHOOK_URL}/webhook"
        await telegram_app.bot.set_webhook(url=webhook_url)
        logger.info(f"Webhook set: {webhook_url}")
    else:
        logger.warning("WEBHOOK_URL not set — bot won't receive updates via webhook")


@fastapi_app.on_event("shutdown")
async def shutdown():
    if telegram_app:
        await telegram_app.stop()
        await telegram_app.shutdown()


@fastapi_app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"ok": True}


@fastapi_app.get("/health")
async def health():
    return {"status": "ok", "service": "disaster-response-bot"}


def main():
    logger.info(f"Starting production server on 0.0.0.0:{config.PORT}")
    server_config = Config(
        app=fastapi_app,
        host="0.0.0.0",
        port=config.PORT,
        log_level="info",
    )
    server = Server(server_config)
    server.run()


if __name__ == "__main__":
    main()
