import os
import random
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from telegram import Bot

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=TELEGRAM_TOKEN)

app = FastAPI()

MESSAGES = [
    "📚 *Heads Up!* "
    "{0} just borrowed '{1}' "
    "from {2} until {3}. "
    "Enjoy the read and return it on time! 😊",

    "✨ *New Book Adventure!*"
    " {0} has a fresh book '{1}' "
    "borrowed from {2} to {3}. "
    "Happy reading! 📖",

    "CONGRATULATIONS! 🎉🥳\n"
    "{0} borrowed '{1}' from {2} to {3}. "
    "Don’t forget to bring it back! 😉",

    "Woohoo! 🎊 "
    "{0} grabbed '{1}' from {2} to {3}. "
    "Dive into the pages! 📘",

    "📢 *Attention!* "
    "{0} borrowed '{1}' from {2} until {3}. "
    "Remember to return it on time! 📆",

    "Enjoy your book journey, {0}! 🌟 "
    "You’ve borrowed '{1}' from {2} to {3}. "
    "Happy reading! 📚",

    "📖 *New Borrowing Alert!* "
    "{0} has taken '{1}' from {2} to {3}. "
    "Have a great read and don’t forget the return date! ⏳",

    "Another book in the bag! 📚 "
    "{0} borrowed '{1}' from {2} to {3}. "
    "Keep track and return it safely! 💼",
]


class BorrowingData(BaseModel):
    user_email: str
    book_title: str
    borrow_date: str
    expected_return_date: str


async def send_telegram_message(message: str):
    await bot.send_message(CHAT_ID, message)


@app.post("/notify/")
async def notify_borrowing(data: BorrowingData):
    message = random.choice(MESSAGES).format(
        data.user_email,
        data.book_title,
        data.borrow_date,
        data.expected_return_date
    )
    await send_telegram_message(message)
    return {"status": "success", "message": message}


class MessageData(BaseModel):
    message: str


@app.post("/overdue/")
async def notify_overdue_borrowing(message_data: MessageData):
    await send_telegram_message(message_data.message)
    return {"status": "success", "message": message_data.message}
