import streamlit as st
import os
from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import List

# --- MODELLI DATI (PYDANTIC) ---
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

# --- FUNZIONE GENERAZIONE ---
def generate_script(topic: str) -> dict:
    
    # Recupero API Key
    api_key = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
    if not api_key:
        st.error("⚠️ API Key mancante.")
        return None

    try:
        # Inizializzazione Client (Libreria Originale)
        client = genai.Client(api_key=api_key)
        
        # PROMPT INGEGNERIZZATO (Logica Nuova)
        system_instruction = """
        You are a Video Director using the OFFICIAL Pixabay API.
        
        PHASE 1: AUDIO TAGGING (Strictly Official Tags)
        Select ONE Genre and ONE Mood from these lists:
        [GENRES]: "ambient", "cinematic", "electronic", "acoustic", "rock", "lofi"
        [MOODS]: "contemplative", "epic", "happy", "suspense", "relaxing", "melancholic"

        PHASE 2: VOICE SPEED
        - "-10%" (Sad/Deep), "+15%" (Hype), "+0%" (Normal)

        PHASE 3: VISUAL KEYWORDS (Simple Rule)
        - Generate a search query for Stock Video.
        - BAD: "Samurai standing in rain cinematic" (Too complex).
        - GOOD: "Samurai rain" (Perfect).
        
        STRUCTURE:
        - 1 Scene (15s) for atmosphere.
        - 3-5 Scenes for lists.

        OUTPUT: JSON Object matching the schema.
        """
        
        # Schema JSON per la libreria google.genai
        manual_schema = {
            "type": "OBJECT",
            "properties": {
                "audio_settings": {
                    "type": "OBJECT",
                    "properties": {
                        "pixabay_genre": {"type": "STRING", "enum": ["ambient", "cinematic", "electronic", "acoustic", "rock", "lofi"]},
                        "pixabay_mood": {"type": "STRING", "enum": ["contemplative", "epic", "happy", "suspense", "relaxing", "melancholic"]},
                        "voice_speed": {"type": "STRING"}
                    },
                    "required": ["pixabay_genre", "pixabay_mood", "voice_speed"]
                },
                "scenes": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "scene_number": {"type": "INTEGER"},
                            "voiceover": {"type": "STRING"},
                            "keyword": {"type": "STRING"},
                            "duration": {"type": "INTEGER"}
                        },
                        "required": ["scene_number", "voiceover", "keyword", "duration"]
                    }
                }
            },
            "required": ["audio_settings", "scenes"]
        }

        # Chiamata al Modello
        response = client.models.generate_content(
            model="gemini-flash-latest", 
            contents=f"TOPIC: {topic}",
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=manual_schema,
                temperature=0.7
            )
        )

        if not response.text:
            st.error("AI Error: Risposta vuota.")
            return None
        
        # Parsing Diretto
        return VideoScript.model_validate_json(response.text).model_dump()

    except Exception as e:
        # Mostriamo l'errore esatto a schermo per debug
        st.error(f"AI Error: {str(e)}")
        print(f"AI ERROR: {e}")
        return None