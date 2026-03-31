import os
import httpx
import asyncio
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
PPLX_API_KEY = os.environ.get("PPLX_API_KEY", "")
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
PORT = int(os.environ.get("PORT", 3000))

# Per-chat conversation history
conversations: dict[int, list[dict]] = {}

SYSTEM_PROMPT = (
    "You are Jarvis, a smart, friendly, and helpful AI assistant. "
    "You are concise, warm, and helpful. You respond in the same language the user uses. "
    "Keep responses short and conversational since this is a Telegram chat. "
    "You can help with anything — questions, ideas, advice, writing, coding, and more."
)

# --- Tiny health check HTTP server so Railway doesn't kill the process ---
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Jarvis is running")
    def log_message(self, *args):
        pass  # Suppress HTTP logs

def start_health_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    log.info(f"Health check server on port {PORT}")
    server.serve_forever()

# --- Telegram Bot Logic ---

async def send_message(client: httpx.AsyncClient, chat_id: int, text: str):
    try:
        await client.post(f"{TELEGRAM_API}/sendMessage", json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        })
    except Exception:
        await client.post(f"{TELEGRAM_API}/sendMessage", json={
            "chat_id": chat_id,
            "text": text
        })


async def send_typing(client: httpx.AsyncClient, chat_id: int):
    try:
        await client.post(f"{TELEGRAM_API}/sendChatAction", json={
            "chat_id": chat_id,
            "action": "typing"
        })
    except Exception:
        pass


async def get_ai_response(chat_id: int, user_message: str) -> str:
    if chat_id not in conversations:
        conversations[chat_id] = [{"role": "system", "content": SYSTEM_PROMPT}]

    conversations[chat_id].append({"role": "user", "content": user_message})

    if len(conversations[chat_id]) > 21:
        conversations[chat_id] = [conversations[chat_id][0]] + conversations[chat_id][-20:]

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {PPLX_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "sonar",
                "messages": conversations[chat_id],
                "max_tokens": 500
            }
        )
        response.raise_for_status()
        data = response.json()
        reply = data["choices"][0]["message"]["content"]
        conversations[chat_id].append({"role": "assistant", "content": reply})
        return reply


async def handle_message(client: httpx.AsyncClient, message: dict):
    chat_id = message["chat"]["id"]
    text = message.get("text", "")

    if not text:
        return

    log.info(f"Message from {chat_id}: {text[:60]}")

    if text == "/start":
        await send_message(client, chat_id,
            "👋 Hey! I'm *Jarvis*, your personal AI assistant.\n\n"
            "Send me any message and I'll help — questions, writing, coding, ideas, anything!\n\n"
            "Type /clear to reset the conversation."
        )
        return

    if text == "/clear":
        conversations.pop(chat_id, None)
        await send_message(client, chat_id, "🧹 Conversation cleared!")
        return

    if text == "/help":
        await send_message(client, chat_id,
            "*Commands:*\n/start — Welcome\n/clear — Reset conversation\n/help — This message\n\nJust type anything to chat!"
        )
        return

    await send_typing(client, chat_id)

    try:
        reply = await get_ai_response(chat_id, text)
        await send_message(client, chat_id, reply)
    except Exception as e:
        log.error(f"Error getting AI response: {e}")
        await send_message(client, chat_id, "Sorry, something went wrong. Please try again.")


async def run_polling():
    if not BOT_TOKEN:
        log.error("BOT_TOKEN not set!")
        return
    if not PPLX_API_KEY:
        log.error("PPLX_API_KEY not set!")
        return

    log.info("Jarvis bot starting (long polling)...")
    offset = 0

    async with httpx.AsyncClient(timeout=60) as client:
        await client.post(f"{TELEGRAM_API}/deleteWebhook")
        log.info("Polling active — waiting for messages...")

        while True:
            try:
                response = await client.post(
                    f"{TELEGRAM_API}/getUpdates",
                    json={"offset": offset, "timeout": 30, "allowed_updates": ["message"]}
                )
                data = response.json()

                if not data.get("ok"):
                    log.warning(f"Telegram API error: {data}")
                    await asyncio.sleep(5)
                    continue

                for update in data.get("result", []):
                    offset = update["update_id"] + 1
                    if "message" in update:
                        asyncio.create_task(handle_message(client, update["message"]))

            except httpx.ReadTimeout:
                continue
            except Exception as e:
                log.error(f"Polling error: {e}")
                await asyncio.sleep(5)


if __name__ == "__main__":
    # Start health check server in background thread (Railway requires an open port)
    thread = threading.Thread(target=start_health_server, daemon=True)
    thread.start()

    # Run the bot
    asyncio.run(run_polling())
