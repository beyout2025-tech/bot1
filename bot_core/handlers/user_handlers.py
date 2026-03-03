import re
import logging
# bot_core/handlers/user_handlers.py

from bot_core.utils.telegram_imports import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove,
    ConversationHandler, ContextTypes, filters, Forbidden, BadRequest
)

# استيراد db_manager
from db_manager import (
    get_all_users, is_admin, add_user, get_all_admins, 
    get_all_categories, get_courses_by_category, get_course_by_id, 
    add_registration, get_accepted_registrations_for_user, update_registration_receipt
)

# تعريف حالات المحادثة للمستخدمين العاديين
(
    GET_NAME,
    GET_GENDER,
    GET_AGE,
    GET_COUNTRY,
    GET_CITY,
    GET_PHONE,
    GET_EMAIL,
) = range(7)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    
    keyboard = [
        [InlineKeyboardButton("📚 استعراض التصنيفات", callback_data="show_categories")]
    ]
    if is_admin(user_id):
        keyboard.append([InlineKeyboardButton("🔧 لوحة المطور", callback_data="dev_panel")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text="اختر من القائمة الرئيسية:", reply_markup=reply_markup
        )
    else:
        await update.message.reply_text("اختر من القائمة الرئيسية:", reply_markup=reply_markup)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_id = user.id
    
    is_new_user = add_user(user_id)
    
    if is_new_user:
        admin_ids_to_notify = [admin_id for admin_id in get_all_admins() if admin_id != user_id]
        if admin_ids_to_notify:
            message_to_admin = (
                f"**🔔 مستخدم جديد دخل البوت!**\n\n"
                f"**الاسم:** {user.first_name} {user.last_name or ''}\n"
                f"**المعرف (@):** {user.username or 'لا يوجد'}\n"
                f"**معرف المستخدم (ID):** `{user_id}`"
            )
            for admin_id in admin_ids_to_notify:
                try:
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=message_to_admin,
                        parse_mode='Markdown'
                    )
                except (Forbidden, BadRequest):
                    continue
    
    await update.message.reply_text("أهلاً بك في بوت الدورات التدريبية!", reply_markup=ReplyKeyboardRemove())
    await show_main_menu(update, context)


async def show_categories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    categories = get_all_categories()
    
    if not categories:
        await query.edit_message_text(text="لا توجد تصنيفات متاحة حالياً.")
        return

    keyboard = []
    for i in range(0, len(categories), 2):
        row = []
        row.append(InlineKeyboardButton(categories[i], callback_data=f"cat_{categories[i]}"))
        if i + 1 < len(categories):
            row.append(InlineKeyboardButton(categories[i+1], callback_data=f"cat_{categories[i+1]}"))
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="اختر التصنيف الذي تهتم به:", reply_markup=reply_markup)


