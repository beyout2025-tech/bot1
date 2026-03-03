import logging
# bot_core/handlers/admin_handlers.py

from bot_core.utils.telegram_imports import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove,
    ConversationHandler, ContextTypes, filters, Forbidden, BadRequest, Bot
)

# استيراد db_manager
from db_manager import (
    get_all_admins, is_admin, add_admin, remove_admin, get_stats, 
    get_all_users, get_all_courses, add_course, get_all_categories, 
    get_courses_by_category, get_course_by_id, delete_course, 
    update_course_field, add_category, delete_category, update_registration_status
)

# استيراد دوال مساعدة
from bot_core.handlers.user_handlers import show_main_menu

# تعريف حالات المحادثة للمديرين
(
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
    CONFIRM_DELETE_CAT_ACTION,
) = range(7, 26)

DEV_ID = 873158772

async def show_dev_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await query.edit_message_text("عذرًا، أنت لست مديرًا.")
        return

    keyboard = [
        [InlineKeyboardButton("📊 إحصائيات", callback_data="dev_stats")],
        [InlineKeyboardButton("👤 إدارة المستخدمين", callback_data="dev_users")],
        [InlineKeyboardButton("📚 إدارة الدورات", callback_data="dev_courses")],
        [InlineKeyboardButton("🗂️ إدارة التصنيفات", callback_data="dev_categories")],
        [InlineKeyboardButton("📢 إرسال رسالة جماعية", callback_data="dev_broadcast")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("مرحباً بك في لوحة المطور! اختر من القائمة:", reply_markup=reply_markup)


async def show_dev_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    # جلب القاموس من db_manager
    stats = get_stats()
    
    stats_text = (
        f"**📊 إحصائيات البوت**\n\n"
        f"عدد المستخدمين: {stats['num_users']}\n"
        f"عدد الدورات: {stats['num_courses']}\n"
        f"عدد المديرين: {stats['num_admins']}\n\n"
        f"**إحصائيات التسجيلات:**\n"
        f"⏳ طلبات معلقة: {stats['num_pending']}\n"
        f"✅ طلبات مقبولة: {stats['num_accepted']}\n"
        f"❌ طلبات مرفوضة: {stats['num_rejected']}"
    )
    
    keyboard = [[InlineKeyboardButton("⬅️ رجوع", callback_data="dev_panel")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(stats_text, reply_markup=reply_markup, parse_mode='Markdown')


async def show_dev_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("➕ إضافة مشرف", callback_data="dev_add_admin")],
        [InlineKeyboardButton("➖ إزالة مشرف", callback_data="dev_remove_admin")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="dev_panel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("اختر عملية إدارة المستخدمين:", reply_markup=reply_markup)


async def add_admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("أرسل معرف المستخدم (User ID) الذي تريد إضافته كمشرف:")
    return GET_ADMIN_ID_TO_ADD

# تغيير اسم الدالة لتجنب التعارض مع add_admin المستوردة
async def process_add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        new_admin_id = int(update.message.text)
        # استدعاء دالة db_manager
        if add_admin(new_admin_id):
            await update.message.reply_text(f"تم إضافة المستخدم {new_admin_id} كمشرف بنجاح.", reply_markup=ReplyKeyboardRemove())
            
            try:
                await context.bot.send_message(
                    chat_id=new_admin_id,
                    text="✅ تهانينا! لقد تم إضافتك كمدير في البوت."
                )
            except (Forbidden, BadRequest):
                logging.warning(f"Failed to notify user {new_admin_id} about admin promotion.")
        else:
            await update.message.reply_text("هذا المستخدم هو مشرف بالفعل.")

    except ValueError:
        await update.message.reply_text("الرجاء إرسال رقم صحيح.")
    return ConversationHandler.END


async def remove_admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    admins_to_remove = [admin for admin in get_all_admins() if admin != DEV_ID]
    if not admins_to_remove:
        await query.edit_message_text("لا يوجد مشرفون لإزالتهم.")
        return ConversationHandler.END
        
    admin_list = "\n".join([str(a) for a in admins_to_remove])
    await query.edit_message_text(f"أرسل معرف المستخدم (User ID) الذي تريد إزالته من المشرفين:\n\nالمشرفون الحاليون:\n{admin_list}")
    return GET_ADMIN_ID_TO_REMOVE

# تغيير اسم الدالة لتجنب التعارض
async def process_remove_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        admin_id_to_remove = int(update.message.text)
        if admin_id_to_remove == DEV_ID:
            await update.message.reply_text("لا يمكنك إزالة المطور الأساسي.", reply_markup=ReplyKeyboardRemove())
        elif is_admin(admin_id_to_remove):
            remove_admin(admin_id_to_remove)
            await update.message.reply_text(f"تم إزالة المستخدم {admin_id_to_remove} من المشرفين.", reply_markup=ReplyKeyboardRemove())
        else:
            await update.message.reply_text("هذا المستخدم ليس مشرفًا.")
    except ValueError:
        await update.message.reply_text("الرجاء إرسال رقم صحيح.")
    return ConversationHandler.END


async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("الرجاء إرسال الرسالة (نص أو صورة) التي تريد إرسالها لجميع المستخدمين:")
    return GET_BROADCAST_MESSAGE

async def send_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    message_text = update.message.caption if update.message.photo else update.message.text
    media_file_id = update.message.photo[-1].file_id if update.message.photo else None
    
    users = get_all_users()
    
    success_count = 0
    fail_count = 0
    
    for user_id in users:
        try:
            if media_file_id:
                await context.bot.send_photo(chat_id=user_id, photo=media_file_id, caption=message_text)
            else:
                await context.bot.send_message(chat_id=user_id, text=message_text)
            success_count += 1
        except Forbidden:
            fail_count += 1
        except Exception:
            fail_count += 1

    await update.message.reply_text(f"تم إرسال الرسالة بنجاح إلى {success_count} مستخدم.\nفشل الإرسال إلى {fail_count} مستخدم.", reply_markup=ReplyKeyboardRemove())
    await show_dev_panel_after_conv(update, context)
    return ConversationHandler.END

async def show_dev_panel_after_conv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if is_admin(user_id):
        keyboard = [
            [InlineKeyboardButton("📊 إحصائيات", callback_data="dev_stats")],
            [InlineKeyboardButton("👤 إدارة المستخدمين", callback_data="dev_users")],
            [InlineKeyboardButton("📚 إدارة الدورات", callback_data="dev_courses")],
            [InlineKeyboardButton("🗂️ إدارة التصنيفات", callback_data="dev_categories")],
            [InlineKeyboardButton("📢 إرسال رسالة جماعية", callback_data="dev_broadcast")],
            [InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=user_id,
            text="تمت العملية بنجاح. عدت إلى لوحة المطور. اختر من القائمة:",
            reply_markup=reply_markup
        )
    else:
        await show_main_menu(update, context)


async def show_manage_courses_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    courses = get_all_courses()
    courses_list = ""
    if courses:
        for c in courses:
            courses_list += f"- {'✅' if c[5] else '❌'} {c[1]} (ID: {c[0]})\n"
    else:
        courses_list = "لا توجد دورات حالياً."
        
    keyboard = [
        [InlineKeyboardButton("➕ إضافة دورة جديدة", callback_data="dev_add_course")],
        [InlineKeyboardButton("✏️ تعديل دورة", callback_data="dev_edit_course")],
        [InlineKeyboardButton("➡️ نقل دورة", callback_data="dev_move_course")],
        [InlineKeyboardButton("🗑️ حذف دورة", callback_data="dev_delete_course")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="dev_panel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(f"**📚 إدارة الدورات**\n\n{courses_list}", reply_markup=reply_markup, parse_mode='Markdown')

async def add_course_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("الرجاء إدخال **اسم الدورة**:")
    return ADD_COURSE_NAME

async def add_course_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["temp_course_data"] = {"name": update.message.text}
    await update.message.reply_text("الآن، أدخل **وصف الدورة**:")
    return ADD_COURSE_DESC

async def add_course_desc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["temp_course_data"]["description"] = update.message.text
    await update.message.reply_text("الآن، أدخل **سعر الدورة** بالأرقام:")
    return ADD_COURSE_PRICE

async def add_course_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        price = float(update.message.text)
        context.user_data["temp_course_data"]["price"] = price
        
        categories = get_all_categories()
        if not categories:
            await update.message.reply_text("لا توجد تصنيفات، الرجاء إضافة تصنيف أولاً.")
            return ConversationHandler.END

        keyboard = [[InlineKeyboardButton(cat, callback_data=f"select_cat_{cat}")] for cat in categories]
        await update.message.reply_text("اختر **تصنيف الدورة**:", reply_markup=InlineKeyboardMarkup(keyboard))
        return ADD_COURSE_CAT
    except ValueError:
        await update.message.reply_text("الرجاء إدخال سعر صحيح (رقم).")
        return ADD_COURSE_PRICE

async def add_course_cat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    category = query.data.split("select_cat_")[1]
    data = context.user_data.pop("temp_course_data")
    
    # تمرير البيانات كمتغيرات منفصلة لتناسب db_manager
    add_course(data['name'], data['description'], data['price'], category)
    
    await query.edit_message_text("✅ تم إضافة الدورة بنجاح!")
    await show_manage_courses_menu(update, context)
    return ConversationHandler.END


async def delete_course_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    courses = get_all_courses()
    if not courses:
        await query.edit_message_text("لا توجد دورات لحذفها.")
        return ConversationHandler.END
    
    keyboard = []
    for c in courses:
        keyboard.append([InlineKeyboardButton(f"{c[1]} (ID: {c[0]})", callback_data=f"del_course_confirm_{c[0]}")])
    keyboard.append([InlineKeyboardButton("⬅️ إلغاء", callback_data="dev_courses")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("اختر الدورة التي تريد حذفها:", reply_markup=reply_markup)
    return DELETE_COURSE_CONFIRM


async def confirm_delete_course(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    course_id = int(query.data.split("del_course_confirm_")[1])
    
    delete_course(course_id)
    
    await query.edit_message_text(f"✅ تم حذف الدورة بنجاح.")
    await show_manage_courses_menu(update, context)
    return ConversationHandler.END


async def edit_course_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    courses = get_all_courses()
    if not courses:
        await query.edit_message_text("لا توجد دورات لتعديلها.")
        return ConversationHandler.END
    
    keyboard = []
    for c in courses:
        keyboard.append([InlineKeyboardButton(f"{c[1]} (ID: {c[0]})", callback_data=f"edit_select_{c[0]}")])
    keyboard.append([InlineKeyboardButton("⬅️ إلغاء", callback_data="dev_courses")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text("اختر الدورة التي تريد تعديلها:", reply_markup=reply_markup)
    return EDIT_COURSE_SELECT_COURSE

async def edit_course_select_field(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    course_id = int(query.data.split("edit_select_")[1])
    context.user_data["edit_course_id"] = course_id
    
    keyboard = [
        [InlineKeyboardButton("تعديل الاسم", callback_data="edit_field_name")],
        [InlineKeyboardButton("تعديل الوصف", callback_data="edit_field_description")],
        [InlineKeyboardButton("تعديل السعر", callback_data="edit_field_price")],
        [InlineKeyboardButton("تعديل التصنيف", callback_data="edit_field_category")],
        [InlineKeyboardButton("تغيير الحالة (متاح/غير متاح)", callback_data=f"toggle_status_{course_id}")],
        [InlineKeyboardButton("⬅️ إلغاء", callback_data="dev_courses")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("اختر ما تريد تعديله في الدورة:", reply_markup=reply_markup)
    return EDIT_COURSE_SELECT_FIELD

async def edit_course_get_new_value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    field = query.data.split("edit_field_")[1]
    context.user_data["edit_field"] = field
    
    if field == "category":
        categories = get_all_categories()
        keyboard = [[InlineKeyboardButton(cat, callback_data=f"edit_cat_{cat}")] for cat in categories]
        await query.edit_message_text("اختر التصنيف الجديد:", reply_markup=InlineKeyboardMarkup(keyboard))
        return EDIT_COURSE_CAT
    else:
        await query.edit_message_text(f"الرجاء إرسال القيمة الجديدة لـ {field}:")
        return EDIT_COURSE_NEW_VALUE

async def update_course_with_new_value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    course_id = context.user_data.pop("edit_course_id")
    field = context.user_data.pop("edit_field")
    
    new_value = update.message.text
    if field == "price":
        try:
            new_value = float(new_value)
        except ValueError:
            await update.message.reply_text("الرجاء إدخال قيمة رقمية صحيحة للسعر.")
            return EDIT_COURSE_NEW_VALUE
            
    update_course_field(course_id, field, new_value)
            
    await update.message.reply_text(f"✅ تم تعديل الدورة بنجاح.", reply_markup=ReplyKeyboardRemove())
    await show_dev_panel_after_conv(update, context)
    return ConversationHandler.END

async def update_course_with_new_cat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    course_id = context.user_data.pop("edit_course_id")
    category = query.data.split("edit_cat_")[1]
    
    update_course_field(course_id, "category", category)
            
    await query.edit_message_text(f"✅ تم تعديل تصنيف الدورة بنجاح.")
    await show_manage_courses_menu(update, context)
    return ConversationHandler.END


async def toggle_course_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    course_id = int(query.data.split("toggle_status_")[1])
    
    course = get_course_by_id(course_id)
    if course:
        new_status = 1 if not bool(course[5]) else 0
        update_course_field(course_id, "active", new_status)

    await query.edit_message_text("✅ تم تغيير حالة الدورة بنجاح.")
    await show_manage_courses_menu(update, context)
    return ConversationHandler.END

async def move_course_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    courses = get_all_courses()
    if not courses:
        await query.edit_message_text("لا توجد دورات لنقلها.")
        return ConversationHandler.END
    
    keyboard = []
    for c in courses:
        keyboard.append([InlineKeyboardButton(f"{c[1]} (ID: {c[0]})", callback_data=f"move_course_{c[0]}")])
    keyboard.append([InlineKeyboardButton("⬅️ إلغاء", callback_data="dev_courses")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text("اختر الدورة التي تريد نقلها:", reply_markup=reply_markup)
    return MOVE_COURSE_SELECT_COURSE

async def move_course_select_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    course_id = int(query.data.split("move_course_")[1])
    context.user_data["move_course_id"] = course_id
    
    categories = get_all_categories()
    
    if not categories:
        await query.edit_message_text("لا توجد تصنيفات لنقل الدورة إليها.")
        return ConversationHandler.END

    keyboard = [[InlineKeyboardButton(cat, callback_data=f"move_to_cat_{cat}")] for cat in categories]
    keyboard.append([InlineKeyboardButton("⬅️ إلغاء", callback_data="dev_courses")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text("اختر التصنيف الجديد للدورة:", reply_markup=reply_markup)
    return MOVE_COURSE_SELECT_CAT

async def move_course(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    new_category = query.data.split("move_to_cat_")[1]
    course_id = context.user_data.pop("move_course_id")
    
    update_course_field(course_id, "category", new_category)
            
    await query.edit_message_text("✅ تم نقل الدورة بنجاح.")
    await show_manage_courses_menu(update, context)
    return ConversationHandler.END


async def show_manage_categories_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    categories = get_all_categories()
    
    categories_list = "\n".join([f"- {cat}" for cat in categories]) if categories else "لا توجد تصنيفات حالياً."
    
    keyboard = [
        [InlineKeyboardButton("➕ إضافة تصنيف جديد", callback_data="dev_add_cat")],
        [InlineKeyboardButton("🗑️ حذف تصنيف", callback_data="dev_delete_cat")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="dev_panel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(f"**🗂️ إدارة التصنيفات**\n\n{categories_list}", reply_markup=reply_markup, parse_mode='Markdown')

async def add_category_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("الرجاء إدخال **اسم التصنيف** الجديد:")
    return ADD_CATEGORY_NAME

# تغيير اسم الدالة لتجنب التعارض
async def process_add_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    category_name = update.message.text
    if add_category(category_name):
        await update.message.reply_text("✅ تم إضافة التصنيف بنجاح.", reply_markup=ReplyKeyboardRemove())
    else:
        await update.message.reply_text("هذا التصنيف موجود بالفعل.")
    
    await show_dev_panel_after_conv(update, context)
    return ConversationHandler.END


async def delete_category_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    categories = get_all_categories()
    if not categories:
        await query.edit_message_text("لا توجد تصنيفات لحذفها.")
        return ConversationHandler.END
    
    keyboard = [[InlineKeyboardButton(cat, callback_data=f"del_cat_{cat}")] for cat in categories]
    keyboard.append([InlineKeyboardButton("⬅️ إلغاء", callback_data="dev_categories")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("اختر التصنيف الذي تريد حذفه:", reply_markup=reply_markup)
    return DELETE_CATEGORY_CONFIRM

async def confirm_delete_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    category_name = query.data.split("del_cat_")[1]
    
    context.user_data["temp_category_name"] = category_name
    
    keyboard = [
        [InlineKeyboardButton("حذف التصنيف فقط", callback_data="delete_cat_only")],
        [InlineKeyboardButton("حذف التصنيف والدورات التابعة له", callback_data="delete_cat_with_courses")],
        [InlineKeyboardButton("⬅️ إلغاء", callback_data="dev_categories")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(f"هل تريد حذف التصنيف '{category_name}' فقط أم مع جميع الدورات التابعة له؟", reply_markup=reply_markup)
    return CONFIRM_DELETE_CAT_ACTION

async def execute_delete_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    choice = query.data
    category_name = context.user_data.pop("temp_category_name")
    
    if choice == "delete_cat_with_courses":
        courses = get_courses_by_category(category_name)
        for c in courses:
            delete_course(c[0])
        delete_category(category_name)
        await query.edit_message_text(f"✅ تم حذف التصنيف '{category_name}' وجميع الدورات التابعة له بنجاح.")
    elif choice == "delete_cat_only":
        delete_category(category_name)
        await query.edit_message_text(f"✅ تم حذف التصنيف '{category_name}' فقط. الدورات التابعة له أصبحت بلا تصنيف.")
    
    await show_manage_categories_menu(update, context)
    return ConversationHandler.END

async def accept_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    _, user_id, course_id = query.data.split('_')
    context.user_data['temp_reg_user_id'] = int(user_id)
    context.user_data['temp_reg_course_id'] = int(course_id)
    await context.bot.send_message(
        chat_id=update.effective_user.id,
        text="الرجاء كتابة رسالة مخصصة للمستخدم لإرسالها مع طلب إيصال الدفع:",
        reply_markup=ReplyKeyboardRemove()
    )
    return GET_ACCEPT_MESSAGE

async def send_accept_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    accept_message = update.message.text
    user_id = context.user_data.pop('temp_reg_user_id')
    course_id = context.user_data.pop('temp_reg_course_id')
    
    update_registration_status(user_id, course_id, "accepted")

    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"✅ تهانينا! تم قبول طلب تسجيلك في الدورة.\n\n"
                 f"{accept_message}\n\n"
                 f"الآن، الرجاء إرسال إيصال الدفع هنا."
        )
    except (Forbidden, BadRequest):
        logging.warning(f"Failed to send acceptance message to user {user_id}.")

    await update.message.reply_text("تم إرسال رسالة القبول للمستخدم بنجاح.", reply_markup=ReplyKeyboardRemove())
    await show_dev_panel_after_conv(update, context)
    return ConversationHandler.END


async def reject_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    _, user_id, course_id = query.data.split('_')
    context.user_data['temp_reg_user_id'] = int(user_id)
    context.user_data['temp_reg_course_id'] = int(course_id)
    await context.bot.send_message(
        chat_id=update.effective_user.id,
        text="الرجاء كتابة رسالة رفض مخصصة للمستخدم:",
        reply_markup=ReplyKeyboardRemove()
    )
    return GET_REJECT_MESSAGE


async def send_reject_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reject_message = update.message.text
    user_id = context.user_data.pop('temp_reg_user_id')
    course_id = context.user_data.pop('temp_reg_course_id')

    update_registration_status(user_id, course_id, "rejected")

    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"❌ للأسف، تم رفض طلب تسجيلك.\n\n"
                 f"{reject_message}"
        )
    except (Forbidden, BadRequest):
        logging.warning(f"Failed to send rejection message to user {user_id}.")

    await update.message.reply_text("تم إرسال رسالة الرفض للمستخدم بنجاح.", reply_markup=ReplyKeyboardRemove())
    await show_dev_panel_after_conv(update, context)
    return ConversationHandler.END
