# Jarvis Telegram Bot

Your personal AI assistant on Telegram (@MehranixBot).

## Deploy to Railway (Free, Permanent)

### Step 1 — Get a Perplexity API Key
1. Go to https://www.perplexity.ai/settings/api
2. Click **Generate** to create a new API key
3. Copy it — you'll need it in Step 3

### Step 2 — Deploy to Railway
1. Go to https://railway.app and sign up (free)
2. Click **New Project** → **Deploy from GitHub repo**
   - OR click **New Project** → **Empty Project** → **Add Service** → **GitHub Repo**
3. Connect your GitHub account and push this folder as a repo:
   ```bash
   cd jarvis-bot
   git init
   git add .
   git commit -m "Jarvis bot"
   # Create a new repo on github.com, then:
   git remote add origin https://github.com/YOUR_USERNAME/jarvis-bot.git
   git push -u origin main
   ```
4. Railway will auto-detect and deploy it

### Step 3 — Set Environment Variables in Railway
In your Railway project dashboard:
1. Click your service → **Variables** tab
2. Add these variables:
   - `BOT_TOKEN` = `8639981960:AAFsX69UAEefEk9UNUhtNTa4KtY-IDI81fE`
   - `PPLX_API_KEY` = `your_perplexity_api_key_here`
3. Railway will automatically restart the bot

### Step 4 — Chat with Jarvis!
Open Telegram and search for **@MehranixBot** or go to https://t.me/MehranixBot

## Commands
- Just type anything to chat
- `/clear` — Reset the conversation
- `/help` — Show available commands

## Cost
- Railway free tier: **$5/month free credits** (more than enough for a bot)
- Perplexity `sonar` model: very cheap (~$1 per million tokens)
