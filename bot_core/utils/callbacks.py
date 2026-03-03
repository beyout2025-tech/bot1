# bot_core/utils/callbacks.py

import logging
from bot_core.utils.telegram_imports import (
    Update, ContextTypes
)

# استيراد دوال المستخدمين
from bot_core.handlers.user_handlers import (
    show_categories,
    show_main_menu,
    show_courses,
    show_course_details
)

# استيراد دوال المديرين
from bot_core.handlers.admin_handlers import (
    show_dev_panel,
    show_dev_stats,
    show_dev_users,
    show_manage_courses_menu,
    confirm_delete_course,
    edit_course_select_field,
    toggle_course_status,
    edit_course_get_new_value,
    update_course_with_new_cat,
    move_course_select_category,
    move_course,
    confirm_delete_category,
    execute_delete_category,
    show_manage_categories_menu
)

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    data = query.data

    # --- بداية التعديل: حماية المحادثات من التداخل ---
    # هذه القائمة تحتوي على البادئات (Prefixes) التي تخص الـ ConversationHandlers
    # إذا اكتشفنا أن الزر يخص عملية (إضافة/تعديل/تسجيل)، نترك المعالجة للـ Handler المختص
    conversation_prefixes = [
        "register_",      # تسجيل مستخدم
        "gender_",        # اختيار الجنس
        "accept_",        # قبول طلب
        "reject_",        # رفض طلب
        "dev_add_course", # بدء إضافة دورة
        "select_cat_",    # اختيار تصنيف أثناء إضافة دورة (هام جداً لمنع التهنيج)
        "dev_add_cat",    # إضافة تصنيف جديد
        "del_cat_confirm_",
        "dev_move_course",
        "edit_field_",
        "edit_cat_",
        "move_to_cat_"
    ]

    if any(data.startswith(prefix) for prefix in conversation_prefixes):
        # لا نقوم بعمل query.answer() هنا لأن الـ ConversationHandler هو من سيتولى ذلك
        return 
    # --- نهاية التعديل ---

    # معالجة الأزرار العامة والقوائم المستقلة
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
        # عرض الدورات داخل تصنيف (للمستخدم العادي)
        await show_courses(update, context)
    elif data.startswith("course_"):
        # عرض تفاصيل دورة معينة
        await show_course_details(update, context)
    elif data.startswith("del_course_confirm_"):
        await confirm_delete_course(update, context)
    elif data.startswith("edit_select_"):
        await edit_course_select_field(update, context)
    elif data.startswith("toggle_status_"):
        await toggle_course_status(update, context)
    elif data.startswith("edit_field_"):
        await edit_course_get_new_value(update, context)
    elif data.startswith("edit_cat_"):
        await update_course_with_new_cat(update, context)
    elif data.startswith("move_course_"):
        await move_course_select_category(update, context)
    elif data.startswith("move_to_cat_"):
        await move_course(update, context)
    elif data.startswith("del_cat_"):
        await confirm_delete_category(update, context)
    elif data in ["delete_cat_only", "delete_cat_with_courses"]:
        await execute_delete_category(update, context)

    # إنهاء حالة التحميل (الساعة الرملية) للأزرار التي لم يتم الرد عليها داخل الدوال
    try:
        await query.answer()
    except Exception as e:
        logging.error(f"Error answering callback query: {e}")
