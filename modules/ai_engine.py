import streamlit as st
import os
import json
import time
from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import List

# --- DATA MODELS ---
class Scene(BaseModel):
    scene_number: int
    voiceover: str
    keyword: str
    duration: int

class VoiceSettings(BaseModel):
    voice_speed: str

class VideoScript(BaseModel):
    voice_settings: VoiceSettings
    scenes: List[Scene]

def generate_script(topic: str) -> dict:
    api_key = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
    if not api_key:
        st.error("⚠️ API Key missing.")
        return None

    client = genai.Client(http_options={'api_version': 'v1alpha'}, api_key=api_key)
    
    target_schema = {
        "type": "OBJECT",
        "properties": {
            "voice_settings": {
                "type": "OBJECT",
                "properties": { "voice_speed": {"type": "STRING"} },
                "required": ["voice_speed"]
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
        "required": ["voice_settings", "scenes"]
    }

    # --- IL NUOVO PROMPT BASATO SULLA MATRICE DI TAG ---
    system_instruction = """You are the AI assistant for Pexels and Pixabay users. The user provides a text or an idea for a video they want to create. 
        Your task is to leverage your deep knowledge of Pexels and Pixabay video tags to identify the most relevant clips for their request. 
        Based on the user's intent, you must determine the appropriate number of video clips (one or more) and the specific duration for each scene.
        MANDATORY: Return ONLY a valid JSON object that matches the provided schema."""

    # Retry Logic
    max_retries = 3
    attempt = 0
    while attempt < max_retries:
        try:
            response = client.models.generate_content(
                model="gemini-3-flash-preview", 
                contents=f"TOPIC: {topic}. REQUIREMENT: 7 scenes, structured tags (Subject+Action+Env+Style), fast cuts.",
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    thinking_config=types.ThinkingConfig(thinking_level=types.ThinkingLevel.LOW),
                    temperature=1.0, # Alta creatività per variare i soggetti
                    response_mime_type="application/json",
                    response_schema=target_schema 
                )
            )
            
            raw_data = json.loads(response.text)
            if isinstance(raw_data, list): raw_data = raw_data[0]
            return VideoScript.model_validate(raw_data).model_dump()

        except Exception as e:
            if "503" in str(e):
                attempt += 1; time.sleep(2)
                continue
            st.error(f"AI Error: {str(e)}")
            return None
    return None