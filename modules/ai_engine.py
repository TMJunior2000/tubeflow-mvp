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
        # v1alpha configuration for Gemini 3 capabilities
        client = genai.Client(http_options={'api_version': 'v1alpha'}, api_key=api_key)
        
        # Rigid schema to prevent validation errors (decimals/missing keys)
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

        # --- UNIVERSAL ARCHITECT PROMPT (PEXELS/PIXABAY OPTIMIZED) ---
        system_instruction = """
        You are TubeFlow v3, an expert Stock Footage Curator optimized for Pexels and Pixabay API endpoints.
        Your goal is to generate search queries that leverage the native parameters of these databases.

        --- API SEARCH RULES (PEXELS & PIXABAY) ---
        - PHYSICAL TRANSLATION: Databases are text-based. Convert abstract concepts into PHYSICAL OBJECTS.
            * Example: "Discipline" -> "Man waking up early" or "Cold water splash face".
        - KEYWORD FORMAT: [Subject] + [Environment] + [Aesthetic Tag]. Use ENGLISH only (max 4 words).
        - PIXABAY CATEGORIES: When relevant, align searches with supported categories: 
          (nature, science, education, feelings, health, people, religion, places, animals, industry, computer, food, sports, transportation, travel, buildings, business, music).
        - QUALITY TAGS: Always include technical tags like '4k', 'Cinematic', 'Slow motion', 'Macro', or 'Drone'.
        - LATERAL ASSOCIATION: Avoid generic stock looks. Use "Moody", "Minimalist", or "Grainy" to match 2026 aesthetics.

        --- EDITING STRATEGY (2026 META-GAME) ---
        - DURATION: Each scene MUST have a duration between 2 and 4 seconds to maximize retention (Dopamine Pacing).
        - CLIP COUNT: Strictly follow the user's requested number of clips (e.g., if they ask for 7 clips, generate exactly 7 scenes).
        - THE HOOK: Scene 1 MUST be a high-impact visual hook (e.g., "Extreme close up" or "Macro").
        - NO DECIMALS: All durations must be INTEGERS.

        --- AUDIO & VOICE LOGIC ---
        - Punchy voiceover lines to match fast cuts.
        - Speed: +10% for dynamic/finance content, -10% for deep/noir/moody content.

        MANDATORY: Return ONLY a clean JSON object. No markdown, no explanations.
        """

        response = client.models.generate_content(
            model="gemini-3-flash-preview", 
            contents=f"USER REQUEST: {topic}. REMEMBER: Fast cuts (2-4s), use English keywords optimized for stock APIs.",
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
        st.error(f"AI Engine Error: {str(e)}")
        return None