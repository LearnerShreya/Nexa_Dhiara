import re
import speech_recognition as sr
import pyttsx3
from deep_translator import GoogleTranslator
from langdetect import detect_langs, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException
import google.generativeai as genai

# Configure Gemini API
genai.configure(api_key="AIzaSyBxRIDftFnItrLZbYJl56zpMmK6x6w-E34")

# Ensure consistent language detection
DetectorFactory.seed = 0  

# Initialize pyttsx3 for speech
engine = pyttsx3.init()
engine.setProperty("rate", 170)  # Adjust speech speed

def clean_text(text):
    """Removes non-text elements like URLs, code blocks, and special characters."""
    text = re.sub(r"http\S+|www\S+", "", text)  # Remove URLs
    text = re.sub(r"\[.*?\]|\{.*?\}|\(.*?\)", "", text)  # Remove bracketed content
    text = re.sub(r"[^\w\s.,!?]", "", text)  # Keep only readable text
    text = text.strip()
    return text if text else "I couldn't process that correctly."

def speak(text, lang="en"):
    """Speaks only cleaned text in the correct language."""
    cleaned_text = clean_text(text)
    engine.say(cleaned_text)
    engine.runAndWait()

def detect_language(text):
    """Detects the most probable language with confidence threshold."""
    try:
        lang_probs = detect_langs(text)
        top_lang, confidence = lang_probs[0].lang, lang_probs[0].prob

        return top_lang if confidence >= 0.7 else "en"
    except LangDetectException:
        return "en"  # Default to English if detection fails

def translate_text(text, target_lang):
    """Translates text to the target language, ensuring consistency."""
    try:
        return GoogleTranslator(source="auto", target=target_lang).translate(text)
    except Exception:
        return text  # Return original text if translation fails

def get_gemini_response(prompt, target_lang="en"):
    """Call Google Gemini API, clean response, and ensure single-language translation."""
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        response_text = clean_text(response.text.strip())  # Clean AI response
        return translate_text(response_text, target_lang)  # Translate to single language
    except Exception:
        return "I'm sorry, but I couldn't process your request."

def get_response(user_input):
    """Detects language, calls Gemini API, translates response, and speaks it."""
    
    detected_lang = detect_language(user_input)
    response_translated = get_gemini_response(user_input, detected_lang)

    speak(response_translated, detected_lang)  # Speak response in the detected language
    return response_translated

def listen_and_respond():
    """Continuously listens and responds using Gemini AI."""
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        print("🎙 Listening... (Say 'stop' or 'exit' to end)")
        recognizer.adjust_for_ambient_noise(source)  
        
        while True:
            try:
                print("\n🔴 Speak now...")
                audio = recognizer.listen(source)
                user_input = recognizer.recognize_google(audio).strip()
                print(f"🗣 User: {user_input}")

                if user_input.lower() in ["stop", "exit", "quit"]:
                    print("👋 Exiting... Goodbye!")
                    speak("Goodbye! Have a great day!", "en")
                    break

                reply = get_response(user_input)
                print(f"🤖 Dhiara: {reply}")

            except sr.UnknownValueError:
                print("❌ Sorry, I couldn't understand. Please try again.")
            except sr.RequestError:
                print("⚠️ Speech Recognition API error.")

# **Play the welcome message when the assistant starts**
speak("Hello! I'm Dhiara. How can I assist you?", "en")

# Start continuous listening
listen_and_respond()
