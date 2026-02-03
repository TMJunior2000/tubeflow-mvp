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

    # --- PROMPT BLINDATO "SUBJECT ANCHOR" ---
    system_instruction = """
    You are TubeFlow v3. Goal: Absolute Visual Precision.

    --- RULE 1: THE "ANCHOR" SUBJECT ---
    - **CRITICAL:** The FIRST word of every keyword MUST be the Main Subject.
    - **REPETITION:** Repeat the subject in every query to avoid ambiguity.
    - **BAD:** "Chick hatching" (Finds chickens), "Swimming" (Finds fish).
    - **GOOD:** "Penguin chick hatching", "Penguin swimming underwater".
    - **NEVER** use ambiguous words alone (e.g. use "Baby Penguin", never just "Chick").

    --- RULE 2: VISUAL PROGRESSION ---
    - Tell a story: Scene 1 (Subject Close-up) -> Scene 2 (Subject Action) -> Scene 3 (Subject Environment).
    - Vary the action, but keep the Anchor Subject fixed.

    --- RULE 3: TECHNICAL SPECS ---
    - Duration: INTEGER (2-4s).
    - Audio Speed: String with sign (e.g. "+10%").
    - Keywords: English, max 3-4 words. format: [Subject] + [Action] + [Aesthetic].

    MANDATORY: Return ONLY valid JSON.
    """

    max_retries = 3
    attempt = 0
    while attempt < max_retries:
        try:
            response = client.models.generate_content(
                model="gemini-3-flash-preview", 
                contents=f"TOPIC: {topic}. REQUIREMENT: 7 scenes, ALWAYS repeat the subject '{topic.split()[0]}' in keywords.",
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    thinking_config=types.ThinkingConfig(thinking_level=types.ThinkingLevel.LOW),
                    temperature=0.7, # Abbassato per maggiore rigore
                    response_mime_type="application/json",
                    response_schema=target_schema 
                )
            )
            raw_data = json.loads(response.text)
            if isinstance(raw_data, list): raw_data = raw_data[0]
            return VideoScript.model_validate(raw_data).model_dump()
        except Exception as e:
            if "503" in str(e): attempt += 1; time.sleep(2); continue
            st.error(f"AI Error: {str(e)}")
            return None
    return None