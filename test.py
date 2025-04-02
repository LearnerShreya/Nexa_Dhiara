import serial
import time
import google.generativeai as genai
import speech_recognition as sr
import pyttsx3
import re
import random
from langdetect import detect
from datetime import datetime
import requests
from googletrans import Translator


# Initialize Arduino (Change ports as needed)
arduino1 = serial.Serial('COM3', 9600)  # Primary Arduino for chatbot control
arduino2 = serial.Serial('COM4', 9600)  # Secondary Arduino for servo motor control
time.sleep(2)  # Wait for Arduino to initialize

engine = pyttsx3.init()
genai.configure(api_key="AIzaSyAa3L56YqsCUNeWHAhVj9YHzUuT4gpxn2I")


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
            print("You:", text)
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


def analyze_question_type(prompt):
    short_questions = ["what", "where", "who", "whom", "whose", "when", "define"]
    detailed_questions = ["how", "why"]
    words = prompt.split()

    # Detect if user specifies a length limit (e.g., "Explain in 50 words")
    word_limit_match = re.search(r'(\d+)\s*(words|sentences|paragraphs?)', prompt)
    if word_limit_match:
        return "custom", int(word_limit_match.group(1))  # Returns "custom" type with the word limit

    if words[0] in short_questions:
        return "short", None
    elif words[0] in detailed_questions:
        return "detailed", None
    return "general", None


def chat_with_gemini(prompt):
    try:


        response_type = analyze_question_type(prompt)

        # Detect word limit in user query
        word_limit_match = re.search(r'\b(\d+)\s*(words?|lines?)\b', prompt)
        word_limit = int(word_limit_match.group(1)) if word_limit_match else None  # None means default short answer
        arduino1.write(b'1')
        time.sleep(0.1)

        arduino2.write(b'1')
        time.sleep(0.1)
        chatbot_reply = None

        if is_math_expression(prompt):
            chatbot_reply = f"The result is {calculate_math(prompt)}"
        elif prompt.startswith("repeat"):
            chatbot_reply = prompt.replace("repeat ", "", 1)  # Extract the phrase after 'repeat'
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
        else:
            model = genai.GenerativeModel("gemini-1.5-flash")

            # Formulate query based on response type
            if word_limit:
                query = f"Give a detailed answer in about {word_limit} words: {prompt}"
            else:
                query = f"Answer concisely in 2-3 complete sentences: {prompt}"

            response = model.generate_content(query)
            chatbot_reply = clean_text(response.text)

        # Ensure response has proper sentence completion
        chatbot_reply = complete_sentences(chatbot_reply, word_limit)

        print("Nexa:", chatbot_reply)
        engine.say(chatbot_reply)
        engine.runAndWait()
        arduino1.write(b'0')
        time.sleep(0.1)

        arduino2.write(b'0')
        time.sleep(0.1)
    except Exception as e:
        print("Error:", e)
        engine.say("I couldn't process that request. Please try again.")
        engine.runAndWait()


# Function to complete sentences without abrupt cutting
def complete_sentences(text, word_limit):
    sentences = re.split(r'(?<=[.!?])\s+', text)  # Split by full stops, exclamation, or question marks
    selected_sentences = []
    word_count = 0

    for sentence in sentences:
        words_in_sentence = len(sentence.split())
        if word_limit and (word_count + words_in_sentence > word_limit):
            break  # Stop if adding this sentence exceeds the word limit
        selected_sentences.append(sentence)
        word_count += words_in_sentence
        if not word_limit and len(selected_sentences) >= 3:  # Default: Max 3 sentences
            break

    return ' '.join(selected_sentences)


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
            if "hello" in user_input:
                print("Nexa: Hello, nice to meet you!")
                engine.say("Hello, nice to meet you!")
                engine.runAndWait()
            else:
                chat_with_gemini(user_input)


if __name__ == "__main__":
    main()