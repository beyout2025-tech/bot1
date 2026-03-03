# main.py
import logging
import os
import sys


sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from flask import Flask, request

from bot_core.utils.telegram_imports import (
    Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove,
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, ContextTypes, filters, Forbidden, BadRequest
)

# استيراد db_manager
from db_manager import (
    init_db, get_all_users, get_all_admins, is_admin, add_admin, remove_admin, 
    get_all_categories, get_courses_by_category, get_all_courses, get_course_by_id, 
    add_course, delete_course, update_course_field, get_stats, add_registration, 
    get_pending_registration, update_registration_status, update_registration_receipt, 
    get_accepted_registration, get_accepted_registrations_for_user
)

# استيراد دوال المستخدمين من ملف user_handlers.py
from bot_core.handlers.user_handlers import (
    show_main_menu,
    start,
    show_categories,
    show_courses,
    show_course_details,
    start_registration,
    get_name,
    get_gender,
    get_age,
    get_country,
    get_city,
    get_phone,
    get_email,
    handle_receipt,
    GET_NAME,
    GET_GENDER,
    GET_AGE,
    GET_COUNTRY,
    GET_CITY,
    GET_PHONE,
    GET_EMAIL
)

# استيراد دوال المديرين من ملف admin_handlers.py
# تم تحديث الأسماء هنا لتطابق التعديلات في admin_handlers.py
from bot_core.handlers.admin_handlers import (
    show_dev_panel,
    show_dev_stats,
    show_dev_users,
    add_admin_start,
    process_add_admin,     # الاسم المعدل
    remove_admin_start,
    process_remove_admin,  # الاسم المعدل
    broadcast_start,
    send_broadcast,
    show_dev_panel_after_conv,
    show_manage_courses_menu,
    add_course_start,
    add_course_name,
    add_course_desc,
    add_course_price,
    add_course_cat,
    delete_course_start,
    confirm_delete_course,
    edit_course_start,
    edit_course_select_field,
    edit_course_get_new_value,
    update_course_with_new_value,
    update_course_with_new_cat,
    toggle_course_status,
    move_course_start,
    move_course_select_category,
    move_course,
    show_manage_categories_menu,
    add_category_start,
    process_add_category,   # الاسم المعدل
    delete_category_start,
    confirm_delete_category,
    execute_delete_category,
    accept_registration,
    send_accept_message,
    reject_registration,
    send_reject_message,
    GET_ACCEPT_MESSAGE,
    GET_REJECT_MESSAGE,
    GET_BROADCAST_MESSAGE,
    GET_ADMIN_ID_TO_ADD,
    GET_ADMIN_ID_TO_REMOVE,
    ADD_COURSE_NAME,
    ADD_COURSE_DESC,
    ADD_COURSE_PRICE,
    ADD_COURSE_CAT,
    EDIT_COURSE_SELECT_COURSE,
    EDIT_COURSE_SELECT_FIELD,
    EDIT_COURSE_NEW_VALUE,
    ADD_CATEGORY_NAME,
    DELETE_CATEGORY_CONFIRM,
    DELETE_COURSE_CONFIRM,
    EDIT_COURSE_CAT,
    MOVE_COURSE_SELECT_COURSE,
    MOVE_COURSE_SELECT_CAT,
    CONFIRM_DELETE_CAT_ACTION
)

# استيراد دالة معالجة الأزرار من ملف callbacks.py
from bot_core.utils.callbacks import handle_callback_query

# استيراد التوكن من config
from config import BOT_TOKEN

# إعداد logging لتتبع الأخطاء
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# إنشاء البوت و Application
application = Application.builder().token(BOT_TOKEN).build()

# إنشاء تطبيق Flask
app = Flask(__name__)

# Route لاستقبال تحديثات Webhook
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.process_update(update)
    return "OK"

# Route أساسي لتأكيد أن السيرفر شغال
@app.route("/")
def home():
    return "Bot is running"

# دالة لإلغاء المحادثة
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('تم إلغاء العملية.', reply_markup=ReplyKeyboardRemove())
    await show_main_menu(update, context)
    return ConversationHandler.END


