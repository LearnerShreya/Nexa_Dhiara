import time
import google.generativeai as genai
import speech_recognition as sr
import pyttsx3
import re
import random
from datetime import datetime
from deep_translator import GoogleTranslator

# 🔧 Configure Google Gemini AI (Replace with your API key)
genai.configure(api_key="AIzaSyAa3L56YqsCUNeWHAhVj9YHzUuT4gpxn2I")

# 🎧 Initialize text-to-speech engine
engine = pyttsx3.init()

# 🤖 Chatbot identity
CHATBOT_NAME = "Dhiara"
NICKNAME = "Nexa"

# 🔊 Random responses when waiting for voice input
listening_responses = ["Go ahead!", "I'm ready.", "Yes?", "Listening...", "Tell me!"]

def speak_random_response():
    response = random.choice(listening_responses)
    print(response)
    engine.say(response)
    engine.runAndWait()

# 🎤 Get voice input from the user
def get_voice_input():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        speak_random_response()
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source, timeout=10)
            text = recognizer.recognize_google(audio)
            print("You:", text)
            return text.lower()
        except sr.UnknownValueError:
            print("Sorry, I couldn't understand.")
            engine.say("Sorry, I couldn't understand.")
            engine.runAndWait()
            return None

# 🧙️ Respond when asked about its name
def respond_to_name_query():
    response = f"My name is {CHATBOT_NAME}, but you can also call me {NICKNAME}."
    print(response)
    engine.say(response)
    engine.runAndWait()

# 🤓 Check if input is a mathematical expression
def is_math_expression(text):
    return bool(re.fullmatch(r'[\d+\-*/%^(). ]+', text))

# 🧐 Evaluate math expressions safely
def calculate_math(expression):
    try:
        return eval(expression, {"builtins": {}})
    except Exception:
        return "Invalid calculation."

# 🌍 Translate text using Deep Translator (no `cgi` dependency)
def translate_text(text, dest_lang="en"):
    try:
        return GoogleTranslator(source='auto', target=dest_lang).translate(text)
    except Exception:
        return "Translation unavailable."

# 📊 Analyze the type of question asked
def analyze_question_type(prompt):
    short_questions = ["what", "where", "who", "whom", "whose", "when", "define"]
    detailed_questions = ["how", "why"]
    words = prompt.split()

    word_limit_match = re.search(r'(\d+)\s*(words?|sentences?|paragraphs?)', prompt)
    if word_limit_match:
        return "custom", int(word_limit_match.group(1))

    if words[0] in short_questions:
        return "short", None
    elif words[0] in detailed_questions:
        return "detailed", None
    return "general", None

# 🤖 Chat with Google Gemini AI
def chat_with_gemini(prompt):
    try:
        response_type, word_limit = analyze_question_type(prompt)
        chatbot_reply = None

        if is_math_expression(prompt):
            chatbot_reply = f"The result is {calculate_math(prompt)}"
        elif prompt.startswith("repeat"):
            chatbot_reply = prompt.replace("repeat ", "", 1)
        elif "translate" in prompt:
            words = prompt.split()
            if "to" in words:
                phrase_index = words.index("translate") + 1
                lang_index = words.index("to") + 1

                if lang_index < len(words):
                    phrase = " ".join(words[phrase_index:words.index("to")])
                    lang = words[lang_index]
                    chatbot_reply = translate_text(phrase, lang)
                else:
                    chatbot_reply = "Please specify the target language."
            else:
                chatbot_reply = "Please specify the translation language."
        elif "time" in prompt or "date" in prompt:
            chatbot_reply = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        elif "your name" in prompt or "what's your name" in prompt:
            respond_to_name_query()
            return
        else:
            model = genai.GenerativeModel("gemini-1.5-flash")
            query = f"Answer concisely in 2-3 complete sentences: {prompt}"
            response = model.generate_content(query)
            chatbot_reply = response.text if response.text else "I couldn't generate a response."

        print("Nexa:", chatbot_reply)
        engine.say(chatbot_reply)
        engine.runAndWait()
    except Exception as e:
        print("Error:", e)
        engine.say("I couldn't process that request. Please try again.")
        engine.runAndWait()

# 🔄 Main chatbot loop
def main():
    stop_words = ["exit", "quit", "stop", "terminate", "end", "shutdown", "bye"]
    while True:
        user_input = get_voice_input()
        if user_input:
            if any(word in user_input for word in stop_words):
                print("Goodbye! See you soon.")
                engine.say("Goodbye! See you soon.")
                engine.runAndWait()
                break
            chat_with_gemini(user_input)

# 🚀 Run the chatbot
if __name__ == "__main__":
    main()