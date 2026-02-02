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
    # Questi devono corrispondere ai filtri API di Pixabay
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
        You are a Video Director using the official Pixabay Audio API.

        PHASE 1: AUDIO TAGGING (Strictly Official Tags)
        Select ONE Genre and ONE Mood from the lists below to match the topic.
        
        [GENRES]
        - "ambient" (Background, drone, deep)
        - "cinematic" (Orchestral, movie scores)
        - "electronic" (Modern, beats)
        - "acoustic" (Soft, guitar, piano)
        - "rock" (Energy, action)

        [MOODS]
        - "contemplative" (Thinking, sad, slow)
        - "epic" (Battle, victory, fast)
        - "happy" (Positive, bright)
        - "suspense" (Dark, tension)
        - "relaxing" (Calm, nature)

        PHASE 2: VISUALS
        - Create 1 Scene (15s) for atmosphere/action.
        - Create 3-5 Scenes for lists/stories.
        - KEYWORDS: Simple English subject (e.g., "Samurai rain").

        OUTPUT: Valid JSON only.
        """
        
        manual_schema = {
            "type": "OBJECT",
            "properties": {
                "audio_settings": {
                    "type": "OBJECT",
                    "properties": {
                        "pixabay_genre": {"type": "STRING", "enum": ["ambient", "cinematic", "electronic", "acoustic", "rock"]},
                        "pixabay_mood": {"type": "STRING", "enum": ["contemplative", "epic", "happy", "suspense", "relaxing"]},
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