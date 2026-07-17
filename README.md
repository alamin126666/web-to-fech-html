# 📥 HTML Fetcher Telegram Bot

Telegram bot যেটা যেকোনো URL থেকে real HTML fetch করে ফাইল হিসেবে পাঠায়।  
Anti-bot challenge (AES cookie challenge) অটোমেটিক সলভ করে।

---

## ⚙️ Features

- `/start` → keyboard button আসে
- **📥 FECH HTML** বাটন → URL চাইবে
- URL দিলে HTML file পাঠাবে
- **Anti-bot detection:** AES cookie challenge অটো সলভ করে real HTML আনে
- **Advanced protection detect করলে** user-friendly error দেয়

---

## 🚀 Deploy করার ধাপ

### 1. GitHub-এ Push করো
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### 2. Render-এ Deploy করো
1. [render.com](https://render.com) এ যাও
2. **New → Web Service** → GitHub repo connect করো
3. Environment Variable যোগ করো:
   - Key: `BOT_TOKEN`
   - Value: তোমার BotFather token
4. **Deploy** চাপো

### 3. Cron-job.org দিয়ে Keep-Alive সেট করো
1. [cron-job.org](https://cron-job.org) এ account খোলো
2. New cronjob → URL: `https://YOUR-APP.onrender.com/health`
3. Schedule: **Every 5 minutes**
4. Save করো

---

## 🔑 Environment Variables

| Variable   | Description                        |
|------------|------------------------------------|
| `BOT_TOKEN` | Telegram bot token (@BotFather)   |
| `PORT`      | Flask port (Render auto-set করে)  |

---

## 📁 File Structure

```
├── main.py          # Entry point: Flask + bot polling thread
├── bot.py           # Telegram bot handlers
├── fetcher.py       # HTML fetch + anti-bot solver
├── requirements.txt
├── render.yaml      # Render deploy config
└── .env.example
```

---

## 🛡️ Anti-Bot Support

| Protection Type         | Status      |
|------------------------|-------------|
| AES Cookie Challenge   | ✅ Auto Solved |
| Meta-Refresh Redirect  | ✅ Followed   |
| Cloudflare JS Challenge| ❌ Not supported (needs real browser) |