async def show_courses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    category_name = query.data.split("_")[1]
    
    courses_in_category = get_courses_by_category(category_name)
    
    if not courses_in_category:
        await query.edit_message_text(
            text=f"لا توجد دورات متاحة حالياً في تصنيف '{category_name}'.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ رجوع", callback_data="show_categories")]])
        )
        return
        
    keyboard = []
    for i in range(0, len(courses_in_category), 2):
        row = []
        course1 = courses_in_category[i]
        row.append(InlineKeyboardButton(course1[1], callback_data=f"course_{course1[0]}"))
        
        if i + 1 < len(courses_in_category):
            course2 = courses_in_category[i+1]
            row.append(InlineKeyboardButton(course2[1], callback_data=f"course_{course2[0]}"))
        keyboard.append(row)
        
    keyboard.append([InlineKeyboardButton("⬅️ رجوع", callback_data="show_categories")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=f"الدورات المتاحة في تصنيف '{category_name}':", reply_markup=reply_markup)


async def show_course_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    course_id = int(query.data.split("_")[1])
    
    course = get_course_by_id(course_id)
    
    if not course:
        await query.edit_message_text("عذرًا، لم يتم العثور على الدورة.")
        return

    message_text = (
        f"**{course[1]}**\n\n"
        f"**الوصف:** {course[2]}\n"
        f"**السعر:** {course[3]} ريال يمني\n"
        f"**الحالة:** {'✅ متاحة للتسجيل' if course[5] else '❌ غير متاحة حالياً'}"
    )
    
    keyboard = []
    if course[5]:
        keyboard.append([InlineKeyboardButton("📥 التسجيل في الدورة", callback_data=f"register_{course[0]}")])
    
    keyboard.append([InlineKeyboardButton("⬅️ رجوع", callback_data=f"cat_{course[4]}")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=message_text, reply_markup=reply_markup, parse_mode='Markdown')


async def start_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    course_id = int(query.data.split("_")[1])
    context.user_data["registration_data"] = {"course_id": course_id}
    
    await query.edit_message_text("الرجاء إدخال **اسمك الثلاثي** الكامل:")
    return GET_NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = update.message.text
    context.user_data["registration_data"]["name"] = name
    
    keyboard = [
        [
            InlineKeyboardButton("ذكر", callback_data="gender_male"),
            InlineKeyboardButton("أنثى", callback_data="gender_female"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text("الرجاء تحديد **الجنس**:", reply_markup=reply_markup)
    return GET_GENDER


async def get_gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    gender = "ذكر" if query.data == "gender_male" else "أنثى"
    context.user_data["registration_data"]["gender"] = gender
    
    await query.edit_message_text("الرجاء إدخال **عمرك** بالأرقام:")
    return GET_AGE


async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    age = update.message.text
    if not age.isdigit():
        await update.message.reply_text("الرجاء إدخال رقم صحيح للعمر.")
        return GET_AGE
    
    context.user_data["registration_data"]["age"] = int(age)
    await update.message.reply_text("الرجاء إدخال **اسم البلد**:")
    return GET_COUNTRY


async def get_country(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    country = update.message.text
    context.user_data["registration_data"]["country"] = country
    await update.message.reply_text("الرجاء إدخال **اسم المدينة**:")
    return GET_CITY


async def get_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    city = update.message.text
    context.user_data["registration_data"]["city"] = city
    await update.message.reply_text("الرجاء إدخال **رقم هاتفك (للتواصل عبر الواتساب)**:")
    return GET_PHONE


async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    phone = update.message.text
    
    # تحقق من صحة رقم الهاتف (أرقام فقط وطول منطقي)
    if not re.match(r'^\+?[\d\s]{7,15}$', phone):
        await update.message.reply_text("⚠️ عذراً، يرجى إدخال رقم هاتف صحيح (أرقام فقط).")
        return GET_PHONE

    context.user_data["registration_data"]["phone"] = phone
    await update.message.reply_text("الرجاء إدخال **بريدك الإلكتروني**:")
    return GET_EMAIL


async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    email = update.message.text
    
    # تحقق من صحة البريد الإلكتروني باستخدام Regex
    email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if not re.match(email_pattern, email):
        await update.message.reply_text(
            "⚠️ عذراً، البريد الإلكتروني الذي أدخلته غير صالح.\n"
            "يرجى إرساله مرة أخرى (مثال: example@mail.com):"
        )
        return GET_EMAIL

    context.user_data["registration_data"]["email"] = email
    
    registration_data = context.user_data.pop("registration_data")
    registration_data["user_id"] = update.effective_user.id
    registration_data["status"] = "pending"
    registration_data["receipt"] = None

    add_registration(registration_data)
    
    await update.message.reply_text(
        "✅ تم استلام طلبك بنجاح! سيتم مراجعته من قبل الإدارة وسيتم إرسال إشعار لك فوراً.",
        reply_markup=ReplyKeyboardRemove()
    )
    
    admin_ids = get_all_admins()
    if admin_ids:
        course = get_course_by_id(registration_data['course_id'])
        course_name = course[1] if course else 'دورة غير معروفة'
        
        message_to_admin = (
            f"**🔔 طلب تسجيل جديد**\n\n"
            f"**الدورة:** {course_name}\n"
            f"**الاسم:** {registration_data['name']}\n"
            f"**الجنس:** {registration_data['gender']}\n"
            f"**العمر:** {registration_data['age']}\n"
            f"**البلد:** {registration_data['country']}\n"
            f"**المدينة:** {registration_data['city']}\n"
            f"**الهاتف:** {registration_data['phone']}\n"
            f"**البريد:** {registration_data['email']}\n"
            f"**معرف المستخدم:** `{registration_data['user_id']}`"
        )
        
        admin_keyboard = [[InlineKeyboardButton("✅ قبول", callback_data=f"accept_{registration_data['user_id']}_{registration_data['course_id']}"),
                           InlineKeyboardButton("❌ رفض", callback_data=f"reject_{registration_data['user_id']}_{registration_data['course_id']}")]]
        
        for admin_id in admin_ids:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=message_to_admin,
                    reply_markup=InlineKeyboardMarkup(admin_keyboard),
                    parse_mode='Markdown'
                )
            except (Forbidden, BadRequest):
                logging.warning(f"Failed to send registration notification to admin {admin_id}.")

    return ConversationHandler.END


async def handle_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    
    accepted_regs = get_accepted_registrations_for_user(user_id)
    if not accepted_regs:
        return
        
    registration = accepted_regs[0]
    
    if update.message.photo:
        receipt_file_id = update.message.photo[-1].file_id
        update_registration_receipt(user_id, registration[2], receipt_file_id)
        
        admin_ids_to_notify = get_all_admins()
        if admin_ids_to_notify:
            course = get_course_by_id(registration[2])
            caption = (
                f"**🔔 تم استلام إيصال دفع جديد**\n\n"
                f"**الدورة:** {course[1] if course else 'غير معروفة'}\n"
                f"**الاسم:** {registration[3]}\n"
                f"**معرف المستخدم:** `{registration[1]}`"
            )
            for admin_id in admin_ids_to_notify:
                try:
                    await context.bot.send_photo(
                        chat_id=admin_id,
                        photo=receipt_file_id,
                        caption=caption,
                        parse_mode='Markdown'
                    )
                except (Forbidden, BadRequest):
                    logging.warning(f"Failed to send receipt notification to admin {admin_id}.")
            await update.message.reply_text("شكراً لك! تم إرسال إيصالك للمراجعة.")
    else:
        pass
