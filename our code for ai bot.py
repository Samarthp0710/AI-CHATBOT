import os
import warnings
import google.generativeai as genai
from gtts import gTTS
from langdetect import detect
import speech_recognition as sr
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
import pygame
import io
import time

# Suppress Warnings
warnings.filterwarnings("ignore")

# API Key - Replace with your actual API key or use environment variable
API_KEY = "AIzaSyAwnVLm-zIyR_FCl9VFqdLXQ3Weu8N9y7A"
if not API_KEY or API_KEY != "AIzaSyAwnVLm-zIyR_FCl9VFqdLXQ3Weu8N9y7A":
    raise ValueError("Missing valid API Key! Set GOOGLE_API_KEY as an environment variable.")

# Configure Gemini API
genai.configure(api_key=API_KEY)

# Set up LangChain with Gemini
llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", google_api_key=API_KEY)

# Define memory to retain chat history
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# Define a prompt template for Kairo, the universal language AI
prompt = PromptTemplate(
    input_variables=["chat_history", "user_input", "detected_language"],
    template="""You are Kairo, an advanced AI guide created to assist in communication across all languages and cultures. 

    Your key capabilities:
    - You respond in EXACTLY the same language the user speaks to you
    - You maintain perfect fluency and natural expression in ANY language
    - You understand cultural context and nuances specific to each language
    - You adapt your responses to be culturally appropriate
    
    Your communication style:  
    - Formal yet warm
    - Clear and concise
    - Natural and conversational
    - Include occasional cultural references or sayings appropriate to the language
    
    The user's detected language code is: {detected_language}
    
    Chat history:  
    {chat_history}  
    
    User: {user_input}
    
    Respond ONLY in the same language as the user input. Do not translate or include any language tags.
    
    Kairo:"""
)

# Function to load memory history
def get_chat_history(_):
    return memory.load_memory_variables({}).get("chat_history", "")

# Create the chatbot chain
def get_response(user_input, detected_lang):
    return chat_chain.invoke({
        "user_input": user_input,
        "detected_language": detected_lang
    })

# Initialize pygame mixer for audio playback
pygame.mixer.init()

# Improved Speech Recognition with retry and language options
def listen_for_speech(language=""):
    recognizer = sr.Recognizer()
    
    # Set recognition parameters for better accuracy
    recognizer.energy_threshold = 300  # Increase sensitivity
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.8  # Shorter pause to detect end of speech
    
    max_attempts = 3
    attempt = 0
    
    while attempt < max_attempts:
        with sr.Microphone() as source:
            print(f"Listening (Attempt {attempt+1}/{max_attempts})...")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = recognizer.listen(source, timeout=10, phrase_time_limit=15)
                
                print("Recognizing...")
                
                # Try with language preference if specified
                if language and language != "auto":
                    try:
                        text = recognizer.recognize_google(audio, language=language)
                        print(f"You said: {text}")
                        return text
                    except:
                        pass  # Fall back to auto-detection if specific language fails
                
                # Auto language detection
                text = recognizer.recognize_google(audio)
                print(f"You said: {text}")
                return text
                
            except sr.WaitTimeoutError:
                print("No speech detected. Please try again.")
            except sr.UnknownValueError:
                print("Could not understand audio. Please speak more clearly.")
            except sr.RequestError as e:
                print(f"Recognition service error: {e}")
                break  # Exit on service error
                
        attempt += 1
    
    print("Voice recognition unsuccessful. Please try again.")
    return ""

# Enhanced language detection
def detect_language(text):
    try:
        # Robust detection for short phrases
        if len(text.split()) <= 3:
            # For very short inputs, we need more context
            # This is a simple approach - you might want to use a more sophisticated method
            words = text.lower().split()
            
            # Simple keyword checking for common words in different languages
            # Expand this dictionary with more languages and common words as needed
            language_markers = {
                'en': ['hi', 'hello', 'the', 'is', 'and', 'what', 'who', 'how'],
                'es': ['hola', 'como', 'qué', 'el', 'la', 'es', 'y', 'por'],
                'fr': ['bonjour', 'salut', 'le', 'la', 'est', 'et', 'qui', 'comment'],
                'de': ['hallo', 'guten', 'der', 'die', 'das', 'ist', 'und', 'wie'],
                'hi': ['नमस्ते', 'कैसे', 'हो', 'क्या', 'है', 'और', 'कौन', 'कैसा'],
                'ta': ['வணக்கம்', 'எப்படி', 'நான்', 'நீங்கள்', 'என்ன', 'மற்றும்'],
                'kn': ['ನಮಸ್ಕಾರ', 'ಹೇಗೆ', 'ನಾನು', 'ನೀವು', 'ಏನು', 'ಮತ್ತು'],
                'te': ['నమస్కారం', 'ఎలా', 'నేను', 'మీరు', 'ఏమి', 'మరియు']
            }
            
            for word in words:
                for lang, markers in language_markers.items():
                    if word in markers:
                        return lang
        
        # Standard language detection for longer phrases
        return detect(text)
    except:
        return 'en'  # Default to English if detection fails

