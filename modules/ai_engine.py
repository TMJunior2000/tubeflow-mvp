import streamlit as st
import os
from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import List, Optional

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

def generate_script(topic: str) -> Optional[dict]:
    api_key = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
    if not api_key: return None

    try:
        client = genai.Client(api_key=api_key)
        
        system_instruction = """
        You are a Video Director using the OFFICIAL Pixabay API.

        PHASE 1: AUDIO TAGGING (Strictly Official Tags)
        Select ONE Genre and ONE Mood:
        [GENRES]: "ambient", "cinematic", "electronic", "acoustic", "rock", "lofi"
        [MOODS]: "contemplative", "epic", "happy", "suspense", "relaxing", "melancholic"

        PHASE 2: VOICE SPEED
        - "-10%" (Sad/Deep), "+15%" (Hype), "+0%" (Normal)

        PHASE 3: VISUAL KEYWORDS (The Lobotomy Rule)
        - You must generate a search query for Stock Video.
        - BAD: "Samurai warrior standing in rain cinematic" (Too complex, returns 0 results).
        - GOOD: "Samurai rain" (Perfect).
        - GOOD: "Cyberpunk city" (Perfect).
        
        STRUCTURE:
        - 1 Scene (15s) if it's a mood/atmosphere.
        - 3-5 Scenes if it's a list/tutorial.

        OUTPUT: Valid JSON only.
        """
        
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

        response = client.models.generate_content(
            model="gemini-flash-latest", 
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