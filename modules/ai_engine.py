import streamlit as st
import os
from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import List, Optional

# --- MODELLI DATI ---
class Scene(BaseModel):
    scene_number: int
    voiceover: str
    keyword: str
    duration: int

class AudioSettings(BaseModel):
    # Mapping rigoroso dei parametri Pixabay
    pixabay_genre: str  # Es: "ambient", "cinematic", "lofi"
    pixabay_mood: str   # Es: "contemplative", "melancholic", "epic"
    voice_speed: str    # Es: "+10%", "-5%"

class VideoScript(BaseModel):
    audio_settings: AudioSettings
    scenes: List[Scene]

def generate_script(topic: str) -> Optional[dict]:
    
    api_key = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
    if not api_key: return None

    try:
        client = genai.Client(api_key=api_key)
        
        system_instruction = """
        You are a Director. Create a video plan.

        ---------------------------------------------------------
        PHASE 1: PIXABAY MUSIC MAPPING (STRICT)
        ---------------------------------------------------------
        You MUST select the audio attributes from these exact lists based on the topic:

        1. GENRE (Pick ONE):
           - "ambient" (For voiceovers, deep thoughts)
           - "cinematic" (For epic nature, mountains, drones)
           - "lofi" (For urban, chill, modern)
           - "acoustic" (For happy, bright)

        2. MOOD (Pick ONE):
           - "contemplative" (Thinking, philosophy, pensive)
           - "melancholic" (Sad, lonely, rain)
           - "dreamy" (Beautiful nature, soft)
           - "epic" (Victory, mountains, power)
           - "suspense" (Tension, mystery)
        
        3. VOICE SPEED:
           - "-10%" (Serious/Sad)
           - "+15%" (Hype/Action)
           - "+0%" (Neutral)

        ---------------------------------------------------------
        PHASE 2: VISUALS (One-Shot Rule)
        ---------------------------------------------------------
        - If Atmosphere/Action -> 1 Scene (15s).
        - If List/Story -> 3-5 Scenes.
        - KEYWORDS: [Subject] + [Context]. English Only.

        OUTPUT: Valid JSON only.
        """
        
        manual_schema = {
            "type": "OBJECT",
            "properties": {
                "audio_settings": {
                    "type": "OBJECT",
                    "properties": {
                        "pixabay_genre": {"type": "STRING", "enum": ["ambient", "cinematic", "lofi", "acoustic"]},
                        "pixabay_mood": {"type": "STRING", "enum": ["contemplative", "melancholic", "dreamy", "epic", "suspense"]},
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

        response = client.models.generate_content(
            model="gemini-1.5-flash", 
            contents=f"TOPIC: {topic}",
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=manual_schema,
                temperature=0.5
            )
        )

        if not response.text: return None
        return VideoScript.model_validate_json(response.text).model_dump()

    except Exception as e:
        print(f"AI Error: {e}")
        return None