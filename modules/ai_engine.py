import streamlit as st
import os
from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import List, Optional

# --- MODELLI DATI (Output Strutturato) ---
class Scene(BaseModel):
    scene_number: int
    voiceover: str
    keyword: str
    duration: int

class AudioSettings(BaseModel):
    music_query: str     # Es: "Epic Orchestral", "Sad Piano", "Cyberpunk"
    voice_speed: str     # Es: "+10%" (Veloce), "-10%" (Lento), "+0%" (Normale)

class VideoScript(BaseModel):
    audio_settings: AudioSettings
    scenes: List[Scene]

# --- FUNZIONE GENERAZIONE ---
def generate_script(topic: str) -> Optional[dict]:
    
    api_key = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
    if not api_key:
        st.error("⚠️ Errore: Chiave API mancante.")
        return None

    try:
        client = genai.Client(api_key=api_key)
        
        # --- IL NUOVO PROMPT "AUTONOMOUS DIRECTOR" ---
        system_instruction = """
        You are an AI Video Director. 
        Your goal is to convert a user Topic into a full production plan (Script, Visuals, Audio).

        ---------------------------------------------------------
        PHASE 1: AUDIO & MOOD ANALYSIS
        ---------------------------------------------------------
        Analyze the emotion of the topic to set the audio atmosphere:
        1. Music Query: Generate a specific search term for Pixabay Audio.
           - Sad/Emotional -> "Sad Piano", "Cinematic Emotional"
           - Tech/Future -> "Synthwave", "Cyberpunk", "Technology"
           - Nature/Calm -> "Forest Ambient", "Meditation"
           - Action/Hype -> "Epic Rock", "Action Trailer", "Phonk"
        
        2. Voice Speed: Set the speaking rate for the narrator.
           - Serious/Dramatic -> "-10%" or "-15%" (Slow)
           - Energetic/TikTok -> "+10%" or "+20%" (Fast)
           - Educational/Normal -> "+0%"

        ---------------------------------------------------------
        PHASE 2: VISUAL STRUCTURE (The "One-Shot" Rule)
        ---------------------------------------------------------
        Determine the number of scenes based on the content type:
        
        👉 TYPE A: ATMOSPHERE / SINGLE ACTION
        - If the user describes a vibe or a continuous action (e.g., "Rain on window", "Girl walking in city").
        - OUTPUT: 1 Scene (15-20 seconds).
        - VISUAL: One continuous, high-quality shot.
        
        👉 TYPE B: NARRATIVE / LIST
        - If the user asks for a story, a list of tips, or contrasting ideas.
        - OUTPUT: 3 to 5 Scenes (3-5 seconds each).
        - VISUAL: Dynamic cuts, visual consistency (same environment).

        ---------------------------------------------------------
        PHASE 3: SEARCH TAG OPTIMIZATION (Pexels Protocol)
        ---------------------------------------------------------
        - KEYWORDS: Must be [Subject] + [Context]. English Only.
        - NO ABSTRACTS: Do not use "Success", use "Man on mountain top".
        - NO TECHNICALS: Do not use "4k", "Vertical".

        OUTPUT: Valid JSON matching the schema.
        """
        
        user_prompt = f"TOPIC: {topic}"

        # Schema JSON per forzare l'output strutturato
        manual_schema = {
            "type": "OBJECT",
            "properties": {
                "audio_settings": {
                    "type": "OBJECT",
                    "properties": {
                        "music_query": {"type": "STRING"},
                        "voice_speed": {"type": "STRING"}
                    },
                    "required": ["music_query", "voice_speed"]
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

        response = client.models.generate_content(
            model="gemini-flash-latest", 
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=manual_schema,
                temperature=0.7
            )
        )

        if not response.text: return None
        
        # Restituiamo il dizionario completo (Settings + Scene)
        return VideoScript.model_validate_json(response.text).model_dump()

    except Exception as e:
        print(f"AI Error: {e}")
        return None