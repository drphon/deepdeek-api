import openai
import sqlite3
from datetime import datetime

# تابعی برای بارگیری کلید API از فایل پیکربندی
def load_api_key(filename='config.txt'):
    with open(filename, 'r') as file:
        return file.readline().strip()

# ایجاد و اتصال به دیتابیس SQLite
conn = sqlite3.connect('chat_history.db')
c = conn.cursor()

# ایجاد جدول برای ذخیره‌سازی چت‌ها بر اساس تاریخ
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

# تابعی برای ارسال درخواست به API و دریافت محتوا
def generate_content(api_key, prompt):
    client = openai.OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    # تاریخ امروز
    today = datetime.now().strftime("%Y-%m-%d")

    # بارگذاری تاریخچه چت امروز از دیتابیس
    chat_history = load_chat_history(today)
    messages = [{"role": "system", "content": "You are a helpful assistant"}]
    messages.extend([{"role": role, "content": content} for role, content in chat_history])
    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        stream=False
    )

    # بررسی پاسخ و استخراج محتوا
    if response and response.choices:
        assistant_message = response.choices[0].message.content
        save_chat(today, "user", prompt)
        save_chat(today, "assistant", assistant_message)
        return assistant_message
    else:
        print('No content generated.')
        return None

# بارگیری کلید API از فایل پیکربندی
api_key = load_api_key()

# دریافت ورودی از کاربر
while True:
    user_input = input("You: ")
    if user_input.lower() in ["exit", "quit"]:
        break

    # بررسی اگر کاربر بخواهد چت‌های قدیمی را ببیند
    if user_input.startswith("check chat on"):
        date_to_check = user_input.split("check chat on ")[1].strip()
        chat_history = load_chat_history(date_to_check)
        if chat_history:
            print(f"Chat history on {date_to_check}:")
            for role, content in chat_history:
                print(f"{role}: {content}")
        else:
            print(f"No chat history found for {date_to_check}.")
        continue

    # تولید محتوا و ذخیره چت
    response = generate_content(api_key, user_input)
    if response:
        print(f"GPT: {response}")

# بستن اتصال به دیتابیس
conn.close()