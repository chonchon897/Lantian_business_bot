import sqlite3
import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler

# ===== 日志 =====
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ===== 数据库 =====
conn = sqlite3.connect("data.db", check_same_thread=False)
cursor = conn.cursor()

# 入款表
cursor.execute("""
CREATE TABLE IF NOT EXISTS deposits (
    amount REAL
)
""")

# 下发表
cursor.execute("""
CREATE TABLE IF NOT EXISTS withdrawals (
    amount REAL
)
""")

# 汇率表
cursor.execute("""
CREATE TABLE IF NOT EXISTS settings (
    rate REAL
)
""")

# 初始化默认汇率
cursor.execute("SELECT COUNT(*) FROM settings")
if cursor.fetchone()[0] == 0:
    cursor.execute("INSERT INTO settings VALUES (7)")
    conn.commit()

# ===== 获取汇率函数 =====
def get_rate():
    cursor.execute("SELECT rate FROM settings")
    return cursor.fetchone()[0]

# ===== start 命令 =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "机器人已启动\n"
        "发送 +100 或 下发 100 开始记账\n"
        "设置汇率：设置汇率7"
    )

# ===== 主消息处理 =====
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    # ===== 设置汇率 =====
    if (
        text.startswith("设置汇率")
        or text.startswith("汇率")
        or text.startswith("rate")
        or text.startswith("r ")
    ):
        try:
            rate = float(
                text.replace("设置汇率", "")
                    .replace("汇率", "")
                    .replace("rate", "")
                    .replace("r", "")
                    .strip()
            )

            cursor.execute("UPDATE settings SET rate=?", (rate,))
            conn.commit()

            await update.message.reply_text(f"✅ 汇率已设置为 {rate}")
        except:
            await update.message.reply_text("❌ 格式错误，例如：设置汇率7")

    # ===== 查看汇率 =====
    elif text == "查看汇率":
        rate = get_rate()
        await update.message.reply_text(f"当前汇率：{rate}")

    # ===== 入款 =====
    elif text.startswith("+"):
        try:
            amount = float(text[1:])
            cursor.execute("INSERT INTO deposits VALUES (?)", (amount,))
            conn.commit()

            rate = get_rate()
            u = amount / rate

            await update.message.reply_text(
                f"入款 {amount} RMB = {u:.2f} U"
            )
        except:
            await update.message.reply_text("格式错误，例如：+1000")

    # ===== 下发 =====
    elif text.startswith("下发"):
        try:
            amount = float(text.replace("下发", "").strip())
            cursor.execute("INSERT INTO withdrawals VALUES (?)", (amount,))
            conn.commit()

            await update.message.reply_text(
                f"下发 {amount} U"
            )
        except:
            await update.message.reply_text("格式错误，例如：下发 200")

    # ===== 显示账单 =====
    elif text == "显示账单":

        cursor.execute("SELECT SUM(amount) FROM deposits")
        deposit = cursor.fetchone()[0] or 0

        cursor.execute("SELECT SUM(amount) FROM withdrawals")
        withdraw = cursor.fetchone()[0] or 0

        await update.message.reply_text(
            f"总入款: {deposit}\n总下发: {withdraw}"
        )

# ===== 主程序 =====
def main():

    TOKEN = os.getenv("BOT_TOKEN")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handle))

    print("机器人已启动")
    app.run_polling()

if __name__ == "__main__":
    main()
