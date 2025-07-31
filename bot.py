
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import requests
from apscheduler.schedulers.background import BackgroundScheduler
import config

user_regions = {}
latest_status = {}

def fetch_alerts():
    try:
        response = requests.get("https://api.ukrainealarm.com/api/v3/alerts/regions", timeout=10)
        return response.json()
    except:
        return []

async def check_alerts(bot):
    data = fetch_alerts()
    for chat_id, regions in user_regions.items():
        for region in regions:
            region_data = next((r for r in data if r['name'] == region), None)
            if not region_data:
                continue
            is_alarm = region_data['alarm']
            key = f"{chat_id}:{region}"
            last_status = latest_status.get(key, None)
            if last_status is None:
                latest_status[key] = is_alarm
                continue
            if last_status != is_alarm:
                latest_status[key] = is_alarm
                msg = f"🚨 Повітряна тривога в {region}!" if is_alarm else f"✅ Відбій тривоги в {region}."
                await bot.send_message(chat_id=chat_id, text=msg)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_regions[chat_id] = ["Чернігівська"]
    await update.message.reply_text("👋 Бот активовано. Стежу за тривогами в Чернігівській області.")

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in user_regions:
        user_regions[chat_id] = []
    region = " ".join(context.args)
    if region:
        user_regions[chat_id].append(region)
        await update.message.reply_text(f"✅ Додано область: {region}")
    else:
        await update.message.reply_text("❗ Вкажіть назву області після команди, наприклад:\n/add Київська")

if __name__ == "__main__":
    app = ApplicationBuilder().token(config.TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add))
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: app.create_task(check_alerts(app.bot)), "interval", seconds=30)
    scheduler.start()
    app.run_polling()
