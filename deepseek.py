import openai
import sqlite3
from datetime import datetime
import os
import glob

# تابعی برای بارگیری کلید API از فایل پیکربندی
def load_api_key(filename='config.txt'):
    with open(filename, 'r') as file:
        return file.readline().strip()

# ایجاد و اتصال به دیتابیس SQLite
conn = sqlite3.connect('chat_history.db')
c = conn.cursor()

# ایجاد جدول برای ذخیره‌سازی چت‌ها
c.execute('''CREATE TABLE IF NOT EXISTS chats
             (id INTEGER PRIMARY KEY AUTOINCREMENT, 
              date TEXT, 
              role TEXT, 
              content TEXT)''')
conn.commit()

def save_chat(date, role, content):
    """ذخیره‌سازی چت در دیتابیس"""
    c.execute("INSERT INTO chats (date, role, content) VALUES (?, ?, ?)", (date, role, content))
    conn.commit()

def load_chat_history(date):
    """بارگذاری تاریخچه چت از دیتابیس بر اساس تاریخ"""
    c.execute("SELECT role, content FROM chats WHERE date = ?", (date,))
    return c.fetchall()

def load_text_files_from_directory(directory_path):
    """
    خواندن تمام فایل‌های متنی از یک پوشه و تبدیل آنها به فرمت مناسب برای چت
    """
    chat_history = []
    
    # پیدا کردن تمام فایل‌های .txt در پوشه
    text_files = glob.glob(os.path.join(directory_path, "*.txt"))
    
    for file_path in text_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read().strip()
                # فرض می‌کنیم محتوای هر فایل یک مکالمه قبلی است
                # آن را به عنوان یک پیام کاربر و یک پاسخ اضافه می‌کنیم
                chat_history.append({"role": "user", "content": content})
                chat_history.append({"role": "assistant", "content": "I remember this conversation."})
                print(f"فایل خوانده شد: {os.path.basename(file_path)}")
        except Exception as e:
            print(f"خطا در خواندن فایل {file_path}: {str(e)}")
    
    return chat_history

def generate_content(api_key, prompt, previous_conversations=None):
    """تابع اصلی برای تولید محتوا با در نظر گرفتن مکالمات قبلی"""
    client = openai.OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    # تاریخ امروز
    today = datetime.now().strftime("%Y-%m-%d")

    # ایجاد لیست پیام‌ها با system message
    messages = [{"role": "system", "content": "You are a helpful assistant"}]

    # اضافه کردن مکالمات قبلی از فایل‌های متنی (اگر وجود داشته باشد)
    if previous_conversations:
        messages.extend(previous_conversations)

    # اضافه کردن تاریخچه چت امروز از دیتابیس
    chat_history = load_chat_history(today)
    messages.extend([{"role": role, "content": content} for role, content in chat_history])
    
    # اضافه کردن پیام جدید کاربر
    messages.append({"role": "user", "content": prompt})

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            stream=False
        )

        if response and response.choices:
            assistant_message = response.choices[0].message.content
            save_chat(today, "user", prompt)
            save_chat(today, "assistant", assistant_message)
            return assistant_message
        else:
            print('محتوایی تولید نشد.')
            return None
    except Exception as e:
        print(f"خطا در ارتباط با API: {str(e)}")
        return None

def show_menu():
    """نمایش منوی اصلی برنامه"""
    print("\n=== منوی اصلی ===")
    print("1. شروع چت جدید")
    print("2. بارگذاری چت‌های قبلی از پوشه")
    print("3. مشاهده تاریخچه چت برای تاریخ خاص")
    print("4. خروج")
    return input("لطفاً گزینه مورد نظر را انتخاب کنید: ")

def main():
    # بارگیری کلید API
    api_key = load_api_key()
    previous_conversations = None

    while True:
        choice = show_menu()

        if choice == '1':
            # شروع چت جدید
            while True:
                user_input = input("\nYou: ")
                if user_input.lower() in ["exit", "quit", "back"]:
                    break

                response = generate_content(api_key, user_input, previous_conversations)
                if response:
                    print(f"GPT: {response}")

        elif choice == '2':
            # بارگذاری چت‌های قبلی از پوشه
            directory_path = input("\nلطفاً آدرس پوشه حاوی فایل‌های چت را وارد کنید: ")
            if os.path.exists(directory_path):
                previous_conversations = load_text_files_from_directory(directory_path)
                print("چت‌های قبلی با موفقیت بارگذاری شدند.")
            else:
                print("پوشه مورد نظر یافت نشد!")

        elif choice == '3':
            # مشاهده تاریخچه چت
            date_to_check = input("\nتاریخ مورد نظر را وارد کنید (YYYY-MM-DD): ")
            chat_history = load_chat_history(date_to_check)
            if chat_history:
                print(f"\nتاریخچه چت در تاریخ {date_to_check}:")
                for role, content in chat_history:
                    print(f"{role}: {content}")
            else:
                print(f"تاریخچه‌ای برای تاریخ {date_to_check} یافت نشد.")

        elif choice == '4':
            print("برنامه در حال خروج...")
            break

        else:
            print("گزینه نامعتبر! لطفاً دوباره تلاش کنید.")

    # بستن اتصال به دیتابیس
    conn.close()

if __name__ == "__main__":
    main()