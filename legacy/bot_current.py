#!/usr/bin/env python3
import os, logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN not set")

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 **KOSFintech Bot (Base)**\n\n"
        "This is the minimal working version.\n"
        "Features will be added step by step.\n\n"
        "Type /ping to test connectivity."
    )

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏓 Pong! Bot is alive.")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ping", ping))
    print("🤖 Minimal bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
# ========== EXTRACTION SERVICES ==========
import re, csv, io, sqlite3, random, json, datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler, filters, CallbackQueryHandler

SERVICE_CONFIG = {
    'whatsapp': {'pattern': r'([A-Za-z\s]+):\s*(\+?\d{10,15})', 'headers': ["Name", "Phone Number"], 'prefix': 'whatsapp_numbers', 'help': 'Extract names and phone numbers.'},
app.run_polling(timeout=30, drop_pending_updates=True)    'email': {'pattern': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', 'headers': ["Email"], 'prefix': 'extracted_emails', 'help': 'Extract email addresses.'},
    'social': {'pattern': r'(?:@|instagram\.com/|twitter\.com/|linkedin\.com/in/)([a-zA-Z0-9_.-]+)', 'headers': ["Social Handle"], 'prefix': 'social_handles', 'help': 'Extract social handles.'},
    'nin': {'pattern': r'\b\d{11}\b', 'headers': ["NIN"], 'prefix': 'nin_numbers', 'help': 'Extract NIN numbers.'},
    'bvn': {'pattern': r'\b\d{11}\b', 'headers': ["BVN"], 'prefix': 'bvn_numbers', 'help': 'Extract BVN numbers.'},
    'urls': {'pattern': r'https?://[^\s]+', 'headers': ["URL"], 'prefix': 'extracted_urls', 'help': 'Extract URLs.'},
    'agents': {'pattern': r'([A-Za-z\s]+):\s*([A-Za-z\s]+)\s*(\+?\d{10,15})', 'headers': ["Trade", "Name", "Phone Number"], 'prefix': 'service_agents', 'help': 'Extract service agents.'},
}

async def handle_file(update, context):
    user_id = update.effective_user.id
    doc = update.message.document
    if not doc or not doc.file_name.endswith('.txt'):
        await update.message.reply_text("❌ Send a .txt file.")
        return
    service = context.user_data.get('service', 'whatsapp')
    config = SERVICE_CONFIG.get(service)
    if not config:
        service = 'whatsapp'
        config = SERVICE_CONFIG['whatsapp']
    pattern, headers, prefix = config['pattern'], config['headers'], config['prefix']
    try:
        file = await context.bot.get_file(doc.file_id)
        path = f"/tmp/{doc.file_name}"
        await file.download_to_drive(path)
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        if service == 'whatsapp':
            matches = re.findall(pattern, content)
            data = []
            for name, num in matches:
                clean = re.sub(r'[\s\-\(\)]', '', num)
                if len(clean) >= 10:
                    data.append((name.strip(), clean))
            seen = set(); unique_data = []
            for name, num in data:
                if num not in seen:
                    seen.add(num); unique_data.append((name, num))
        elif service == 'agents':
            matches = re.findall(pattern, content)
            unique_data = []
            seen = set()
            for trade, name, num in matches:
                clean = re.sub(r'[\s\-\(\)]', '', num)
                if len(clean) >= 10:
                    key = (trade.strip(), name.strip(), clean)
                    if key not in seen:
                        seen.add(key); unique_data.append(key)
        else:
            raw = re.findall(pattern, content)
            unique_data = list(set(raw)) if service in ('nin','bvn') else list(set([m.strip() for m in raw]))
        if not unique_data:
            await update.message.reply_text("❌ No matches found.")
            os.remove(path); return
        csv_path = path.replace('.txt', '.csv')
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            if service == 'whatsapp':
                for name, num in unique_data: writer.writerow([name, num])
            elif service == 'agents':
                for trade, name, num in unique_data: writer.writerow([trade, name, num])
            else:
                for item in unique_data: writer.writerow([item])
        with open(csv_path, 'rb') as f:
            await update.message.reply_document(document=f, filename=f"{prefix}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        await update.message.reply_text("✅ Extraction complete!")
        os.remove(path); os.remove(csv_path)
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
        logging.error(f"File error: {e}")

async def service_command(update, context, svc):
    if svc in SERVICE_CONFIG:
        context.user_data['service'] = svc
        await update.message.reply_text(f"✅ Service selected: {svc.upper()}. Send .txt file.")
    else:
        await update.message.reply_text("❌ Unknown service.")

async def whatsapp(update, context): await service_command(update, context, 'whatsapp')
async def email(update, context): await service_command(update, context, 'email')
async def social(update, context): await service_command(update, context, 'social')
async def nin(update, context): await service_command(update, context, 'nin')
async def bvn(update, context): await service_command(update, context, 'bvn')
async def urls(update, context): await service_command(update, context, 'urls')
async def agents(update, context): await service_command(update, context, 'agents')