# دالة رئيسية لتشغيل البوت
def main() -> None:
    # تهيئة قاعدة البيانات عند بدء التشغيل
    init_db()

    # ConversationHandler لعملية تسجيل المستخدم
    user_reg_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_registration, pattern=r"^register_\d+$")],
        states={
            GET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            GET_GENDER: [CallbackQueryHandler(get_gender, pattern=r"^gender_")],
            GET_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
            GET_COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_country)],
            GET_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_city)],
            GET_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            GET_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # ConversationHandler لرسائل المدير المخصصة للقبول/الرفض
    admin_msg_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(accept_registration, pattern=r"^accept_\d+_\d+$"),
            CallbackQueryHandler(reject_registration, pattern=r"^reject_\d+_\d+$"),
        ],
        states={
            GET_ACCEPT_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_accept_message)],
            GET_REJECT_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_reject_message)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # ConversationHandler لإدارة المستخدمين
    admin_user_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(add_admin_start, pattern="^dev_add_admin$"),
            CallbackQueryHandler(remove_admin_start, pattern="^dev_remove_admin$"),
        ],
        states={
            GET_ADMIN_ID_TO_ADD: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_add_admin)],
            GET_ADMIN_ID_TO_REMOVE: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_remove_admin)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # ConversationHandler لإرسال رسالة جماعية
    admin_broadcast_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(broadcast_start, pattern="^dev_broadcast$")],
        states={
            GET_BROADCAST_MESSAGE: [MessageHandler(filters.TEXT | filters.PHOTO & ~filters.COMMAND, send_broadcast)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    # ConversationHandler لإضافة دورة جديدة
    admin_add_course_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_course_start, pattern="^dev_add_course$")],
        states={
            ADD_COURSE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_course_name)],
            ADD_COURSE_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_course_desc)],
            ADD_COURSE_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_course_price)],
            ADD_COURSE_CAT: [CallbackQueryHandler(add_course_cat, pattern=r"^select_cat_")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # ConversationHandler لتعديل دورة
    admin_edit_course_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(edit_course_start, pattern="^dev_edit_course$")],
        states={
            EDIT_COURSE_SELECT_COURSE: [CallbackQueryHandler(edit_course_select_field, pattern=r"^edit_select_\d+$")],
            EDIT_COURSE_SELECT_FIELD: [
                CallbackQueryHandler(edit_course_get_new_value, pattern=r"^edit_field_"),
                CallbackQueryHandler(toggle_course_status, pattern=r"^toggle_status_\d+$")
            ],
            EDIT_COURSE_NEW_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_course_with_new_value)],
            EDIT_COURSE_CAT: [CallbackQueryHandler(update_course_with_new_cat, pattern=r"^edit_cat_")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    # ConversationHandler لحذف دورة
    admin_delete_course_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(delete_course_start, pattern="^dev_delete_course$")],
        states={
            DELETE_COURSE_CONFIRM: [CallbackQueryHandler(confirm_delete_course, pattern=r"^del_course_confirm_\d+$")]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # ConversationHandler لنقل دورة
    admin_move_course_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(move_course_start, pattern="^dev_move_course$")],
        states={
            MOVE_COURSE_SELECT_COURSE: [CallbackQueryHandler(move_course_select_category, pattern=r"^move_course_\d+$")],
            MOVE_COURSE_SELECT_CAT: [CallbackQueryHandler(move_course, pattern=r"^move_to_cat_")]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    # ConversationHandler لإدارة التصنيفات
    admin_category_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(add_category_start, pattern="^dev_add_cat$"),
            CallbackQueryHandler(delete_category_start, pattern="^dev_delete_cat$")
        ],
        states={
            ADD_CATEGORY_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_add_category)],
            DELETE_CATEGORY_CONFIRM: [CallbackQueryHandler(confirm_delete_category, pattern=r"^del_cat_")],
            CONFIRM_DELETE_CAT_ACTION: [CallbackQueryHandler(execute_delete_category, pattern=r"^(delete_cat_only|delete_cat_with_courses)$")]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    # إضافة Handlers إلى الـ application
    application.add_handler(CommandHandler("start", start))
    application.add_handler(user_reg_handler)
    application.add_handler(admin_msg_handler)
    application.add_handler(admin_user_handler)
    application.add_handler(admin_broadcast_handler)
    application.add_handler(admin_add_course_handler)
    application.add_handler(admin_edit_course_handler)
    application.add_handler(admin_delete_course_handler)
    application.add_handler(admin_move_course_handler)
    application.add_handler(admin_category_handler)
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    application.add_handler(MessageHandler(filters.PHOTO, handle_receipt))
    
    # تشغيل البوت
    print("البوت يعمل بنجاح...")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

if __name__ == "__main__":
    main()
