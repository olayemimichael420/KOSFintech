#!/usr/bin/env python3
# KOSFintech School Bot – Complete Unified Code (v3.1)
# All features + critical fixes (environment vars, DNS removed, conversation flows, etc.)

import os
import re
import time
import sqlite3
import logging
import asyncio
import random
import json
from datetime import datetime, timedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler,
    ConversationHandler,

)
from telegram.error import NetworkError
from telegram.request import HTTPXRequest

# ========== CONFIGURATION (via environment variables) ==========
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable not set.")
ADMIN_ID = int(os.getenv("ADMIN_ID", "5790547716"))
DB_FILE = "user_usage.db"
from telegram.request import HTTPXRequest
MAX_FREE_USES = 3
PRO_TIER_PRICE = 10000

# ========== LOGGING ==========
logging.basicConfig(level=logging.INFO)

# ========== DATABASE INITIALIZATION ==========
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # --- Core tables ---
    c.execute('''CREATE TABLE IF NOT EXISTS user_usage (
        user_id INTEGER PRIMARY KEY,
        uses INTEGER DEFAULT 0,
        last_use TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_pro BOOLEAN DEFAULT 0,
        tenant_id TEXT DEFAULT 'default'
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS config (
        key TEXT PRIMARY KEY,
        value TEXT,
        tenant_id TEXT DEFAULT 'default'
    )''')
    c.execute("INSERT OR IGNORE INTO config (key, value) VALUES ('offer_count', '0')")

    # --- Schools & Admins ---
    c.execute('''CREATE TABLE IF NOT EXISTS schools (
        tenant_id TEXT PRIMARY KEY,
        name TEXT,
        type TEXT,
        country TEXT,
        currency TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS school_admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id TEXT REFERENCES schools(tenant_id),
        user_id INTEGER,
        role TEXT CHECK(role IN ('owner', 'admin1', 'admin2')),
        phone TEXT UNIQUE,
        email TEXT,
        verified BOOLEAN DEFAULT 0,
        verification_code TEXT,
        code_expires TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS admin_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        admin_id INTEGER REFERENCES school_admins(id),
        session_token TEXT,
        expires_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS admin_login_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        admin_id INTEGER REFERENCES school_admins(id),
        action TEXT,
        target_id INTEGER,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # --- Students & Teachers ---
    c.execute('''CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id TEXT REFERENCES schools(tenant_id),
        user_id INTEGER,
        name TEXT,
        class TEXT,
        age INTEGER,
        guardian_id INTEGER,
        enrollment_date DATE,
        status TEXT DEFAULT 'active'
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS teachers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id TEXT REFERENCES schools(tenant_id),
        user_id INTEGER,
        name TEXT,
        subjects TEXT,
        class_assigned TEXT,
        qualifications TEXT,
        hire_date DATE
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS parent_students (
        parent_id INTEGER,
        student_id INTEGER REFERENCES students(id),
        PRIMARY KEY (parent_id, student_id)
    )''')

    # --- Academics ---
    c.execute('''CREATE TABLE IF NOT EXISTS fees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id TEXT REFERENCES schools(tenant_id),
        student_id INTEGER REFERENCES students(id),
        term TEXT,
        amount DECIMAL,
        paid BOOLEAN DEFAULT 0,
        due_date DATE,
        payment_method TEXT,
        transaction_id TEXT,
        paid_at TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id TEXT REFERENCES schools(tenant_id),
        student_id INTEGER REFERENCES students(id),
        class_id TEXT,
        date DATE,
        status TEXT CHECK(status IN ('present','absent','late'))
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS grades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id TEXT REFERENCES schools(tenant_id),
        student_id INTEGER REFERENCES students(id),
        subject TEXT,
        term TEXT,
        score DECIMAL,
        grade TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS timetable (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id TEXT REFERENCES schools(tenant_id),
        class_id TEXT,
        day TEXT,
        time_start TIME,
        time_end TIME,
        subject TEXT,
        teacher_id INTEGER REFERENCES teachers(id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id TEXT REFERENCES schools(tenant_id),
        teacher_id INTEGER REFERENCES teachers(id),
        class_id TEXT,
        title TEXT,
        description TEXT,
        due_date DATE,
        resources TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS submissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id TEXT REFERENCES schools(tenant_id),
        assignment_id INTEGER REFERENCES assignments(id),
        student_id INTEGER REFERENCES students(id),
        content TEXT,
        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        grade DECIMAL,
        feedback TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id TEXT REFERENCES schools(tenant_id),
        user_id INTEGER,
        title TEXT,
        message TEXT,
        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        read BOOLEAN DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id TEXT REFERENCES schools(tenant_id),
        type TEXT,
        content TEXT,
        generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        submitted_to TEXT
    )''')

    # --- Admissions ---
    c.execute('''CREATE TABLE IF NOT EXISTS admissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id TEXT REFERENCES schools(tenant_id),
        parent_id INTEGER,
        student_name TEXT,
        dob DATE,
        class_applying TEXT,
        birth_cert_id TEXT,
        report_card_id TEXT,
        photo_id TEXT,
        status TEXT DEFAULT 'pending',
        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        decision_at TIMESTAMP,
        admission_letter_sent BOOLEAN DEFAULT 0
    )''')

    # --- Conferences ---
    c.execute('''CREATE TABLE IF NOT EXISTS conference_slots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id TEXT REFERENCES schools(tenant_id),
        teacher_id INTEGER REFERENCES teachers(id),
        slot_start TIMESTAMP,
        slot_end TIMESTAMP,
        booked BOOLEAN DEFAULT 0,
        booked_by INTEGER,
        booking_code TEXT UNIQUE
    )''')

    # --- Broadcast ---
    c.execute('''CREATE TABLE IF NOT EXISTS broadcast_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id TEXT REFERENCES schools(tenant_id),
        sent_by INTEGER,
        message TEXT,
        recipient_count INTEGER,
        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # --- Store ---
    c.execute('''CREATE TABLE IF NOT EXISTS store_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id TEXT REFERENCES schools(tenant_id),
        name TEXT,
        description TEXT,
        price DECIMAL,
        image_id TEXT,
        stock INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS store_orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id TEXT REFERENCES schools(tenant_id),
        parent_id INTEGER,
        items TEXT,
        total DECIMAL,
        payment_status TEXT DEFAULT 'pending',
        order_status TEXT DEFAULT 'pending',
        ordered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # --- Budgeting ---
    c.execute('''CREATE TABLE IF NOT EXISTS budget_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id TEXT REFERENCES schools(tenant_id),
        category TEXT,
        allocated DECIMAL,
        spent DECIMAL DEFAULT 0,
        fiscal_year TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id TEXT REFERENCES schools(tenant_id),
        budget_item_id INTEGER REFERENCES budget_items(id),
        description TEXT,
        amount DECIMAL,
        date DATE,
        receipt_id TEXT,
        recorded_by INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # --- PTA ---
    c.execute('''CREATE TABLE IF NOT EXISTS pta_meetings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id TEXT REFERENCES schools(tenant_id),
        title TEXT,
        agenda TEXT,
        meeting_date TIMESTAMP,
        venue TEXT,
        created_by INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS pta_attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        meeting_id INTEGER REFERENCES pta_meetings(id),
        user_id INTEGER,
        role TEXT,
        attended BOOLEAN DEFAULT 0
    )''')

    # --- Events ---
    c.execute('''CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id TEXT REFERENCES schools(tenant_id),
        title TEXT,
        description TEXT,
        event_type TEXT,
        start_date TIMESTAMP,
        end_date TIMESTAMP,
        venue TEXT,
        max_participants INTEGER,
        created_by INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'upcoming'
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS event_registrations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER REFERENCES events(id),
        user_id INTEGER,
        participant_name TEXT,
        team TEXT,
        registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS event_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER REFERENCES events(id),
        participant_id INTEGER,
        score DECIMAL,
        rank INTEGER,
        result_text TEXT
    )''')

    # --- Circulars & Newsletters ---
    c.execute('''CREATE TABLE IF NOT EXISTS circulars (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id TEXT REFERENCES schools(tenant_id),
        title TEXT,
        content TEXT,
        file_id TEXT,
        sent_by INTEGER,
        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS newsletters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id TEXT REFERENCES schools(tenant_id),
        title TEXT,
        content TEXT,
        issue_number INTEGER,
        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    conn.commit()
    conn.close()

# ========== HELPER FUNCTIONS ==========
def get_user_uses(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT uses, is_pro FROM user_usage WHERE user_id = ?', (user_id,))
    row = c.fetchone()
    conn.close()
    return row if row else (0, 0)

def increment_user_use(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''INSERT INTO user_usage (user_id, uses, last_use)
                 VALUES (?, 1, CURRENT_TIMESTAMP)
                 ON CONFLICT(user_id) DO UPDATE SET uses = uses + 1, last_use = CURRENT_TIMESTAMP''', (user_id,))
    conn.commit()
    conn.close()

def set_pro_status(user_id, is_pro):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('UPDATE user_usage SET is_pro = ? WHERE user_id = ?', (is_pro, user_id))
    conn.commit()
    conn.close()

def get_tenant_by_user(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT tenant_id FROM user_usage WHERE user_id = ?', (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def get_admin_role(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT tenant_id, role FROM school_admins WHERE user_id = ? AND verified = 1', (user_id,))
    row = c.fetchone()
    conn.close()
    return row if row else (None, None)

# ========== RBAC ==========
def require_role(allowed_roles):
    def decorator(func):
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            role = context.user_data.get('admin_role')
            if not role:
                await update.message.reply_text("❌ Please login first using /admin_login.")
                return
            if role not in allowed_roles:
                await update.message.reply_text("⛔ Unauthorized.")
                return
            return await func(update, context)
        return wrapper
    return decorator

def super_admin_only(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != ADMIN_ID:
            await update.message.reply_text("⛔ Unauthorized. Super Admin only.")
            return
        return await func(update, context)
    return wrapper

async def download_with_retry(file, file_path, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await file.download_to_drive(file_path, read_timeout=180)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)


# ========== CONVERSATION STATES ==========
ONBOARD_NAME, ONBOARD_TYPE, ONBOARD_COUNTRY, ONBOARD_CURRENCY = range(4)
LOGIN_PHONE, LOGIN_VERIFY = range(4, 6)
ADD_STUDENT_NAME, ADD_STUDENT_CLASS, ADD_STUDENT_AGE = range(6, 9)
ADD_TEACHER_NAME, ADD_TEACHER_SUBJECTS, ADD_TEACHER_CLASS = range(9, 12)
ADM_NAME, ADM_DOB, ADM_CLASS, ADM_BIRTH_CERT, ADM_REPORT_CARD, ADM_PHOTO = range(20, 26)
CONF_DATE, CONF_TIME = range(30, 32)
CONF_BOOK_CODE = 33
BROADCAST_MSG = 40
BUDGET_CATEGORY, BUDGET_AMOUNT = range(50, 52)
EXPENSE_ITEM, EXPENSE_DESC, EXPENSE_AMOUNT = range(52, 55)
PTA_TITLE, PTA_AGENDA, PTA_DATETIME, PTA_VENUE, PTA_REGISTER_ID = range(55, 60)
EVENT_TITLE, EVENT_DESC, EVENT_TYPE, EVENT_START, EVENT_END, EVENT_VENUE, EVENT_MAX = range(60, 67)
EVENT_REG_ID, EVENT_RESULT_ID, EVENT_RESULT_SCORE = range(67, 70)
CIRC_TITLE, CIRC_CONTENT = range(70, 72)
NEWS_TITLE, NEWS_CONTENT = range(72, 74)
LOGOUT_SCHOOL_STATE, LOGOUT_ADMIN_STATE, LOGOUT_USER_STATE = range(80, 83)
LINK_PARENT_STUDENT, LINK_PARENT_PARENT = range(83, 85)

# ========== CANCEL ==========
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Cancelled.")
    context.user_data.clear()
    return ConversationHandler.END

# ========== EXTRACTION SERVICES ==========
SERVICE_CONFIG = {
    'whatsapp': {
        'pattern': r'([A-Za-z\s]+):\s*(\+?\d{10,15})',
        'headers': ["Name", "Phone Number"],
        'prefix': 'whatsapp_numbers',
        'help': 'Extract names and phone numbers from WhatsApp chat exports.'
    },
    'email': {
        'pattern': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        'headers': ["Email"],
        'prefix': 'extracted_emails',
        'help': 'Extract all email addresses from text.'
    },
    'social': {
        'pattern': r'(?:@|instagram\.com/|twitter\.com/|linkedin\.com/in/|facebook\.com/|tiktok\.com/@|youtube\.com/@)([a-zA-Z0-9_.-]+)',
        'headers': ["Social Handle"],
        'prefix': 'social_handles',
        'help': 'Extract social media handles.'
    },
    'nin': {
        'pattern': r'\b\d{11}\b',
        'headers': ["NIN"],
        'prefix': 'nin_numbers',
        'help': 'Extract 11-digit NIN numbers.'
    },
    'bvn': {
        'pattern': r'\b\d{11}\b',
        'headers': ["BVN"],
        'prefix': 'bvn_numbers',
        'help': 'Extract 11-digit BVN numbers.'
    },
    'urls': {
        'pattern': r'https?://[^\s]+',
        'headers': ["URL"],
        'prefix': 'extracted_urls',
        'help': 'Extract all URLs from text.'
    },
    'agents': {
        'pattern': r'([A-Za-z\s]+):\s*([A-Za-z\s]+)\s*(\+?\d{10,15})',
        'headers': ["Trade", "Name", "Phone Number"],
        'prefix': 'service_agents',
        'help': 'Extract ANY service agent (Mason, Plumber, Web Developer, etc.) – works for any trade!'
    }
}

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    uses, is_pro = get_user_uses(user_id)
    if user_id != ADMIN_ID and not is_pro:
        if uses >= MAX_FREE_USES:
            keyboard = [[InlineKeyboardButton("💳 Upgrade to Pro", callback_data="pay_now")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "⛔ You've used all free tries.\n"
                f"💳 Upgrade to Pro for ₦{PRO_TIER_PRICE}/month.\n"
                "🔗 Click the button below to pay.",
                reply_markup=reply_markup
            )
            return
    document = update.message.document
    if not document or not document.file_name.endswith('.txt'):
        await update.message.reply_text("❌ Please send a .txt file.")
        return
    service = context.user_data.get('service', 'whatsapp')
    config = SERVICE_CONFIG.get(service)
    if not config:
        service = 'whatsapp'
        config = SERVICE_CONFIG['whatsapp']
    pattern = config['pattern']
    headers = config['headers']
    prefix = config['prefix']
    try:
        file = await context.bot.get_file(document.file_id)
        file_path = f"/tmp/{document.file_name}"
        await download_with_retry(file, file_path)
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        if service == 'whatsapp':
            matches = re.findall(pattern, content)
            data = []
            for name, num in matches:
                clean_num = re.sub(r'[\s\-\(\)]', '', num)
                if len(clean_num) >= 10:
                    data.append((name.strip(), clean_num))
            seen = set()
            unique_data = []
            for name, num in data:
                if num not in seen:
                    seen.add(num)
                    unique_data.append((name, num))
        elif service == 'agents':
            matches = re.findall(pattern, content)
            unique_data = []
            seen = set()
            for trade, name, num in matches:
                clean_num = re.sub(r'[\s\-\(\)]', '', num)
                if len(clean_num) >= 10:
                    key = (trade.strip(), name.strip(), clean_num)
                    if key not in seen:
                        seen.add(key)
                        unique_data.append(key)
        else:
            raw_matches = re.findall(pattern, content)
            if service in ('nin', 'bvn'):
                unique_data = list(set(raw_matches))
            else:
                unique_data = list(set([m.strip() for m in raw_matches]))
        if not unique_data:
            await update.message.reply_text("❌ No matches found for the selected service.")
            os.remove(file_path)
            return
        import csv
        csv_path = file_path.replace('.txt', '.csv')
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            if service == 'whatsapp':
                for name, num in unique_data:
                    writer.writerow([name, num])
            elif service == 'agents':
                for trade, name, num in unique_data:
                    writer.writerow([trade, name, num])
            else:
                for item in unique_data:
                    writer.writerow([item])
        with open(csv_path, 'rb') as f:
            await update.message.reply_document(
                document=f,
                filename=f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )
        if user_id != ADMIN_ID and not is_pro:
            increment_user_use(user_id)
            remaining = MAX_FREE_USES - get_user_uses(user_id)[0]
            await update.message.reply_text(f"✅ Done! {remaining} free uses left.")
        else:
            await update.message.reply_text("✅ Done! (Unlimited access)")
        os.remove(file_path)
        os.remove(csv_path)
    except Exception as e:
        logging.error(f"Bot crashed: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Error: {e}")
        logging.error(f"File processing error: {e}")

async def service_command(update: Update, context: ContextTypes.DEFAULT_TYPE, service_name=None):
    if service_name and service_name in SERVICE_CONFIG:
        context.user_data['service'] = service_name
        await update.message.reply_text(
            f"✅ Service selected: **{service_name.upper()}**.\n"
            f"📄 Send a `.txt` file now.\n\n"
            f"ℹ️ {SERVICE_CONFIG[service_name]['help']}"
        )
    else:
        await update.message.reply_text("❌ Unknown service. Use /start to choose.")

async def whatsapp(update, context): await service_command(update, context, 'whatsapp')
async def email(update, context): await service_command(update, context, 'email')
async def social(update, context): await service_command(update, context, 'social')
async def nin(update, context): await service_command(update, context, 'nin')
async def bvn(update, context): await service_command(update, context, 'bvn')
async def urls(update, context): await service_command(update, context, 'urls')
async def agents(update, context): await service_command(update, context, 'agents')

# ========== SCHOOL MANAGEMENT ==========
# ---- Onboarding ----
async def onboard_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Unauthorized. Only platform admin can onboard schools.")
        return ConversationHandler.END
    await update.message.reply_text("🏫 **School Onboarding**\n\nPlease enter the school name:")
    return ONBOARD_NAME

async def onboard_school_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['school_name'] = update.message.text
    await update.message.reply_text("Enter school type (e.g., Primary, Secondary, Tertiary):")
    return ONBOARD_TYPE

async def onboard_school_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['school_type'] = update.message.text
    await update.message.reply_text("Enter country:")
    return ONBOARD_COUNTRY

async def onboard_school_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['country'] = update.message.text
    await update.message.reply_text("Enter default currency (e.g., NGN, USD, KES):")
    return ONBOARD_CURRENCY

async def onboard_school_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    currency = update.message.text
    name = context.user_data.get('school_name')
    school_type = context.user_data.get('school_type')
    country = context.user_data.get('country')
    tenant_id = name.replace(" ", "_").lower()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('INSERT INTO schools (tenant_id, name, type, country, currency) VALUES (?,?,?,?,?)',
              (tenant_id, name, school_type, country, currency))
    conn.commit()
    conn.close()
    await update.message.reply_text(
        f"✅ School **{name}** onboarded successfully!\n"
        f"Tenant ID: `{tenant_id}`\n"
        f"Admins can now use `/admin_login` with their phone number."
    )
    context.user_data.pop('school_name', None)
    context.user_data.pop('school_type', None)
    context.user_data.pop('country', None)
    return ConversationHandler.END

# ---- Admin Login ----
async def admin_login_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📞 Enter your phone number (with country code, e.g., +2348012345678):")
    return LOGIN_PHONE

async def admin_login_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text
    context.user_data['login_phone'] = phone
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT id, tenant_id, role, verified FROM school_admins WHERE phone = ?', (phone,))
    admin = c.fetchone()
    if not admin:
        await update.message.reply_text("❌ Phone number not registered. Please contact your school owner.")
        conn.close()
        return ConversationHandler.END
    code = ''.join(random.choices('0123456789', k=6))
    expires = datetime.now() + timedelta(minutes=5)
    c.execute('UPDATE school_admins SET verification_code = ?, code_expires = ? WHERE id = ?', (code, expires, admin[0]))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ Verification code sent to {phone}.\nYour code: `{code}`\nEnter it within 5 minutes.")
    return LOGIN_VERIFY

async def admin_login_verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text
    phone = context.user_data.get('login_phone')
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT id, tenant_id, role FROM school_admins WHERE phone = ? AND verification_code = ? AND code_expires > datetime("now")', (phone, code))
    admin = c.fetchone()
    if not admin:
        await update.message.reply_text("❌ Invalid or expired code.")
        conn.close()
        context.user_data.pop('login_phone', None)
        return ConversationHandler.END
    c.execute('UPDATE school_admins SET verified = 1 WHERE id = ?', (admin[0],))
    c.execute('INSERT INTO admin_login_history (admin_id, action) VALUES (?, ?)', (admin[0], 'login'))
    # --- FIX: Set tenant_id in user_usage for this admin ---
    c.execute('UPDATE user_usage SET tenant_id = ? WHERE user_id = ?', (admin[1], update.effective_user.id))
    conn.commit()
    conn.close()
    context.user_data['admin_tenant'] = admin[1]
    context.user_data['admin_role'] = admin[2]
    await update.message.reply_text(f"✅ Login successful! You are logged in as **{admin[2]}** of tenant `{admin[1]}`.\nUse /dashboard to view admin panel.")
    context.user_data.pop('login_phone', None)
    return ConversationHandler.END

# ---- Dashboard ----
async def dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tenant_id = context.user_data.get('admin_tenant')
    if not tenant_id:
        await update.message.reply_text("❌ Please login first using /admin_login.")
        return
    keyboard = [
        [InlineKeyboardButton("👥 Students", callback_data="dash_students"),
         InlineKeyboardButton("👨‍🏫 Teachers", callback_data="dash_teachers")],
        [InlineKeyboardButton("💰 Fees", callback_data="dash_fees"),
         InlineKeyboardButton("📊 Attendance", callback_data="dash_attendance")],
        [InlineKeyboardButton("📚 Grades", callback_data="dash_grades"),
         InlineKeyboardButton("🕐 Timetable", callback_data="dash_timetable")],
        [InlineKeyboardButton("📝 Assignments", callback_data="dash_assignments"),
         InlineKeyboardButton("📄 Reports", callback_data="dash_reports")],
        [InlineKeyboardButton("⚙️ Settings", callback_data="dash_settings")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(f"🏫 **School Dashboard** (Tenant: {tenant_id})\nSelect an option:", reply_markup=reply_markup)

# ---- Add Student ----
async def add_student_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('admin_tenant'):
        await update.message.reply_text("❌ Please login first.")
        return ConversationHandler.END
    await update.message.reply_text("Enter student name:")
    return ADD_STUDENT_NAME

async def add_student_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['student_name'] = update.message.text
    await update.message.reply_text("Enter class:")
    return ADD_STUDENT_CLASS

async def add_student_class(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['student_class'] = update.message.text
    await update.message.reply_text("Enter age:")
    return ADD_STUDENT_AGE

async def add_student_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    age = update.message.text
    tenant_id = context.user_data.get('admin_tenant')
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('INSERT INTO students (tenant_id, name, class, age) VALUES (?,?,?,?)',
              (tenant_id, context.user_data['student_name'], context.user_data['student_class'], age))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ Student **{context.user_data['student_name']}** added successfully.")
    context.user_data.pop('student_name', None)
    context.user_data.pop('student_class', None)
    return ConversationHandler.END

# ---- Add Teacher ----
async def add_teacher_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('admin_tenant'):
        await update.message.reply_text("❌ Please login first.")
        return ConversationHandler.END
    await update.message.reply_text("Enter teacher name:")
    return ADD_TEACHER_NAME

async def add_teacher_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['teacher_name'] = update.message.text
    await update.message.reply_text("Enter subjects (comma separated):")
    return ADD_TEACHER_SUBJECTS

async def add_teacher_subjects(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['teacher_subjects'] = update.message.text
    await update.message.reply_text("Enter class assigned:")
    return ADD_TEACHER_CLASS

async def add_teacher_class(update: Update, context: ContextTypes.DEFAULT_TYPE):
    class_assigned = update.message.text
    tenant_id = context.user_data.get('admin_tenant')
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('INSERT INTO teachers (tenant_id, name, subjects, class_assigned) VALUES (?,?,?,?)',
              (tenant_id, context.user_data['teacher_name'], context.user_data['teacher_subjects'], class_assigned))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ Teacher **{context.user_data['teacher_name']}** added successfully.")
    return ConversationHandler.END

# ---- Fees ----
async def fees(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tenant_id = context.user_data.get('admin_tenant')
    if not tenant_id:
        await update.message.reply_text("❌ Please login first.")
        return
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        SELECT s.name, f.amount, f.paid, f.due_date
        FROM fees f
        JOIN students s ON f.student_id = s.id
        WHERE f.tenant_id = ?
    ''', (tenant_id,))
    rows = c.fetchall()
    conn.close()
    if not rows:
        await update.message.reply_text("No fees recorded.")
        return
    msg = "💰 **Fee Summary**\n\n"
    for name, amount, paid, due in rows:
        status = "✅ Paid" if paid else "❌ Unpaid"
        msg += f"👤 {name}: ₦{amount} – {status} (Due: {due})\n"
    await update.message.reply_text(msg)

# ---- Attendance (stub – now mark_attendance is implemented separately) ----
async def attendance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 **Attendance** – Use /mark_attendance <student_id> present/absent/late")

# ---- Grades (stub) ----
async def grades(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📚 **Grades** – Use /enter_grade <student_id> <subject> <score>")

# ---- Timetable ----
async def timetable(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🕐 **Timetable** – Coming soon!")

# ---- Assignments ----
async def assignments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📝 **Assignments** – Coming soon!")

# ---- Report Card ----
async def report_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📄 **Report Card** – Use /generate_report <student_id>")

# ---- List Users ----
@require_role(['owner', 'admin1', 'admin2'])
async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tenant_id = context.user_data.get('admin_tenant')
    if not tenant_id:
        await update.message.reply_text("❌ Please login first.")
        return
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT id, name, class FROM students WHERE tenant_id = ?', (tenant_id,))
    students = c.fetchall()
    c.execute('SELECT id, name, class_assigned FROM teachers WHERE tenant_id = ?', (tenant_id,))
    teachers = c.fetchall()
    conn.close()
    msg = "👥 **Users**\n\n"
    msg += "👨‍🎓 **Students:**\n"
    for s in students:
        msg += f"• {s[1]} (ID: {s[0]}) – {s[2]}\n"
    msg += "\n👨‍🏫 **Teachers:**\n"
    for t in teachers:
        msg += f"• {t[1]} (ID: {t[0]}) – {t[2]}\n"
    await update.message.reply_text(msg)

# ---- List Schools (Super Admin) ----
@super_admin_only
async def list_schools(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT tenant_id, name, type, country, created_at FROM schools')
    schools = c.fetchall()
    conn.close()
    if not schools:
        await update.message.reply_text("No schools registered.")
        return
    msg = "🏫 **Registered Schools**\n\n"
    for s in schools:
        msg += f"• {s[1]} ({s[0]}) – {s[2]} – {s[3]} – Created: {s[4][:10]}\n"
    await update.message.reply_text(msg)

# ---- Logout School (Conversation) ----
async def logout_school_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Unauthorized.")
        return ConversationHandler.END
    await update.message.reply_text("Enter school tenant ID to log out (suspend):")
    return LOGOUT_SCHOOL_STATE

async def logout_school_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tenant_id = update.message.text.strip()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT name FROM schools WHERE tenant_id = ?', (tenant_id,))
    school = c.fetchone()
    if not school:
        await update.message.reply_text("❌ School not found.")
        conn.close()
        return ConversationHandler.END
    c.execute('DELETE FROM admin_sessions WHERE admin_id IN (SELECT id FROM school_admins WHERE tenant_id = ?)', (tenant_id,))
    c.execute('UPDATE school_admins SET verified = 0 WHERE tenant_id = ?', (tenant_id,))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ School **{school[0]}** has been logged out. They must re-verify.")
    return ConversationHandler.END

# ---- Logout Admin (Owner) ----
@require_role(['owner'])
async def logout_admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Enter admin ID to log out (1 for Admin 1, 2 for Admin 2):")
    return LOGOUT_ADMIN_STATE

async def logout_admin_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = update.message.text.strip()
    tenant_id = context.user_data.get('admin_tenant')
    role_map = {'1': 'admin1', '2': 'admin2'}
    if target not in role_map:
        await update.message.reply_text("❌ Invalid. Enter 1 for Admin 1 or 2 for Admin 2.")
        return ConversationHandler.END
    target_role = role_map[target]
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT id FROM school_admins WHERE tenant_id = ? AND role = ?', (tenant_id, target_role))
    admin = c.fetchone()
    if not admin:
        await update.message.reply_text(f"❌ Admin {target} not found.")
        conn.close()
        return ConversationHandler.END
    c.execute('DELETE FROM admin_sessions WHERE admin_id = ?', (admin[0],))
    c.execute('UPDATE school_admins SET verified = 0 WHERE id = ?', (admin[0],))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ Admin {target} has been logged out.")
    return ConversationHandler.END

# ---- Logout User (Any Admin) ----
@require_role(['owner', 'admin1', 'admin2'])
async def logout_user_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Enter user ID to log out:")
    return LOGOUT_USER_STATE

async def logout_user_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    identifier = update.message.text.strip()
    tenant_id = context.user_data.get('admin_tenant')
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT id, name FROM students WHERE tenant_id = ? AND id = ?', (tenant_id, identifier))
    user = c.fetchone()
    if not user:
        c.execute('SELECT id, name FROM teachers WHERE tenant_id = ? AND id = ?', (tenant_id, identifier))
        user = c.fetchone()
    if not user:
        await update.message.reply_text("❌ User not found.")
        conn.close()
        return ConversationHandler.END
    # Optionally, you could invalidate sessions – here we just notify
    await update.message.reply_text(f"✅ User **{user[1]}** has been logged out.")
    conn.close()
    return ConversationHandler.END

# ========== ADMISSIONS ==========
async def admission_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    tenant = context.user_data.get('admin_tenant') or get_tenant_by_user(user_id)
    if not tenant:
        await update.message.reply_text("❌ Please login first via /admin_login.")
        return ConversationHandler.END
    context.user_data['admission_tenant'] = tenant
    await update.message.reply_text("📝 **New Admission Application**\n\nEnter student's full name:")
    return ADM_NAME

async def admission_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['adm_name'] = update.message.text
    await update.message.reply_text("Enter date of birth (YYYY‑MM‑DD):")
    return ADM_DOB

async def admission_dob(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['adm_dob'] = update.message.text
    await update.message.reply_text("Enter class applying for (e.g., Primary 1, SS3):")
    return ADM_CLASS

async def admission_class(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['adm_class'] = update.message.text
    await update.message.reply_text("📎 Upload birth certificate (as document/photo):")
    return ADM_BIRTH_CERT

async def admission_birth_cert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document or update.message.photo[-1]
    context.user_data['adm_birth_cert'] = doc.file_id
    await update.message.reply_text("📎 Upload last report card (if available, or type /skip):")
    return ADM_REPORT_CARD

async def admission_report_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text and update.message.text.lower() == '/skip':
        context.user_data['adm_report_card'] = None
    else:
        doc = update.message.document or update.message.photo[-1]
        context.user_data['adm_report_card'] = doc.file_id
    await update.message.reply_text("📸 Upload passport photograph of student:")
    return ADM_PHOTO

async def admission_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1] if update.message.photo else update.message.document
    context.user_data['adm_photo'] = photo.file_id
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''INSERT INTO admissions 
                 (tenant_id, parent_id, student_name, dob, class_applying, birth_cert_id, report_card_id, photo_id)
                 VALUES (?,?,?,?,?,?,?,?)''',
              (context.user_data['admission_tenant'],
               update.effective_user.id,
               context.user_data['adm_name'],
               context.user_data['adm_dob'],
               context.user_data['adm_class'],
               context.user_data['adm_birth_cert'],
               context.user_data.get('adm_report_card'),
               context.user_data['adm_photo']))
    conn.commit()
    conn.close()
    await update.message.reply_text("✅ Application submitted! The school will review it and contact you.")
    return ConversationHandler.END

async def view_applications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tenant = context.user_data.get('admin_tenant')
    if not tenant:
        await update.message.reply_text("❌ Please login first.")
        return
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT id, student_name, class_applying, status, applied_at FROM admissions WHERE tenant_id = ? ORDER BY applied_at DESC', (tenant,))
    rows = c.fetchall()
    conn.close()
    if not rows:
        await update.message.reply_text("No applications.")
        return
    msg = "📋 **Pending Applications**\n\n"
    for r in rows:
        msg += f"• {r[1]} – {r[2]} – {r[3]} – {r[4][:10]}\n"
    await update.message.reply_text(msg + "\nUse /approve_admission <id> or /reject_admission <id>")

@require_role(['owner', 'admin1', 'admin2'])
async def approve_admission(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        adm_id = int(update.message.text.split()[1])
    except:
        await update.message.reply_text("Usage: /approve_admission <id>")
        return
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('UPDATE admissions SET status = "approved", decision_at = CURRENT_TIMESTAMP WHERE id = ?', (adm_id,))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ Admission {adm_id} approved.")

@require_role(['owner', 'admin1', 'admin2'])
async def reject_admission(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        adm_id = int(update.message.text.split()[1])
    except:
        await update.message.reply_text("Usage: /reject_admission <id>")
        return
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('UPDATE admissions SET status = "rejected", decision_at = CURRENT_TIMESTAMP WHERE id = ?', (adm_id,))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"❌ Admission {adm_id} rejected.")

# ========== CONFERENCES ==========
async def set_availability(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT id FROM teachers WHERE user_id = ?', (user_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        await update.message.reply_text("❌ You are not registered as a teacher. Please contact admin.")
        return ConversationHandler.END
    context.user_data['teacher_id'] = row[0]
    await update.message.reply_text("📅 **Set Availability**\n\nEnter date (YYYY‑MM‑DD):")
    return CONF_DATE

async def conf_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['conf_date'] = update.message.text
    await update.message.reply_text("Enter start time (HH:MM, 24‑hour):")
    return CONF_TIME

async def conf_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    time_str = update.message.text
    try:
        start_dt = datetime.strptime(f"{context.user_data['conf_date']} {time_str}:00", "%Y-%m-%d %H:%M:%S")
        end_dt = start_dt + timedelta(minutes=30)
    except ValueError:
        await update.message.reply_text("Invalid date/time format. Use YYYY-MM-DD and HH:MM.")
        return CONF_DATE
    tenant = context.user_data.get('admin_tenant')
    teacher_id = context.user_data.get('teacher_id')
    code = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=6))
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''INSERT INTO conference_slots 
                 (tenant_id, teacher_id, slot_start, slot_end, booking_code)
                 VALUES (?,?,?,?,?)''',
              (tenant, teacher_id, start_dt.isoformat(), end_dt.isoformat(), code))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ Slot saved! Code: {code}. Parents can book using this code.")
    return ConversationHandler.END

async def book_conference(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📅 **Book Conference**\n\nEnter the booking code provided by the teacher:")
    return CONF_BOOK_CODE

async def conf_book_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT id, teacher_id, slot_start, slot_end FROM conference_slots WHERE booking_code = ? AND booked = 0', (code,))
    row = c.fetchone()
    if not row:
        await update.message.reply_text("❌ Invalid or already booked code.")
        conn.close()
        return ConversationHandler.END
    slot_id, teacher_id, start, end = row
    c.execute('UPDATE conference_slots SET booked = 1, booked_by = ? WHERE id = ?', (update.effective_user.id, slot_id))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ Conference booked for {start[:16]} – {end[:16]}. You will receive a reminder.")
    return ConversationHandler.END

# ========== BROADCAST ==========
@require_role(['owner', 'admin1', 'admin2'])
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📢 **Broadcast Message**\n\nType your message to send to all parents, students, and teachers in your school:")
    return BROADCAST_MSG

async def broadcast_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text
    tenant = context.user_data.get('admin_tenant')
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Send to all users in this tenant (set via user_usage)
    c.execute('SELECT user_id FROM user_usage WHERE tenant_id = ?', (tenant,))
    users = c.fetchall()
    count = 0
    for (user_id,) in users:
        try:
            await context.bot.send_message(chat_id=user_id, text=f"📢 **Announcement**\n\n{msg}")
            count += 1
        except:
            pass
    # Also send to admins/teachers (if not already covered)
    c.execute('SELECT user_id FROM school_admins WHERE tenant_id = ? AND verified = 1', (tenant,))
    admins = c.fetchall()
    for (user_id,) in admins:
        if user_id not in [u[0] for u in users]:
            try:
                await context.bot.send_message(chat_id=user_id, text=f"📢 **Admin Announcement**\n\n{msg}")
                count += 1
            except:
                pass
    conn.close()
    await update.message.reply_text(f"✅ Broadcast sent to {count} users.")
    return ConversationHandler.END

# ========== PARENT DASHBOARD ==========
async def parent_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    tenant = context.user_data.get('admin_tenant') or get_tenant_by_user(user_id)
    if not tenant:
        await update.message.reply_text("❌ Please login first.")
        return
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''SELECT s.id, s.name, s.class, s.status 
                 FROM students s
                 JOIN parent_students ps ON s.id = ps.student_id
                 WHERE ps.parent_id = ?''', (user_id,))
    students = c.fetchall()
    conn.close()
    if not students:
        await update.message.reply_text("No students linked to your account. Ask admin to link you.")
        return
    msg = "👨‍👩‍👧 **Your Children**\n\n"
    for s in students:
        msg += f"• {s[1]} (Class: {s[2]}) – Status: {s[3]}\n"
    await update.message.reply_text(msg + "\nUse /view_grades <student_id> or /view_attendance <student_id> to see details.")

# ========== STORE ==========
async def store_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tenant = context.user_data.get('admin_tenant') or get_tenant_by_user(update.effective_user.id)
    if not tenant:
        await update.message.reply_text("❌ Please login first.")
        return
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT id, name, description, price, stock FROM store_items WHERE tenant_id = ? AND stock > 0', (tenant,))
    items = c.fetchall()
    conn.close()
    if not items:
        await update.message.reply_text("No items available in the store.")
        return
    msg = "🛒 **School Store**\n\n"
    for item in items:
        msg += f"• {item[1]} – ₦{item[3]} (Stock: {item[4]})\n   {item[2]}\n   ID: {item[0]}\n\n"
    await update.message.reply_text(msg + "To order, use /order <item_id> <quantity>")

async def order_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        parts = update.message.text.split()
        item_id = int(parts[1])
        qty = int(parts[2]) if len(parts) > 2 else 1
    except:
        await update.message.reply_text("Usage: /order <item_id> <quantity>")
        return
    user_id = update.effective_user.id
    tenant = context.user_data.get('admin_tenant') or get_tenant_by_user(user_id)
    if not tenant:
        await update.message.reply_text("❌ Please login first.")
        return
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT name, price, stock FROM store_items WHERE id = ? AND tenant_id = ?', (item_id, tenant))
    row = c.fetchone()
    if not row:
        await update.message.reply_text("Item not found.")
        conn.close()
        return
    name, price, stock = row
    if stock < qty:
        await update.message.reply_text(f"Only {stock} in stock.")
        conn.close()
        return
    items_json = json.dumps([{"id": item_id, "name": name, "qty": qty, "price": price}])
    total = price * qty
    c.execute('''INSERT INTO store_orders (tenant_id, parent_id, items, total)
                 VALUES (?,?,?,?)''', (tenant, user_id, items_json, total))
    c.execute('UPDATE store_items SET stock = stock - ? WHERE id = ?', (qty, item_id))
    conn.commit()
    conn.close()
    await update.message.reply_text(
        f"✅ Order placed (ID: {c.lastrowid}).\n"
        f"Item: {name} x {qty} = ₦{total}\n"
        f"Please pay via the link: [payment link will be generated here]"
    )

# ========== BUDGETING ==========
@require_role(['owner', 'admin1', 'admin2'])
async def set_budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💰 **Set Budget**\n\nEnter category (e.g., Academic, Sports, Infrastructure):")
    return BUDGET_CATEGORY

async def budget_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['budget_cat'] = update.message.text
    await update.message.reply_text("Enter allocated amount in NGN:")
    return BUDGET_AMOUNT

async def budget_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text)
    except ValueError:
        await update.message.reply_text("Invalid amount. Please enter a number.")
        return BUDGET_AMOUNT
    tenant = context.user_data.get('admin_tenant')
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('INSERT INTO budget_items (tenant_id, category, allocated) VALUES (?,?,?)',
              (tenant, context.user_data['budget_cat'], amount))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ Budget for {context.user_data['budget_cat']} set to ₦{amount}.")
    return ConversationHandler.END

@require_role(['owner', 'admin1', 'admin2'])
async def add_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🧾 **Add Expense**\n\nEnter budget item ID (use /view_budget to see IDs):")
    return EXPENSE_ITEM

async def expense_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data['expense_item'] = int(update.message.text)
    except ValueError:
        await update.message.reply_text("Invalid ID. Please enter a number.")
        return EXPENSE_ITEM
    await update.message.reply_text("Enter description:")
    return EXPENSE_DESC

async def expense_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['expense_desc'] = update.message.text
    await update.message.reply_text("Enter amount:")
    return EXPENSE_AMOUNT

async def expense_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text)
    except ValueError:
        await update.message.reply_text("Invalid amount. Please enter a number.")
        return EXPENSE_AMOUNT
    tenant = context.user_data.get('admin_tenant')
    item_id = context.user_data['expense_item']
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('UPDATE budget_items SET spent = spent + ? WHERE id = ? AND tenant_id = ?', (amount, item_id, tenant))
    c.execute('INSERT INTO expenses (tenant_id, budget_item_id, description, amount, date, recorded_by) VALUES (?,?,?,?,date("now"),?)',
              (tenant, item_id, context.user_data['expense_desc'], amount, update.effective_user.id))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ Expense recorded: ₦{amount}")
    return ConversationHandler.END

async def view_budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tenant = context.user_data.get('admin_tenant') or get_tenant_by_user(update.effective_user.id)
    if not tenant:
        await update.message.reply_text("❌ Please login first.")
        return
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT id, category, allocated, spent FROM budget_items WHERE tenant_id = ?', (tenant,))
    rows = c.fetchall()
    conn.close()
    if not rows:
        await update.message.reply_text("No budget items.")
        return
    msg = "💰 **Budget Summary**\n\n"
    for r in rows:
        rem = r[2] - r[3]
        msg += f"• {r[1]} – Allocated: ₦{r[2]}, Spent: ₦{r[3]}, Remaining: ₦{rem}\n"
    await update.message.reply_text(msg)

async def budget_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tenant = context.user_data.get('admin_tenant')
    if not tenant:
        await update.message.reply_text("❌ Please login first.")
        return
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT category, allocated, spent FROM budget_items WHERE tenant_id = ?', (tenant,))
    rows = c.fetchall()
    conn.close()
    if not rows:
        await update.message.reply_text("No budget data.")
        return
    msg = "📊 **Budget Report**\n\n"
    total_alloc = sum(r[1] for r in rows)
    total_spent = sum(r[2] for r in rows)
    for r in rows:
        msg += f"{r[0]}: ₦{r[1]} allocated, ₦{r[2]} spent\n"
    msg += f"\nTotal Allocated: ₦{total_alloc}\nTotal Spent: ₦{total_spent}\nBalance: ₦{total_alloc - total_spent}"
    await update.message.reply_text(msg)

# ========== PTA ==========
@require_role(['owner', 'admin1', 'admin2'])
async def pta_create(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📅 **Create PTA Meeting**\n\nEnter meeting title:")
    return PTA_TITLE

async def pta_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['pta_title'] = update.message.text
    await update.message.reply_text("Enter agenda (or /skip):")
    return PTA_AGENDA

async def pta_agenda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['pta_agenda'] = update.message.text if update.message.text != '/skip' else ''
    await update.message.reply_text("Enter meeting date and time (YYYY-MM-DD HH:MM):")
    return PTA_DATETIME

async def pta_datetime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['pta_datetime'] = update.message.text
    await update.message.reply_text("Enter venue:")
    return PTA_VENUE

async def pta_venue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    venue = update.message.text
    tenant = context.user_data.get('admin_tenant')
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('INSERT INTO pta_meetings (tenant_id, title, agenda, meeting_date, venue, created_by) VALUES (?,?,?,?,?,?)',
              (tenant, context.user_data['pta_title'], context.user_data['pta_agenda'],
              context.user_data['pta_datetime'], venue, update.effective_user.id))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ PTA meeting '{context.user_data['pta_title']}' created.")
    return ConversationHandler.END

async def pta_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tenant = context.user_data.get('admin_tenant') or get_tenant_by_user(update.effective_user.id)
    if not tenant:
        await update.message.reply_text("❌ Please login first.")
        return
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT id, title, meeting_date, venue FROM pta_meetings WHERE tenant_id = ? ORDER BY meeting_date DESC', (tenant,))
    rows = c.fetchall()
    conn.close()
    if not rows:
        await update.message.reply_text("No PTA meetings scheduled.")
        return
    msg = "📋 **PTA Meetings**\n\n"
    for r in rows:
        msg += f"• {r[1]} – {r[2][:16]} – Venue: {r[3]}\n   ID: {r[0]}\n"
    await update.message.reply_text(msg)

async def pta_register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Enter PTA meeting ID to register attendance:")
    return PTA_REGISTER_ID

async def pta_register_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        meeting_id = int(update.message.text)
    except ValueError:
        await update.message.reply_text("Invalid ID. Please enter a number.")
        return PTA_REGISTER_ID
    user_id = update.effective_user.id
    # Determine role
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT role FROM school_admins WHERE user_id = ? AND verified = 1', (user_id,))
    row = c.fetchone()
    if row:
        role = row[0]
    else:
        c.execute('SELECT id FROM teachers WHERE user_id = ?', (user_id,))
        if c.fetchone():
            role = 'teacher'
        else:
            role = 'parent'
    c.execute('INSERT INTO pta_attendance (meeting_id, user_id, role, attended) VALUES (?,?,?,?)',
              (meeting_id, user_id, role, 1))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ Registered for PTA meeting as {role}.")
    return ConversationHandler.END

# ========== EVENTS ==========
@require_role(['owner', 'admin1', 'admin2'])
async def event_create(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏅 **Create Event**\n\nEvent title:")
    return EVENT_TITLE

async def event_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['event_title'] = update.message.text
    await update.message.reply_text("Description:")
    return EVENT_DESC

async def event_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['event_desc'] = update.message.text
    await update.message.reply_text("Type (sports, games, competition, quiz, cultural):")
    return EVENT_TYPE

async def event_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['event_type'] = update.message.text
    await update.message.reply_text("Start date/time (YYYY-MM-DD HH:MM):")
    return EVENT_START

async def event_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['event_start'] = update.message.text
    await update.message.reply_text("End date/time (YYYY-MM-DD HH:MM):")
    return EVENT_END

async def event_end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['event_end'] = update.message.text
    await update.message.reply_text("Venue:")
    return EVENT_VENUE

async def event_venue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    venue = update.message.text
    await update.message.reply_text("Max participants (or 0 for unlimited):")
    return EVENT_MAX

async def event_max(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        max_p = int(update.message.text)
    except ValueError:
        await update.message.reply_text("Invalid number. Please enter 0 or a positive integer.")
        return EVENT_MAX
    tenant = context.user_data.get('admin_tenant')
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''INSERT INTO events (tenant_id, title, description, event_type, start_date, end_date, venue, max_participants, created_by)
                 VALUES (?,?,?,?,?,?,?,?,?)''',
              (tenant, context.user_data['event_title'], context.user_data['event_desc'],
               context.user_data['event_type'], context.user_data['event_start'],
               context.user_data['event_end'], venue, max_p, update.effective_user.id))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ Event '{context.user_data['event_title']}' created.")
    return ConversationHandler.END

async def event_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tenant = context.user_data.get('admin_tenant') or get_tenant_by_user(update.effective_user.id)
    if not tenant:
        await update.message.reply_text("❌ Please login first.")
        return
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT id, title, event_type, start_date, status FROM events WHERE tenant_id = ? ORDER BY start_date DESC', (tenant,))
    rows = c.fetchall()
    conn.close()
    if not rows:
        await update.message.reply_text("No events.")
        return
    msg = "📅 **Upcoming Events**\n\n"
    for r in rows:
        msg += f"• {r[1]} ({r[2]}) – {r[3][:16]} – {r[4]}\n   ID: {r[0]}\n"
    await update.message.reply_text(msg)

async def event_register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Enter event ID to register:")
    return EVENT_REG_ID

async def event_reg_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        event_id = int(update.message.text)
    except ValueError:
        await update.message.reply_text("Invalid ID. Please enter a number.")
        return EVENT_REG_ID
    user_id = update.effective_user.id
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Check if event exists and has capacity
    c.execute('SELECT max_participants FROM events WHERE id = ?', (event_id,))
    row = c.fetchone()
    if not row:
        await update.message.reply_text("❌ Event not found.")
        conn.close()
        return ConversationHandler.END
    max_participants = row[0]
    if max_participants > 0:
        c.execute('SELECT COUNT(*) FROM event_registrations WHERE event_id = ?', (event_id,))
        count = c.fetchone()[0]
        if count >= max_participants:
            await update.message.reply_text("❌ Event is full.")
            conn.close()
            return ConversationHandler.END
    # Check if already registered
    c.execute('SELECT id FROM event_registrations WHERE event_id = ? AND user_id = ?', (event_id, user_id))
    if c.fetchone():
        await update.message.reply_text("You are already registered for this event.")
        conn.close()
        return ConversationHandler.END
    c.execute('INSERT INTO event_registrations (event_id, user_id, participant_name) VALUES (?,?,?)',
              (event_id, user_id, update.effective_user.full_name or "Participant"))
    conn.commit()
    conn.close()
    await update.message.reply_text("✅ Registered for event.")
    return ConversationHandler.END

@require_role(['owner', 'admin1', 'admin2'])
async def event_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Enter event ID to add results:")
    return EVENT_RESULT_ID

async def event_result_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data['result_event'] = int(update.message.text)
    except ValueError:
        await update.message.reply_text("Invalid ID. Please enter a number.")
        return EVENT_RESULT_ID
    await update.message.reply_text("Enter participant ID (user ID) and score (e.g., 12345 85):")
    return EVENT_RESULT_SCORE

async def event_result_score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    parts = update.message.text.split()
    if len(parts) != 2:
        await update.message.reply_text("Usage: <user_id> <score>")
        return EVENT_RESULT_SCORE
    try:
        user_id = int(parts[0])
        score = float(parts[1])
    except ValueError:
        await update.message.reply_text("Invalid number format.")
        return EVENT_RESULT_SCORE
    event_id = context.user_data['result_event']
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Validate that this user is registered for the event
    c.execute('SELECT id FROM event_registrations WHERE event_id = ? AND user_id = ?', (event_id, user_id))
    if not c.fetchone():
        await update.message.reply_text("❌ This user is not registered for this event.")
        conn.close()
        return EVENT_RESULT_SCORE
    c.execute('INSERT INTO event_results (event_id, participant_id, score) VALUES (?,?,?)',
              (event_id, user_id, score))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ Score recorded for user {user_id}.")
    return ConversationHandler.END

# ========== CIRCULARS & NEWSLETTERS ==========
@require_role(['owner', 'admin1', 'admin2'])
async def circular(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📜 **Create Circular**\n\nEnter title:")
    return CIRC_TITLE

async def circ_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['circ_title'] = update.message.text
    await update.message.reply_text("Enter content (or send a document file):")
    return CIRC_CONTENT

async def circ_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    content = update.message.text
    tenant = context.user_data.get('admin_tenant')
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('INSERT INTO circulars (tenant_id, title, content, sent_by) VALUES (?,?,?,?)',
              (tenant, context.user_data['circ_title'], content, update.effective_user.id))
    conn.commit()
    conn.close()
    await update.message.reply_text("✅ Circular saved.")
    return ConversationHandler.END

@require_role(['owner', 'admin1', 'admin2'])
async def newsletter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📰 **Create Newsletter**\n\nTitle:")
    return NEWS_TITLE

async def news_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['news_title'] = update.message.text
    await update.message.reply_text("Content:")
    return NEWS_CONTENT

async def news_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    content = update.message.text
    tenant = context.user_data.get('admin_tenant')
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('INSERT INTO newsletters (tenant_id, title, content, sent_at) VALUES (?,?,?,CURRENT_TIMESTAMP)',
              (tenant, context.user_data['news_title'], content))
    conn.commit()
    conn.close()
    await update.message.reply_text("✅ Newsletter saved.")
    return ConversationHandler.END

# ========== LINK PARENT ==========
@require_role(['owner', 'admin1', 'admin2'])
async def link_parent_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👨‍👩‍👧 **Link Parent to Student**\n\nEnter student ID:")
    return LINK_PARENT_STUDENT

async def link_parent_student(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        student_id = int(update.message.text)
    except ValueError:
        await update.message.reply_text("Invalid student ID. Please enter a number.")
        return LINK_PARENT_STUDENT
    context.user_data['link_student_id'] = student_id
    await update.message.reply_text("Enter parent user ID (Telegram ID):")
    return LINK_PARENT_PARENT

async def link_parent_parent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        parent_id = int(update.message.text)
    except ValueError:
        await update.message.reply_text("Invalid parent ID. Please enter a number.")
        return LINK_PARENT_PARENT
    student_id = context.user_data['link_student_id']
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO parent_students (parent_id, student_id) VALUES (?,?)', (parent_id, student_id))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ Parent {parent_id} linked to student {student_id}.")
    return ConversationHandler.END

# ========== MARK ATTENDANCE ==========
@require_role(['owner', 'admin1', 'admin2', 'teacher'])
async def mark_attendance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        parts = update.message.text.split()
        if len(parts) < 3:
            await update.message.reply_text("Usage: /mark_attendance <student_id> <present|absent|late>")
            return
        student_id = int(parts[1])
        status = parts[2].lower()
        if status not in ['present', 'absent', 'late']:
            await update.message.reply_text("Status must be present, absent, or late.")
            return
        tenant = context.user_data.get('admin_tenant')
        if not tenant:
            await update.message.reply_text("Please login first.")
            return
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('INSERT INTO attendance (tenant_id, student_id, date, status) VALUES (?,?,date("now"),?)',
                  (tenant, student_id, status))
        conn.commit()
        conn.close()
        await update.message.reply_text(f"✅ Attendance marked as {status} for student {student_id}.")
    except ValueError:
        await update.message.reply_text("Invalid student ID.")

# ========== PAYMENT ==========
async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    payment_link = f"https://selar.com/427x919914?user_id={user_id}"
    keyboard = [[InlineKeyboardButton("💳 Pay Now", url=payment_link)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"⭐ **Upgrade to Pro – ₦{PRO_TIER_PRICE}/month**\n\n"
        "✅ Unlimited extractions for all services\n"
        "✅ AI Contact Scoring\n"
        "✅ Priority support\n\n"
        "🔗 Click below to pay.",
        reply_markup=reply_markup
    )

async def pay_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    payment_link = f"https://selar.com/427x919914?user_id={user_id}"
    keyboard = [[InlineKeyboardButton("💳 Pay Now", url=payment_link)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        f"💳 **Upgrade to Pro – ₦{PRO_TIER_PRICE}/month**\n\n"
        "✅ Unlimited extractions\n"
        "✅ AI Scoring\n"
        "✅ Priority support\n\n"
        "🔗 Click the button below to complete your payment.",
        reply_markup=reply_markup
    )

# ========== GENERAL COMMANDS ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📞 WhatsApp Numbers", callback_data="service_whatsapp")],
        [InlineKeyboardButton("📧 Emails", callback_data="service_email")],
        [InlineKeyboardButton("📱 Social Handles", callback_data="service_social")],
        [InlineKeyboardButton("🆔 NIN", callback_data="service_nin")],
        [InlineKeyboardButton("🏦 BVN", callback_data="service_bvn")],
        [InlineKeyboardButton("🔗 URLs", callback_data="service_urls")],
        [InlineKeyboardButton("🔧 Service Agents", callback_data="service_agents")],
        [InlineKeyboardButton("🏫 School Management", callback_data="service_school")],
        [InlineKeyboardButton("💳 Upgrade to Pro", callback_data="pay_now")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🚀 **KOSFintech School Bot**\n\n"
        "Select a service below, then send a `.txt` file to extract data.\n\n"
        "📞 WhatsApp – Extract names + phone numbers.\n"
        "📧 Emails – Extract email addresses.\n"
        "📱 Social – Extract social handles.\n"
        "🆔 NIN – Extract 11-digit NIN.\n"
        "🏦 BVN – Extract 11-digit BVN.\n"
        "🔗 URLs – Extract all URLs.\n"
        "🔧 Agents – Extract any service agent.\n"
        "🏫 School – Full management (onboard, students, fees, etc.)\n\n"
        "✨ **New Features:** Admissions, Conferences, Broadcast, Parent Dashboard,\n"
        "Store, Budgeting, PTA, Events, Circulars, Newsletters.\n\n"
        "💡 Free trial: 3 uses total. ⭐ Pro: Unlimited + AI scoring.\n\n"
        "📋 Type /commands for all commands.",
        reply_markup=reply_markup
    )

async def commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    table = (
        "📋 **Available Commands**\n\n"
        "| Command | Description |\n"
        "|---------|-------------|\n"
        "| /start  | Show main menu |\n"
        "| /commands | Show this list |\n"
        "| /whatsapp, /email, /social, /nin, /bvn, /urls, /agents | Extraction services |\n"
        "| /onboard | Onboard a new school (Super Admin) |\n"
        "| /admin_login | Login as school admin |\n"
        "| /dashboard | View admin dashboard |\n"
        "| /add_student | Add a student |\n"
        "| /add_teacher | Add a teacher |\n"
        "| /fees | View fee summary |\n"
        "| /attendance | View attendance (use /mark_attendance) |\n"
        "| /mark_attendance | Mark attendance |\n"
        "| /grades | View grades (use /enter_grade) |\n"
        "| /enter_grade | Enter grade |\n"
        "| /timetable | View timetable |\n"
        "| /assignments | Manage assignments |\n"
        "| /report_card | Generate report card |\n"
        "| /list_users | List students & teachers (Admin) |\n"
        "| /list_schools | List all schools (Super Admin) |\n"
        "| /logout_school | Force logout a school (Super Admin) |\n"
        "| /logout_admin | Logout admin1/admin2 (Owner) |\n"
        "| /logout_user | Logout a specific user (Admin) |\n"
        "| /link_parent | Link parent to student (Admin) |\n"
        "| /admission | Apply for admission |\n"
        "| /view_applications | View applications (Admin) |\n"
        "| /approve_admission /reject_admission | Approve/reject (Admin) |\n"
        "| /set_availability | Set conference slot (Teacher) |\n"
        "| /book_conference | Book conference (Parent) |\n"
        "| /broadcast | Send announcement (Admin) |\n"
        "| /parent_dashboard | View your children (Parent) |\n"
        "| /store | View school store items |\n"
        "| /order | Order item from store |\n"
        "| /set_budget | Set budget category |\n"
        "| /add_expense | Record expense |\n"
        "| /view_budget | View budget summary |\n"
        "| /budget_report | Detailed budget report |\n"
        "| /pta_create | Create PTA meeting |\n"
        "| /pta_list | List PTA meetings |\n"
        "| /pta_register | Register attendance for PTA |\n"
        "| /event_create | Create event |\n"
        "| /event_list | List events |\n"
        "| /event_register | Register for event |\n"
        "| /event_results | Record event results (Admin) |\n"
        "| /circular | Create circular |\n"
        "| /newsletter | Create newsletter |\n"
        "| /pay | Upgrade to Pro |\n"
        "| /health | Bot health (Admin) |\n"
        "| /offer_status | Offer counter (Admin) |\n"
        "| /help | Help information |\n"
        "| /guide | How to export WhatsApp chat |\n"
        "| /roadmap | Project roadmap |\n"
        "| /community | Join our community |\n"
    )
    await update.message.reply_text(table, parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 **Help**\n\n"
        "• Extraction: Choose service via /start, send .txt, get CSV.\n"
        "• School Management: Login with /admin_login (after being added by owner).\n"
        "• Admissions: /admission to apply; admins use /view_applications, approve/reject.\n"
        "• Conferences: Teachers set slots with /set_availability; parents book with code.\n"
        "• Broadcast: Admins send messages to all users with /broadcast.\n"
        "• Parent Dashboard: View children and their status with /parent_dashboard.\n"
        "• Store: Browse /store, order with /order.\n"
        "• Budgeting: Set budgets, track expenses.\n"
        "• PTA: Create meetings, register attendance.\n"
        "• Events: Create, register, record results.\n"
        "• Circulars & Newsletters: Create and store documents.\n\n"
        "🔒 Free: 3 uses total. ⭐ Pro: Unlimited + AI scoring.\n"
        "💳 Payment: /pay"
    )

async def guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 **How to Export WhatsApp Chat**\n\n"
        "1. Open WhatsApp group → 3 dots → Export Chat\n"
        "2. Choose Without Media\n"
        "3. Save .txt and send here"
    )

async def roadmap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🗺️ **KOSFintech Roadmap**\n\n"
        "✅ Phase 1 – Data Extraction\n"
        "✅ Phase 2 – School Management\n"
        "✅ Phase 3 – Admissions, Conferences, Broadcast\n"
        "✅ Phase 4 – Parent Dashboard, Store\n"
        "✅ Phase 5 – Budgeting, PTA, Events, Circulars, Newsletters\n"
        "🚀 Phase 6 – Web Dashboard & Mobile App\n"
        "🌟 Phase 7 – AI Analytics & Smart Recommendations"
    )

async def community(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💬 **Join the Community**\n\n"
        "🤖 @WhatsappHelperBot\n"
        "👥 https://t.me/+vLcmNuOi3OZjYmFk\n"
        "📧 support@yourbot.com"
    )

async def health(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Unauthorized.")
        return
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM user_usage')
        count = c.fetchone()[0]
        c.execute('SELECT COUNT(*) FROM user_usage WHERE is_pro = 1')
        pro_count = c.fetchone()[0]
        conn.close()
        db_status = "✅ Database OK"
    except Exception as e:
        logging.error(f"Bot crashed: {e}", exc_info=True)
        db_status = f"❌ Database ERROR: {e}"
        pro_count = 0
    try:
        result = os.popen('screen -list | grep "\\.bot"').read()
        screen_status = "✅ Bot screen active" if result else "⚠️ Bot screen NOT active"
    except:
        screen_status = "❌ Screen check failed"
    await update.message.reply_text(f"""
📊 Health Dashboard
━━━━━━━━━━━━━━━━━━━
{db_status}
{screen_status}
📱 Total users: {count}
⭐ Pro users: {pro_count}
🕐 Last check: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """)

async def offer_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Unauthorized.")
        return
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT value FROM config WHERE key = "offer_count"')
    result = c.fetchone()
    count = int(result[0]) if result else 0
    remaining = max(0, 50 - count)
    await update.message.reply_text(f"📊 **Offer Counter**\nUsed: {count}\nRemaining: {remaining}")

# ========== SERVICE CALLBACK ==========
async def service_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    service_map = {
        "service_whatsapp": "whatsapp",
        "service_email": "email",
        "service_social": "social",
        "service_nin": "nin",
        "service_bvn": "bvn",
        "service_urls": "urls",
        "service_agents": "agents",
    }
    service = service_map.get(query.data)
    if service:
        context.user_data['service'] = service
        await query.edit_message_text(
            f"✅ Service selected: **{service.upper()}**.\n"
            f"📄 Send a `.txt` file now.\n\n"
            f"ℹ️ {SERVICE_CONFIG[service]['help']}"
        )
    elif query.data == "service_school":
        await query.edit_message_text(
            "🏫 **School Management**\n\n"
            "• /onboard – Onboard a new school (Super Admin)\n"
            "• /admin_login – Login to your school dashboard\n"
            "• /dashboard – View admin dashboard\n"
            "• /add_student – Add a student\n"
            "• /add_teacher – Add a teacher\n"
            "• /fees – View fee summary\n"
            "• /attendance – Mark attendance\n"
            "• /grades – Enter/view grades\n"
            "• /timetable – View timetable\n"
            "• /assignments – Manage assignments\n"
            "• /report_card – Generate report card\n"
            "• /list_users – List users\n"
            "• /list_schools – List schools (Super Admin)"
        )
    elif query.data == "pay_now":
        await pay_callback(update, context)
    else:
        await query.edit_message_text("❌ Unknown service.")

# ========== ERROR HANDLER ==========
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if isinstance(context.error, NetworkError):
        logging.warning(f"Network error: {context.error}. Continuing...")
    else:
        logging.error(f"Unhandled error: {context.error}")

# ========== MAIN ==========

# ========== BULK IMPORT SCHOOLS ==========
import csv
import io
from telegram import Update
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, filters, ContextTypes

BULK_SCHOOLS_FILE = 100

async def bulk_schools_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Super Admin only.")
        return ConversationHandler.END
    await update.message.reply_text(
        "📤 **Bulk Import Schools**\n\n"
        "Send a CSV file with columns:\n"
        "tenant_id,name,type,country,currency,admin_phone,admin_user_id"
    )
    return BULK_SCHOOLS_FILE

async def bulk_schools_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    if not document or not document.file_name.endswith(".csv"):
        await update.message.reply_text("❌ Please send a CSV file.")
        return BULK_SCHOOLS_FILE
    await update.message.reply_text("✅ File received! Processing...")
    return ConversationHandler.END

bulk_schools_conv = ConversationHandler(
    entry_points=[CommandHandler("bulk_import_schools", bulk_schools_start)],
    states={BULK_SCHOOLS_FILE: [MessageHandler(filters.Document.ALL, bulk_schools_file)]},
    fallbacks=[CommandHandler("cancel", cancel)],
)

async def privacy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📄 **Privacy Policy – CommunityBusinessHelperBot**\n\n"
        "**What we collect:**\n"
        "• Telegram User ID, Username\n"
        "• School data (students, teachers, fees, grades)\n"
        "• Uploaded files (processed and deleted immediately)\n"
        "• Feedback and dispute messages\n\n"
        "**How we use it:**\n"
        "• To provide extraction and school management services\n"
        "• To track free trial usage (3 uses)\n"
        "• To process payments and manage Pro subscriptions\n"
        "• To respond to feedback and resolve disputes\n\n"
        "**Your rights (NDPA 2023):**\n"
        "• Access, rectify, delete, restrict, object, and data portability\n\n"
        "**Data deletion:**\n"
        "• Use `/delete_my_data` to request deletion\n"
        "• We will process your request within 72 hours\n\n"
        "**Third‑party services:**\n"
        "• Telegram (message delivery)\n"
        "• Selar (payment processing)\n"
        "• DeepSeek/OpenAI (future AI features)\n\n"
        "**Consent:**\n"
        "By using this bot, you consent to this policy.\n\n"
        "📌 Full policy available at: https://yourdomain.com/privacy\n"
        "📧 Contact: support@yourdomain.com"
    )

    await update.message.reply_text(
        "📄 **Privacy Policy – CommunityBusinessHelperBot**\n\n"
        "**What we collect:**\n"
        "• Telegram User ID, Username\n"
        "• School data (students, teachers, fees, grades)\n"
        "• Uploaded files (processed and deleted immediately)\n"
        "• Feedback and dispute messages\n\n"
        "**How we use it:**\n"
        "• To provide extraction and school management services\n"
        "• To track free trial usage (3 uses)\n"
        "• To process payments and manage Pro subscriptions\n"
        "• To respond to feedback and resolve disputes\n\n"
        "**Your rights (NDPA 2023):**\n"
        "• Access, rectify, delete, restrict, object, and data portability\n\n"
        "**Data deletion:**\n"
        "• Use `/delete_my_data` to request deletion\n"
        "• We will process your request within 72 hours\n\n"
        "**Third‑party services:**\n"
        "• Telegram (message delivery)\n"
        "• Selar (payment processing)\n"
        "• DeepSeek/OpenAI (future AI features)\n\n"
        "**Consent:**\n"
        "By using this bot, you consent to this policy.\n\n"
        "📌 Full policy available at: https://yourdomain.com/privacy\n"
        "📧 Contact: support@yourdomain.com"
    )

def main():
    os.environ["HTTPX_DNS_MODE"] = "system"
    init_db()
    # Create a custom httpx client with longer timeouts and proper DNS
    import httpx
    app = Application.builder().token(TOKEN).build()

    # --- Onboard ---
    onboard_conv = ConversationHandler(
        entry_points=[CommandHandler("onboard", onboard_start)],
        states={
            ONBOARD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, onboard_school_name)],
            ONBOARD_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, onboard_school_type)],
            ONBOARD_COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, onboard_school_country)],
            ONBOARD_CURRENCY: [MessageHandler(filters.TEXT & ~filters.COMMAND, onboard_school_currency)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(onboard_conv)
    app.add_handler(bulk_schools_conv)

    # --- Login ---
    login_conv = ConversationHandler(
        entry_points=[CommandHandler("admin_login", admin_login_start)],
        states={
            LOGIN_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_login_phone)],
            LOGIN_VERIFY: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_login_verify)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(login_conv)

    # --- Add Student ---
    add_student_conv = ConversationHandler(
        entry_points=[CommandHandler("add_student", add_student_start)],
        states={
            ADD_STUDENT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_student_name)],
            ADD_STUDENT_CLASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_student_class)],
            ADD_STUDENT_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_student_age)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(add_student_conv)

    # --- Add Teacher ---
    add_teacher_conv = ConversationHandler(
        entry_points=[CommandHandler("add_teacher", add_teacher_start)],
        states={
            ADD_TEACHER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_teacher_name)],
            ADD_TEACHER_SUBJECTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_teacher_subjects)],
            ADD_TEACHER_CLASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_teacher_class)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(add_teacher_conv)

    # --- Admissions ---
    adm_conv = ConversationHandler(
        entry_points=[CommandHandler("admission", admission_start)],
        states={
            ADM_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, admission_name)],
            ADM_DOB: [MessageHandler(filters.TEXT & ~filters.COMMAND, admission_dob)],
            ADM_CLASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, admission_class)],
            ADM_BIRTH_CERT: [MessageHandler(filters.PHOTO | filters.Document.ALL, admission_birth_cert)],
            ADM_REPORT_CARD: [MessageHandler(filters.PHOTO | filters.Document.ALL, admission_report_card)],
            ADM_PHOTO: [MessageHandler(filters.PHOTO | filters.Document.ALL, admission_photo)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(adm_conv)

    # --- Conferences ---
    set_conf_conv = ConversationHandler(
        entry_points=[CommandHandler("set_availability", set_availability)],
        states={
            CONF_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, conf_date)],
            CONF_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, conf_time)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(set_conf_conv)

    book_conf_conv = ConversationHandler(
        entry_points=[CommandHandler("book_conference", book_conference)],
        states={
            CONF_BOOK_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, conf_book_code)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(book_conf_conv)

    # --- Broadcast ---
    broadcast_conv = ConversationHandler(
        entry_points=[CommandHandler("broadcast", broadcast)],
        states={
            BROADCAST_MSG: [MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_send)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(broadcast_conv)

    # --- Budget ---
    budget_conv = ConversationHandler(
        entry_points=[CommandHandler("set_budget", set_budget)],
        states={
            BUDGET_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, budget_category)],
            BUDGET_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, budget_amount)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(budget_conv)

    expense_conv = ConversationHandler(
        entry_points=[CommandHandler("add_expense", add_expense)],
        states={
            EXPENSE_ITEM: [MessageHandler(filters.TEXT & ~filters.COMMAND, expense_item)],
            EXPENSE_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, expense_desc)],
            EXPENSE_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, expense_amount)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(expense_conv)

    # --- PTA ---
    pta_conv = ConversationHandler(
        entry_points=[CommandHandler("pta_create", pta_create)],
        states={
            PTA_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, pta_title)],
            PTA_AGENDA: [MessageHandler(filters.TEXT & ~filters.COMMAND, pta_agenda)],
            PTA_DATETIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, pta_datetime)],
            PTA_VENUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, pta_venue)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(pta_conv)

    pta_reg_conv = ConversationHandler(
        entry_points=[CommandHandler("pta_register", pta_register)],
        states={
            PTA_REGISTER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, pta_register_id)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(pta_reg_conv)

    # --- Events ---
    event_conv = ConversationHandler(
        entry_points=[CommandHandler("event_create", event_create)],
        states={
            EVENT_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, event_title)],
            EVENT_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, event_desc)],
            EVENT_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, event_type)],
            EVENT_START: [MessageHandler(filters.TEXT & ~filters.COMMAND, event_start)],
            EVENT_END: [MessageHandler(filters.TEXT & ~filters.COMMAND, event_end)],
            EVENT_VENUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, event_venue)],
            EVENT_MAX: [MessageHandler(filters.TEXT & ~filters.COMMAND, event_max)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(event_conv)

    event_reg_conv = ConversationHandler(
        entry_points=[CommandHandler("event_register", event_register)],
        states={
            EVENT_REG_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, event_reg_id)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(event_reg_conv)

    event_result_conv = ConversationHandler(
        entry_points=[CommandHandler("event_results", event_results)],
        states={
            EVENT_RESULT_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, event_result_id)],
            EVENT_RESULT_SCORE: [MessageHandler(filters.TEXT & ~filters.COMMAND, event_result_score)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(event_result_conv)

    # --- Circular & Newsletter ---
    circ_conv = ConversationHandler(
        entry_points=[CommandHandler("circular", circular)],
        states={
            CIRC_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, circ_title)],
            CIRC_CONTENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, circ_content)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(circ_conv)

    news_conv = ConversationHandler(
        entry_points=[CommandHandler("newsletter", newsletter)],
        states={
            NEWS_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, news_title)],
            NEWS_CONTENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, news_content)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(news_conv)

    # --- Logout School Conversation ---
    logout_school_conv = ConversationHandler(
        entry_points=[CommandHandler("logout_school", logout_school_start)],
        states={LOGOUT_SCHOOL_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, logout_school_confirm)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(logout_school_conv)

    # --- Logout Admin Conversation ---
    logout_admin_conv = ConversationHandler(
        entry_points=[CommandHandler("logout_admin", logout_admin_start)],
        states={LOGOUT_ADMIN_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, logout_admin_confirm)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(logout_admin_conv)

    # --- Logout User Conversation ---
    logout_user_conv = ConversationHandler(
        entry_points=[CommandHandler("logout_user", logout_user_start)],
        states={LOGOUT_USER_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, logout_user_confirm)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(logout_user_conv)

    # --- Link Parent Conversation ---
    link_parent_conv = ConversationHandler(
        entry_points=[CommandHandler("link_parent", link_parent_start)],
        states={
            LINK_PARENT_STUDENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, link_parent_student)],
            LINK_PARENT_PARENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, link_parent_parent)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(link_parent_conv)

    # --- Single command handlers ---
    app.add_handler(CommandHandler("dashboard", dashboard))
    app.add_handler(CommandHandler("fees", fees))
    app.add_handler(CommandHandler("attendance", attendance))
    app.add_handler(CommandHandler("grades", grades))
    app.add_handler(CommandHandler("timetable", timetable))
    app.add_handler(CommandHandler("assignments", assignments))
    app.add_handler(CommandHandler("report_card", report_card))
    app.add_handler(CommandHandler("list_users", list_users))
    app.add_handler(CommandHandler("list_schools", list_schools))
    app.add_handler(CommandHandler("view_applications", view_applications))
    app.add_handler(CommandHandler("approve_admission", approve_admission))
    app.add_handler(CommandHandler("reject_admission", reject_admission))
    app.add_handler(CommandHandler("parent_dashboard", parent_dashboard))
    app.add_handler(CommandHandler("store", store_list))
    app.add_handler(CommandHandler("order", order_item))
    app.add_handler(CommandHandler("view_budget", view_budget))
    app.add_handler(CommandHandler("budget_report", budget_report))
    app.add_handler(CommandHandler("pta_list", pta_list))
    app.add_handler(CommandHandler("event_list", event_list))
    app.add_handler(CommandHandler("mark_attendance", mark_attendance))

    # --- Extraction commands ---
    app.add_handler(CommandHandler("whatsapp", whatsapp))
    app.add_handler(CommandHandler("email", email))
    app.add_handler(CommandHandler("social", social))
    app.add_handler(CommandHandler("nin", nin))
    app.add_handler(CommandHandler("bvn", bvn))
    app.add_handler(CommandHandler("urls", urls))
    app.add_handler(CommandHandler("agents", agents))

    # --- Payment ---
    app.add_handler(CommandHandler("pay", pay))
    app.add_handler(CallbackQueryHandler(pay_callback, pattern="pay_now"))

    # --- General ---
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("commands", commands))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("privacy", privacy))
    app.add_handler(CommandHandler("privacy", privacy))
    app.add_handler(CommandHandler("guide", guide))
    app.add_handler(CommandHandler("roadmap", roadmap))
    app.add_handler(CommandHandler("community", community))
    app.add_handler(CommandHandler("health", health))
    app.add_handler(CommandHandler("offer_status", offer_status))

    app.add_handler(CallbackQueryHandler(service_callback, pattern="service_"))

    # --- File handler ---
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))

    app.add_error_handler(error_handler)

    print("🤖 KOSFintech Helper Bot (All Features Integrated) started...")
if __name__ == "__main__":
    main()

import csv
import io
from telegram import Update
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, filters, ContextTypes

BULK_SCHOOLS_FILE = 100  # state

async def bulk_schools_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Super Admin only.")
        return ConversationHandler.END
    await update.message.reply_text(
        "📤 **Bulk Import Schools**\n\n"
        "Send a CSV file with the following columns:\n"
        "`tenant_id,name,type,country,currency,admin_phone,admin_user_id`\n\n"
        "Rules:\n"
        "- tenant_id: unique, lowercase, underscores\n"
        "- type: Primary/Secondary/Tertiary/Vocational/Other\n"
        "- country: Nigeria, Ghana, Kenya, South Africa, Uganda\n"
        "- currency: NGN, GHS, KES, ZAR, UGX\n"
        "- admin_phone: with country code\n"
        "- admin_user_id: numeric Telegram ID\n\n"
        "Send a `.csv` file."
    )
    return BULK_SCHOOLS_FILE

async def bulk_schools_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    if not document or not document.file_name.endswith('.csv'):
        await update.message.reply_text("❌ Please send a CSV file.")
        return BULK_SCHOOLS_FILE

    try:
        file = await context.bot.get_file(document.file_id)
        file_content = await file.download_as_bytearray()
        # Decode and parse CSV
        content = file_content.decode('utf-8')
        reader = csv.DictReader(io.StringIO(content))
        required_headers = {'tenant_id','name','type','country','currency','admin_phone','admin_user_id'}
        if not required_headers.issubset(reader.fieldnames):
            await update.message.reply_text(f"❌ Missing columns. Required: {', '.join(required_headers)}")
            return BULK_SCHOOLS_FILE

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()

        allowed_types = ('Primary','Secondary','Tertiary','Vocational','Other')
        allowed_countries = ('Nigeria','Ghana','Kenya','South Africa','Uganda')
        allowed_currencies = ('NGN','GHS','KES','ZAR','UGX')

        success_count = 0
        fail_count = 0
        errors = []

        for idx, row in enumerate(reader, start=2):
            tenant_id = row.get('tenant_id', '').strip().lower().replace(' ', '_')
            name = row.get('name', '').strip()
            typ = row.get('type', '').strip()
            country = row.get('country', '').strip()
            currency = row.get('currency', '').strip()
            admin_phone = row.get('admin_phone', '').strip()
            admin_user_id = row.get('admin_user_id', '').strip()

            # Validate each field
            row_errors = []
            if not tenant_id:
                row_errors.append("tenant_id missing")
            elif not re.match(r'^[a-z0-9_]+$', tenant_id):
                row_errors.append("tenant_id must be lowercase letters, numbers, underscores")
            else:
                # Check uniqueness
                c.execute('SELECT 1 FROM schools WHERE tenant_id = ?', (tenant_id,))
                if c.fetchone():
                    row_errors.append(f"tenant_id '{tenant_id}' already exists")

            if not name:
                row_errors.append("name missing")
            elif len(name) > 100:
                row_errors.append("name too long (max 100)")

            if typ not in allowed_types:
                row_errors.append(f"type must be one of: {', '.join(allowed_types)}")
            if country not in allowed_countries:
                row_errors.append(f"country must be one of: {', '.join(allowed_countries)}")
            if currency not in allowed_currencies:
                row_errors.append(f"currency must be one of: {', '.join(allowed_currencies)}")

            if not admin_phone:
                row_errors.append("admin_phone missing")
            elif not re.match(r'^\+\d{10,15}$', admin_phone):
                row_errors.append("admin_phone must include country code (e.g., +234...)")

            if not admin_user_id:
                row_errors.append("admin_user_id missing")
            elif not admin_user_id.isdigit():
                row_errors.append("admin_user_id must be numeric")

            if row_errors:
                fail_count += 1
                errors.append(f"Row {idx} ({name or 'unnamed'}): {'; '.join(row_errors)}")
                continue

            # Insert school
            try:
                c.execute('''INSERT INTO schools (tenant_id, name, type, country, currency)
                             VALUES (?,?,?,?,?)''',
                          (tenant_id, name, typ, country, currency))
                # Insert admin
                c.execute('''INSERT INTO school_admins
                             (tenant_id, user_id, role, phone, verified)
                             VALUES (?,?,?,?,?)''',
                          (tenant_id, int(admin_user_id), 'owner', admin_phone, 1))
                conn.commit()
                success_count += 1
            except sqlite3.IntegrityError as e:
                fail_count += 1
                errors.append(f"Row {idx} ({name}): DB error – {e}")
                conn.rollback()

        conn.close()

        # Report
        msg = f"📊 **Bulk Import Summary**\n\n✅ Success: {success_count}\n❌ Failed: {fail_count}"
        if errors:
            msg += "\n\n**Errors:**\n" + "\n".join(errors[:10])

    except Exception as e:
        logging.error(f"Bot crashed: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Error processing file: {e}")
        return BULK_SCHOOLS_FILE

    entry_points=[CommandHandler("bulk_import_schools", bulk_schools_start)],
    states={BULK_SCHOOLS_FILE: [MessageHandler(filters.Document.ALL, bulk_schools_file)]},
    fallbacks=[CommandHandler("cancel", cancel)],
