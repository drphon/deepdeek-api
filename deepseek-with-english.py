import openai
import os

# Function to load API key from config file
def load_api_key(filename='config.txt'):
    with open(filename, 'r') as file:
        return file.readline().strip()

# Function to read text files from a folder
def load_chat_history_from_folder(folder_path):
    chat_history = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".txt"):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                chat_history.append({"role": "user", "content": content})
    return chat_history

# Function to send a request to the API and get content
def generate_content(api_key, prompt, chat_history=None):
    client = openai.OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    if chat_history is None:
        chat_history = []

    # Add the new message to the chat history
    chat_history.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=chat_history,
        stream=False
    )

    # Check the response and extract content
    if response and response.choices:
        assistant_message = response.choices[0].message.content
        chat_history.append({"role": "assistant", "content": assistant_message})
        return assistant_message, chat_history
    else:
        print('No content generated.')
        return None, chat_history

# Load API key from config file
api_key = load_api_key()

# Main menu
def main_menu():
    print("1. Start a new chat")
    print("2. Load previous chats from text files")
    choice = input("Choose an option (1 or 2): ").strip()

    chat_history = []

    if choice == "2":
        folder_path = input("Enter the path to the folder containing text files: ").strip()
        if os.path.isdir(folder_path):
            chat_history = load_chat_history_from_folder(folder_path)
            print(f"{len(chat_history)} previous chats loaded.")
        else:
            print("The provided folder path is invalid.")
            return

    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            break

        response, chat_history = generate_content(api_key, user_input, chat_history)
        if response:
            print(f"GPT: {response}")

# Run the main menu
if __name__ == "__main__":
    main_menu()