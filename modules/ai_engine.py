import streamlit as st
import os
import json
import google.generativeai as genai
from google.ai.generativelanguage import Content, Part
from pydantic import BaseModel
from typing import List

# --- MODELLI DATI ---
class Scene(BaseModel):
    scene_number: int
    voiceover: str
    keyword: str
    duration: int

class AudioSettings(BaseModel):
    pixabay_genre: str  
    pixabay_mood: str   
    voice_speed: str

class VideoScript(BaseModel):
    audio_settings: AudioSettings
    scenes: List[Scene]

def generate_script(topic: str) -> dict:
    
    # 1. Recupero API KEY
    api_key = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
    if not api_key:
        st.error("❌ ERRORE CRITICO: Google API Key non trovata nei secrets o environment.")
        return None

    try:
        # 2. Configurazione Vecchia Scuola (Funziona Sempre)
        genai.configure(api_key=api_key)
        
        # Configurazione Modello
        generation_config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": 8192,
            "response_mime_type": "application/json",
        }

        model = genai.GenerativeModel(
            model_name="gemini-flash-latest",
            generation_config=generation_config,
        )
        
        # 3. Prompt Ingegnerizzato
        system_instruction = """
        You are a Video Director using the OFFICIAL Pixabay API.
        Output MUST be a JSON object following this exact schema.

        PHASE 1: AUDIO TAGGING
        Select ONE Genre: ["ambient", "cinematic", "electronic", "acoustic", "rock", "lofi"]
        Select ONE Mood: ["contemplative", "epic", "happy", "suspense", "relaxing", "melancholic"]

        PHASE 2: VOICE SPEED
        - "-10%" (Sad/Deep), "+15%" (Hype), "+0%" (Normal)

        PHASE 3: VISUAL KEYWORDS
        - Search query for Stock Video. Simple English. 
        - BAD: "Samurai standing in rain"
        - GOOD: "Samurai rain"
        
        STRUCTURE:
        - 1 Scene for atmosphere.
        - 3-5 Scenes for lists.

        JSON SCHEMA:
        {
            "audio_settings": {
                "pixabay_genre": "string",
                "pixabay_mood": "string",
                "voice_speed": "string"
            },
            "scenes": [
                {
                    "scene_number": int,
                    "voiceover": "string",
                    "keyword": "string",
                    "duration": int
                }
            ]
        }
        """
        
        # 4. Chiamata
        full_prompt = f"{system_instruction}\n\nTOPIC: {topic}"
        response = model.generate_content(full_prompt)
        
        if not response.text:
            st.error("❌ Errore AI: Risposta vuota da Gemini.")
            return None
        
        # 5. Parsing JSON Manuale (Più robusto)
        json_data = json.loads(response.text)
        return VideoScript.model_validate(json_data).model_dump()

    except Exception as e:
        # STAMPA L'ERRORE REALE A SCHERMO
        st.error(f"❌ AI ENGINE ERROR: {str(e)}")
        print(f"AI ERROR DETAILS: {e}")
        return None