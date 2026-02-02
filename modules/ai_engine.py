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

def generate_script(topic: str) -> dict | None:
    api_key = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
    if not api_key:
        st.error("⚠️ API Key missing.")
        return None

    try:
        client = genai.Client(http_options={'api_version': 'v1alpha'}, api_key=api_key)
        
        # SCHEMA RIGIDO: Impedisce decimali e chiavi inventate
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

        # --- IL PROMPT OTTIMIZZATO PER I TAG STOCK ---
        system_instruction = """
        You are TubeFlow v3, a specialized Stock Footage Curator for Pexels and Pixabay.
        Your goal is to provide search queries that guarantee 100% match rate and professional aesthetics.

        --- RULE 1: STOCK DATABASE LOGIC (PEXELS/PIXABAY) ---
        - NO ABSTRACT WORDS: Never use "Success", "Motivation", "Sadness", or "Future".
        - SEARCH FORMULA: [Concrete Subject] + [Specific Action/Detail] + [Aesthetic Tag].
        - PHYSICAL SNIPERIZING examples:
            * Instead of "Wealth", use: "Gold bar stack" or "Luxury mansion interior".
            * Instead of "Loneliness", use: "Empty train station night" or "Lone tree winter".
            * Instead of "Knowledge", use: "Old books library" or "Human brain 3d render".
        - LANGUAGE: Always English. Max 3-4 words per query.
        - TOP TAGS: Always include one of: 'Cinematic', 'Moody', 'Minimalist', 'Macro', 'Aerial'.

        --- RULE 2: DOPAMINE RETENTION (2026 META) ---
        - DURATION LIMIT: For viral/motivational content, EACH scene duration MUST be an INTEGER between 2 and 4 seconds.
        - CLIP COUNT: If the user asks for 7 clips, provide EXACTLY 7 scenes. 
        - TOTAL TIME: A 7-clip video must be around 20-25 seconds total.
        - HOOK: Scene 1 MUST be a visual stunner (Macro or Slow Motion).

        --- RULE 3: AUDIO & VIBE ---
        - Voiceover must be punchy and fit the 2-4s window.
        - Use voice_speed "+10%" for energetic/finance, "-10%" for deep/noir.

        MANDATORY: Return ONLY a JSON object. No markdown.
        """

        response = client.models.generate_content(
            model="gemini-3-flash-preview", 
            contents=f"USER REQUEST: {topic}. 7 clips. Fast pacing. Max 4s each.",
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