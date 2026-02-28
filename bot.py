import sqlite3
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8626674822:AAEu1os9jwr_3rueiaANtzN3nHjQFMTWvgI"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

conn = sqlite3.connect("data.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS ledger (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amount REAL,
    type TEXT,
    rate REAL,
    fee REAL,
    user TEXT,
    time TEXT
)
""")
conn.commit()

rate = 7.0
fee = 0.0

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("机器人已启动，发送 +100 或 下发100 开始记账")

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global rate, fee

    text = update.message.text
    user = update.message.from_user.username

    if text.startswith("+"):
        amount = float(text[1:])
        cursor.execute("INSERT INTO ledger (amount,type,rate,fee,user,time) VALUES (?,?,?,?,?,datetime('now'))",
                       (amount, "in", rate, fee, user))
        conn.commit()
        u = amount / rate
        await update.message.reply_text(f"入款 {amount} RMB = {u:.2f} U")

    elif text.startswith("下发"):
        amount = float(text.replace("下发", ""))
        cursor.execute("INSERT INTO ledger (amount,type,rate,fee,user,time) VALUES (?,?,?,?,?,datetime('now'))",
                       (amount, "out", rate, fee, user))
        conn.commit()
        await update.message.reply_text(f"下发 {amount} U")

    elif text.startswith("设置汇率"):
        rate = float(text.replace("设置汇率", ""))
        await update.message.reply_text(f"汇率已设置为 {rate}")

    elif text == "显示账单":
        cursor.execute("SELECT SUM(amount) FROM ledger WHERE type='in'")
        total_in = cursor.fetchone()[0] or 0

        cursor.execute("SELECT SUM(amount) FROM ledger WHERE type='out'")
        total_out = cursor.fetchone()[0] or 0

        await update.message.reply_text(
            f"总入款: {total_in}\n总下发: {total_out}"
        )

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handle))

    app.run_polling()

if name == "__main__":
    main()
