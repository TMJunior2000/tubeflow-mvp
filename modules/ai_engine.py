import streamlit as st
import os
from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import List

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
    api_key = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
    if not api_key: return None

    try:
        client = genai.Client(api_key=api_key)
        
        system_instruction = """
        You are a TikTok Video Director.

        PHASE 1: AUDIO (Pixabay Strict)
        - GENRE: Choose ONE ["ambient", "cinematic", "lofi", "acoustic"]
        - MOOD: Choose ONE ["contemplative", "melancholic", "dreamy", "epic", "suspense"]
        - SPEED: "-10%" (Sad/Deep), "+15%" (Hype), "+0%" (Normal)

        PHASE 2: VISUALS (The "Lobotomy" Rule)
        - KEYWORDS MUST BE STUPID SIMPLE. 2-3 WORDS MAX.
        - BAD: "Samurai warrior solitary under heavy rain cinematic" (Too long, returns 0 results).
        - GOOD: "Samurai rain" (Perfect).
        - GOOD: "Katana" (Perfect).
        - NEVER use adjectives like "cinematic", "4k", "detailed". Just the SUBJECT.

        PHASE 3: STRUCTURE
        - If Atmosphere -> 1 Scene (15s).
        - If List -> 3-5 Scenes.

        OUTPUT: JSON only.
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
        return None