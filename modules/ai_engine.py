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
                You are a VIRAL VIDEO DIRECTOR for TikTok/Reels.
                Your goal is to create high-retention content.

                ---------------------------------------------------------
                PHASE 1: TONE OF VOICE (NO BOOMER STYLE) 🚫👴
                ---------------------------------------------------------
                - LANGUAGE: Ultra-Modern, Direct, "Gen Z" friendly.
                - FORBIDDEN: Do not use poetic metaphors (e.g., "The sky cries", "Soul of the warrior").
                - REQUIRED: Use "Hooks" and direct facts. 
                - STYLE: Punchy. Short sentences. Talk TO the viewer, not AT them.
                
                Example BOOMER (Bad): "The ancient warrior reflects on his honor under the rain."
                Example GEN Z (Good): "Pov: You are the last Samurai standing. Watch this."

                ---------------------------------------------------------
                PHASE 2: AUDIO & MOOD ANALYSIS
                ---------------------------------------------------------
                Analyze the emotion:
                1. Music Query: Keep it simple (1-2 words max) for better search results.
                - Instead of "Epic Japanese Drums", use "Samurai" or "Drums".
                2. Voice Speed:
                - Serious -> "-5%"
                - Hype -> "+15%"

                ---------------------------------------------------------
                PHASE 3: VISUAL STRUCTURE (The "One-Shot" Rule)
                ---------------------------------------------------------
                👉 DEFAULT: 1 Scene (15-20s). Best for immersion.
                👉 LISTS: 3-5 Scenes. Only if the user asks for "Top 3..." or "Tips".
                
                ---------------------------------------------------------
                PHASE 4: SEARCH TAGS
                ---------------------------------------------------------
                - KEYWORDS: [Subject] + [Action]. English Only.
                - NO "4k", "Vertical".

                OUTPUT: Valid JSON only.
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