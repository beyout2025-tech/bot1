import logging
from bot_core.utils.telegram_imports import Update, ContextTypes
from bot_core.handlers.user_handlers import show_categories, show_main_menu, show_courses, show_course_details
# استيراد الدوال الضرورية فقط
from bot_core.handlers.admin_handlers import (
    show_dev_panel, show_dev_stats, show_dev_users, 
    show_manage_courses_menu, show_manage_categories_menu
)

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    data = query.data

    # حماية: أي زر يبدأ بكلمات تخص "المحادثات" نتركه فوراً ليعالجه main.py
    # لا نضع هنا أي زر يُستخدم داخل ConversationHandler
    protected_prefixes = ["register_", "gender_", "select_cat_", "edit_field_", "edit_cat_", "move_to_cat_", "del_course_confirm_", "del_cat_"]
    if any(data.startswith(p) for p in protected_prefixes):
        return # نخرج فوراً لنعطي الفرصة للمحادثة

    try:
        if data == "show_categories":
            await show_categories(update, context)
        elif data == "main_menu":
            await show_main_menu(update, context)
        elif data == "dev_panel":
            await show_dev_panel(update, context)
        elif data == "dev_stats":
            await show_dev_stats(update, context)
        elif data == "dev_users":
            await show_dev_users(update, context)
        elif data == "dev_courses":
            await show_manage_courses_menu(update, context)
        elif data == "dev_categories":
            await show_manage_categories_menu(update, context)
        elif data.startswith("cat_"):
            await show_courses(update, context)
        elif data.startswith("course_"):
            await show_course_details(update, context)
        
        await query.answer()
    except Exception as e:
        logging.error(f"Error in callbacks: {e}")
