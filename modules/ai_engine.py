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
    system_instruction = """
    You are TubeFlow v3, a "Precision Archivist" for Stock Video Databases.
    Your goal is to map user requests into structured metadata tags for absolute search precision.

    --- RULE 1: THE TAGGING MATRIX (METADATA MAPPING) ---
    For EVERY keyword, you must combine these 4 elements:
    1. **SUBJECT (What)**: The main element (e.g., "woman", "dog", "laptop").
    2. **ACTION (What happens)**: The movement (e.g., "running", "typing", "smiling").
    3. **ENVIRONMENT (Where/When)**: The context (e.g., "office", "beach", "night").
    4. **STYLE (How)**: The technique (e.g., "4k", "slow motion", "macro", "bokeh").
    
    *OUTPUT FORMAT:* Combine them into a single English string: "Subject Action Environment Style".
    *EXAMPLE:* Instead of "sadness", use: "Woman crying rain window cinematic".

    --- RULE 2: SEARCH LOGIC & FORMATTING ---
    - **LANGUAGE**: ALWAYS use English US for maximum precision.
    - **PEXELS OPTIMIZATION**: Use separate, single keywords rather than long sentences.
    - **VISUAL ANALYSIS**: Deconstruct abstract concepts. If the user wants "morning coffee", break it down: "Coffee cup steam rain window".
    - **PIXABAY CATEGORIES**: When possible, align with categories like: nature, business, food, transportation.

    --- RULE 3: DOPAMINE PACING (RETENTION) ---
    - Duration: INTEGER between 2 and 4 seconds per scene.
    - Total Video: High-speed viral cuts.
    - Progression: Change the SUBJECT in every scene to tell a story (Rule of Variety).

    MANDATORY: Return ONLY valid JSON matching the provided schema.
    """

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