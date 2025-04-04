import pyttsx3
import requests
import random
import time
import google.generativeai as genai
import speech_recognition as sr
import re
from langdetect import detect
from datetime import datetime
from googletrans import Translator
from dotenv import load_dotenv
import os

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
w_api_key = WEATHER_API_KEY
# Initialize text-to-speech engine
engine = pyttsx3.init()

# Get available voices
voices = engine.getProperty('voices')

# Select a female voice (prioritizing Zira or Samantha)
for voice in voices:
    if "female" in voice.name.lower() or "Zira" in voice.name or "Samantha" in voice.name:
        engine.setProperty("voice", voice.id)
        break  # Stop after selecting the preferred voice

# Adjust speech speed (slower for better clarity)
engine.setProperty('rate', 155)  # Default is around 200 WPM


def get_weather(city_name):
    # w_api_key = "28e3b5fd214ab042c0c7297ff4f60a65"  # Replace with your OpenWeatherMap API key
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={w_api_key}&units=metric"

    try:
        response = requests.get(url)
        data = response.json()

        if data.get("cod") != 200:
            return f"Sorry, I couldn't find weather information for {city_name}."

        temp = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        humidity = data["main"]["humidity"]
        weather = data["weather"][0]["description"].capitalize()
        wind_speed = data["wind"]["speed"]

        return (
            f"It's currently {weather} in {city_name}. "
            f"The temperature is {temp}°C, feels like {feels_like}°C. "
            f"Humidity is {humidity}% and wind speed is {wind_speed} meters per second."
        )

    except Exception as e:
        return "I'm having trouble fetching the weather right now. Please try again later."



def clean_text(text):
    return re.sub(r'[*#\\{}_$%^&]', '', text)


listening_responses = ["Go ahead!", "I'm ready.", "Yes?", "Listening...", "Tell me!"]


def speak_random_response():
    response = random.choice(listening_responses)
    print(response)
    engine.say(response)
    engine.runAndWait()


def get_voice_input():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        speak_random_response()
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source, timeout=10)
        try:
            text = recognizer.recognize_google(audio)
            print("🗣  User:", text)
            return text.lower()
        except:
            print("Sorry, I couldn't understand.")
            engine.say("Sorry, I couldn't understand.")
            engine.runAndWait()
    return None


def is_math_expression(text):
    return bool(re.fullmatch(r'[\d+\-*/%^(). ]+', text))

def calculate_math(expression):
    try:
        return eval(expression, {"builtins": {}})
    except Exception:
        return "Invalid calculation."


def translate_text(text, dest_lang="en"):
    try:
        translator = Translator()
        translated = translator.translate(text, dest=dest_lang)
        return translated.text
    except Exception:
        return "Translation unavailable."


def chat_with_gemini(prompt):
    try:
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
        elif "weather" in prompt:
            match = re.search(r'weather(?:\s+(?:in|at|of))?\s+([a-zA-Z\s]+)', prompt)

            if match:
                city = match.group(2).strip()
                chatbot_reply = get_weather(city)
            else:
                # Safe fallback: extract last word of prompt as possible city
                words = prompt.strip().split()
                if words:
                    possible_city = words[-1]
                    chatbot_reply = get_weather(possible_city)
                else:
                    chatbot_reply = "Please specify the city for weather information."
        else:
            model = genai.GenerativeModel("gemini-1.5-flash")
            # Random sentence limit between 1 to 7
            sentence_limit = random.randint(1, 7)
            query = f"Answer concisely in {sentence_limit} complete sentences: {prompt}"

            response = model.generate_content(query)
            chatbot_reply = clean_text(response.text)

        # Ensure response has proper sentence completion
        chatbot_reply = complete_sentences(chatbot_reply, sentence_limit)

        print("🤖 Dhiara:", chatbot_reply)
        engine.say(chatbot_reply)
        engine.runAndWait()
    except Exception as e:
        print("Error:", e)
        engine.say("I couldn't process that request. Please try again.")
        engine.runAndWait()


# Function to complete sentences properly
def complete_sentences(text, sentence_limit):
    sentences = re.split(r'(?<=[.!?])\s+', text)  # Split by full stops, exclamation, or question marks
    return ' '.join(sentences[:sentence_limit])  # Keep only the required number of sentences


def main():
    stop_words = {"exit", "quit", "stop", "terminate", "end", "shutdown", "bye"}
    
    while True:
        user_input = get_voice_input()
        if user_input:
            user_input = user_input.lower().strip()
            words = set(user_input.split())

            if stop_words & words:
                print("Goodbye! See you soon.")
                engine.say("Goodbye! See you soon.")
                engine.runAndWait()
                break

            elif "hello" in words:
                print("Dhiara: Hello, nice to meet you!")
                engine.say("Hello, nice to meet you!")
                engine.runAndWait()

            elif "your name" in user_input or "who are you" in user_input:
                print("Dhiara: My name is Dhiara! I am your AI assistant.")
                engine.say("My name is Dhiara! I am your AI assistant.")
                engine.runAndWait()

            else:
                chat_with_gemini(user_input)


if __name__ == "__main__":
    main()