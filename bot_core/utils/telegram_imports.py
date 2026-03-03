# bot_core/utils/telegram_imports.py

from telegram import (
    Update, 
    Bot, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    ReplyKeyboardRemove
)
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler, 
    ConversationHandler, 
    ContextTypes, 
    filters
)
# تم استبدال Unauthorized بـ Forbidden للتوافق مع الإصدارات الجديدة
from telegram.error import Forbidden, BadRequest

