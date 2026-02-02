import streamlit as st
import os
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
        st.error("⚠️ API Key missing in Secrets.")
        return None

    try:
        # Client configurato per la serie Gemini 3 (v1alpha)
        client = genai.Client(http_options={'api_version': 'v1alpha'}, api_key=api_key)
        
        system_instruction = """
        You are TubeFlow v3 "Expert Edition", a specialist in 2026 viral content.
        Your mission is to translate user requests into high-retention Faceless videos.

        STRATEGY 2026:
        1. SNIPER SEARCH: Convert abstract feelings into CONCRETE objects for Pexels/Pixabay. 
           (e.g., "Loneliness" -> "Empty street night moody", "Wealth" -> "Minimalist gold watch detail").
        2. VINTAGE AESTHETIC: Always add tags like "Moody", "Cinematic", "Grainy", or "Slow shutter" to keywords.
        3. DOPAMINE PACING: Use fast cuts (2-3s) for facts, and long "POV" takes (10s+) for atmospheres.
        4. HOOK FIRST: The first scene must be a "Visual Hook" (Macro, Extreme Close-up).

        ADAPTABILITY:
        - If the user specifies "X clips", obey strictly.
        - If no number is specified, decide the best storytelling rhythm.
        """

        # Chiamata al modello Gemini 3 Flash
        response = client.models.generate_content(
            model="gemini-3-flash-preview", 
            contents=f"USER REQUEST: {topic}",
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                # Livello di pensiero "low" per massimizzare la velocità e minimizzare i costi
                thinking_config=types.ThinkingConfig(thinking_level="low"),
                response_mime_type="application/json",
                temperature=1.0 # Valore ottimale per Gemini 3
            )
        )

        if not response.text:
            return None
        
        return VideoScript.model_validate_json(response.text).model_dump()

    except Exception as e:
        if "429" in str(e):
            st.error("🚫 QUOTA EXCEEDED (20 RPD). Please create a NEW Google Project or wait 24h.")
        else:
            st.error(f"AI Engine Error: {str(e)}")
        return None