# Improved Text-to-Speech with enhanced pronunciation
def text_to_speech(text, lang_code='en'):
    if not text.strip():
        return
        
    try:
        # Map language codes to more specific locale codes for better pronunciation
        tld_map = {
            'en': 'com',       # US English
            'en-uk': 'co.uk',  # UK English
            'en-au': 'com.au', # Australian English
            'es': 'es',        # Spanish
            'fr': 'fr',        # French
            'de': 'de',        # German
            'hi': 'co.in',     # Hindi
            'ta': 'co.in',     # Tamil 
            'kn': 'co.in',     # Kannada
            'te': 'co.in',     # Telugu
            'ja': 'co.jp',     # Japanese
            'ko': 'co.kr',     # Korean
            'zh': 'com.hk',    # Chinese
            'ru': 'ru',        # Russian
            'ar': 'ae',        # Arabic
            'pt': 'com.br',    # Portuguese
            'it': 'it',        # Italian
        }
        
        # Get the TLD based on language or default to .com
        tld = tld_map.get(lang_code, 'com')
        
        # Create gTTS object with appropriate settings for better pronunciation
        tts = gTTS(text=text, lang=lang_code, tld=tld, slow=False)
        
        # Save to in-memory file
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        
        # Play directly
        pygame.mixer.music.load(fp)
        pygame.mixer.music.play()
        
        # Wait for playback to finish
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
            
    except Exception as e:
        print(f"Text-to-Speech Error: {e}")
        print(f"Response text: {text}")

# Initialize the chat chain
chat_chain = (
    RunnablePassthrough.assign(chat_history=get_chat_history) 
    | prompt 
    | llm
)

# Chatbot Function with improved voice interaction
def chatbot():
    # Initial greeting in English
    welcome_message = "Greetings, I am Kairo, your multilingual AI guide. I can understand and respond in any language you speak to me. How may I assist you today?"
    print(f"Kairo: {welcome_message}")
    text_to_speech(welcome_message, 'en')
    
    # Store last detected language for consistency
    current_language = 'en'
    
    while True:
        # Use last detected language to improve recognition
        user_input = listen_for_speech(current_language).strip()
        
        if not user_input:
            continue
            
        # Detect language from user input
        detected_lang = detect_language(user_input)
        current_language = detected_lang  # Update current language
        
        # Check for exit commands in multiple languages
        exit_phrases = [
            "exit", "quit", "bye", "goodbye", "stop",  # English
            "salir", "adiós", "chao", "hasta luego",   # Spanish
            "sortir", "au revoir", "adieu",            # French
            "beenden", "tschüss", "auf wiedersehen",   # German
            "अलविदा", "बाय", "निकास",                  # Hindi
            "வெளியேறு", "பிரியாவிடை", "வணக்கம்",      # Tamil
            "ನಿರ್ಗಮಿಸು", "ವಿದಾಯ", "ಹೋಗ್ತಿನಿ",          # Kannada
            "నిష్క్రమించు", "వీడ్కోలు", "బై"           # Telugu
        ]
        
        if any(exit_word in user_input.lower() for exit_word in exit_phrases):
            # Create a culturally appropriate farewell in the detected language
            response = get_response(f"Say a warm and culturally appropriate farewell in this language", detected_lang)
            farewell = response.content
            
            print(f"Kairo: {farewell}")
            text_to_speech(farewell, detected_lang)
            break
        
        # Get response in detected language
        response = get_response(user_input, detected_lang)
        kairo_response = response.content
        
        # Print and speak response
        print(f"Kairo: {kairo_response}")
        text_to_speech(kairo_response, detected_lang)
        
        # Save to memory
        memory.save_context({"input": user_input}, {"output": kairo_response})

# Run the chatbot when the script is executed directly
if _name_ == "_main_":
    chatbot()
