# db_manager.py
import sqlite3
import json

DB_FILE = "db.sqlite"
DEV_ID = 873158772

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # جدول المستخدمين
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY
        )
    """)
    
    # جدول المديرين
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY
        )
    """)

    # جدول التصنيفات
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            name TEXT PRIMARY KEY
        )
    """)
    
    # جدول الدورات
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY,
            name TEXT,
            description TEXT,
            price REAL,
            category TEXT,
            active INTEGER
        )
    """)
    
    # جدول التسجيلات
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            course_id INTEGER,
            name TEXT,
            gender TEXT,
            age INTEGER,
            country TEXT,
            city TEXT,
            phone TEXT,
            email TEXT,
            status TEXT,
            receipt TEXT
        )
    """)
    
    # إضافة المطور الرئيسي كمدير إذا لم يكن موجودًا
    cursor.execute("SELECT id FROM admins WHERE id=?", (DEV_ID,))
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO admins (id) VALUES (?)", (DEV_ID,))

    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users")
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users

def get_all_admins():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM admins")
    admins = [row[0] for row in cursor.fetchall()]
    conn.close()
    return admins

def is_admin(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM admins WHERE id=?", (user_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0

def add_user(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (id) VALUES (?)", (user_id,))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def add_admin(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO admins (id) VALUES (?)", (user_id,))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False
        
def remove_admin(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM admins WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

def get_all_categories():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM categories")
    categories = [row[0] for row in cursor.fetchall()]
    conn.close()
    return categories

def add_category(name):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO categories (name) VALUES (?)", (name,))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def delete_category(name):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM categories WHERE name=?", (name,))
    conn.commit()
    conn.close()

def get_courses_by_category(category):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM courses WHERE category=? AND active=1", (category,))
    courses = cursor.fetchall()
    conn.close()
    return courses

def get_all_courses():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM courses")
    courses = cursor.fetchall()
    conn.close()
    return courses

def get_course_by_id(course_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM courses WHERE id=?", (course_id,))
    course = cursor.fetchone()
    conn.close()
    return course

def add_course(course_data):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO courses (name, description, price, category, active) VALUES (?, ?, ?, ?, ?)",
                   (course_data['name'], course_data['description'], course_data['price'], course_data['category'], 1))
    conn.commit()
    last_id = cursor.lastrowid
    conn.close()
    return last_id

def delete_course(course_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM courses WHERE id=?", (course_id,))
    conn.commit()
    conn.close()

def update_course_field(course_id, field, new_value):
    # أضف هذا التحقق لضمان أن اسم الحقل آمن
    allowed_fields = ["name", "description", "price", "category", "active"]
    if field not in allowed_fields:
        raise ValueError("Invalid field name")

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # استخدام الاستعلام البارامتري للحقل القيمة
    query = f"UPDATE courses SET {field}=? WHERE id=?" 
    cursor.execute(query, (new_value, course_id))
    conn.commit()
    conn.close()

    
def get_stats():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    num_users = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM courses")
    num_courses = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM admins")
    num_admins = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM registrations WHERE status='pending'")
    num_pending = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM registrations WHERE status='accepted'")
    num_accepted = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM registrations WHERE status='rejected'")
    num_rejected = cursor.fetchone()[0]
    conn.close()
    return {
        "num_users": num_users,
        "num_courses": num_courses,
        "num_admins": num_admins,
        "num_pending": num_pending,
        "num_accepted": num_accepted,
        "num_rejected": num_rejected
    }
    
    
def add_registration(reg_data):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO registrations (user_id, course_id, name, gender, age, country, city, phone, email, status, receipt) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                   (reg_data['user_id'], reg_data['course_id'], reg_data['name'], reg_data['gender'], reg_data['age'], reg_data['country'], reg_data['city'], reg_data['phone'], reg_data['email'], reg_data['status'], reg_data['receipt']))
    conn.commit()
    conn.close()
    
def get_pending_registration(user_id, course_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM registrations WHERE user_id=? AND course_id=? AND status='pending'", (user_id, course_id))
    reg = cursor.fetchone()
    conn.close()
    return reg

def update_registration_status(user_id, course_id, new_status):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE registrations SET status=? WHERE user_id=? AND course_id=? AND status='pending'", (new_status, user_id, course_id))
    conn.commit()
    conn.close()

def update_registration_receipt(user_id, course_id, receipt_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE registrations SET receipt=? WHERE user_id=? AND course_id=? AND status='accepted'", (receipt_id, user_id, course_id))
    conn.commit()
    conn.close()

def get_accepted_registration(user_id, course_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM registrations WHERE user_id=? AND course_id=? AND status='accepted'", (user_id, course_id))
    reg = cursor.fetchone()
    conn.close()
    return reg

def get_accepted_registrations_for_user(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM registrations WHERE user_id=? AND status='accepted'", (user_id,))
    regs = cursor.fetchall()
    conn.close()
    return regs
