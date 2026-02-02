import streamlit as st
import os
import json
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

    try:
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

        # --- IL PROMPT OTTIMIZZATO PER I DATABASE STOCK ---
        system_instruction = """
        You are TubeFlow v3, a professional Video Editor specialized in Pexels and Pixabay database indexing.
        Your goal is to generate keywords that ALWAYS return high-quality results.

        ---------------------------------------------------------
        RULE 1: PEXELS/PIXABAY SNIPER ENGINE (MANDATORY)
        - KEYWORD STRUCTURE: [Subject] + [Action/Environment] + [Aesthetic].
        - NO ABSTRACT NOUNS: Never search for "Trust", "Innovation", "Motivation", or "Hate". These databases will fail.
        - PHYSICAL SUBSTITUTION (Sniperizing):
            * Instead of "Growth", use "Plant sprout growing time-lapse".
            * Instead of "Wealth", use "Golden coins falling" or "Luxury car interior".
            * Instead of "Hard Work", use "Person typing on keyboard backlit" or "Man sweating workout".
        - SEARCH LANGUAGE: Always use English. Maximum 4 words.
        - FILTERS: Append aesthetic tags like "Moody", "Cinematic", "Blurred background", or "Top view".

        ---------------------------------------------------------
        RULE 2: CONTENT ARCHITECTURE (META 2026)
        - HOOK: Scene 1 must be a high-impact visual (Macro, Close-up, Slow motion).
        - DOPAMINE FLOW: If the user asks for a specific clip count (e.g., 7 clips), divide the script into short, punchy segments (2-4s each).
        - CONSISTENCY: Ensure all keywords share a similar lighting style (e.g., "Dark Noir", "Bright Minimal", or "Golden Hour").

        ---------------------------------------------------------
        TECHNICAL RULES:
        - DURATION: Must be an INTEGER (e.g., 3, not 3.5).
        - SCENE COUNT: Strictly follow the user's requested number of clips.
        - JSON ONLY: Return a single JSON object. No markdown.
        """

        response = client.models.generate_content(
            model="gemini-3-flash-preview", 
            contents=f"USER REQUEST: {topic}",
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