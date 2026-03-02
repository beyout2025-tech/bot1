import os
from dotenv import load_dotenv # أضف هذا السطر

load_dotenv() # أضف هذا السطر لتحميل المتغيرات من ملف .env
BOT_TOKEN = os.getenv("BOT_TOKEN")
