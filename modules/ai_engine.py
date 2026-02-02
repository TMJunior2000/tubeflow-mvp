import streamlit as st
import os
import json
import time
from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import List

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
    client = genai.Client(http_options={'api_version': 'v1alpha'}, api_key=api_key)
    
    target_schema = {
        "type": "OBJECT",
        "properties": {
            "voice_settings": {"type": "OBJECT", "properties": {"voice_speed": {"type": "STRING"}}, "required": ["voice_speed"]},
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

    system_instruction = """
    You are TubeFlow v3 "Visual Architect". Your goal is extreme visual coherence and high retention.

    --- RULE 1: THE DOPAMINE LIMITER (CRITICAL) ---
    - Every scene duration MUST be an INTEGER between 2 and 4 seconds.
    - NEVER exceed 4 seconds. Speed is life for retention.

    --- RULE 2: VISUAL COHERENCE & SNIPER SEARCH ---
    - Pick ONE aesthetic for the whole video (e.g., 'Dark Noir', 'Golden Hour', 'Clean Minimalist').
    - All keywords must include this aesthetic tag to ensure consistency across clips.
    - Keywords must be concrete. Use: [Subject] + [Environment] + [Fixed Aesthetic Tag].

    --- RULE 3: API MATCHING ---
    - Keywords must match standard stock tags (English, 3-4 words max).
    - Scene 1 is always a high-impact Macro/Close-up hook.
    """

    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview", 
            contents=f"TOPIC: {topic}. REQUIREMENT: 7 fast cuts (3s each), total visual coherence.",
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                thinking_config=types.ThinkingConfig(thinking_level=types.ThinkingLevel.LOW),
                temperature=1.0,
                response_mime_type="application/json",
                response_schema=target_schema 
            )
        )
        raw_data = json.loads(response.text)
        if isinstance(raw_data, list): raw_data = raw_data[0]
        return VideoScript.model_validate(raw_data).model_dump()
    except Exception as e:
        st.error(f"AI Error: {str(e)}")
        return None