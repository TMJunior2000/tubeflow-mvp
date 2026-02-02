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
        # Client v1alpha per Gemini 3
        client = genai.Client(http_options={'api_version': 'v1alpha'}, api_key=api_key)
        
        # Schema strutturale rigido per evitare i 23 errori di validazione
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

        # --- IL TUO PROMPT META 2026 (Expert Edition) ---
        system_instruction = """
        You are TubeFlow v3 "Expert Edition", a specialist in the 2026 viral content meta-game.
        Your goal is to create "Faceless" videos that don't look like generic stock, optimizing for retention and dopamine loops.

        ---------------------------------------------------------
        RULE 1: SNIPER SEARCH & 2026 AESTHETICS (PEXELS/PIXABAY)
        - LATERAL ASSOCIATIONS: Avoid literal/didactic queries. 
             * Instead of "Sadness", use "Rain on window dark" or "Single dead leaf".
             * Instead of "Success", use "Luxury car detail" or "Minimalist office view".
        - "IMPERFECT VINTAGE" AESTHETIC: For every scene, add aesthetic tags like "Moody", "Cinematic", "Grainy", "Slow shutter", or "Minimalist".
        - VISUAL COHERENCE: Maintain a consistent color thread across scenes (e.g., all cold tones or all warm tones).

        RULE 2: THE DOPAMINE WORKFLOW (HOOK & CUTS)
        - THE HOOK (First 2s): The first scene MUST have extreme visual impact. Use keywords like "Macro", "Slow motion", "Explosion", "Extreme close up".
        - PACING: If the script is informative, use cuts every 2-3 seconds to maintain high dopamine (Multi-Clip Strategy). Use ONLY INTEGERS for duration.
        - PAUSES: If the script is cinematic/reflective, use long clips with fluid camera movements (Slow Shutter).

        RULE 3: HIGH-RPM NICHES (FEBRUARY 2026)
        Adapt the script and visuals if you detect these niches:
        - AI STORIES/CRIME: Dark visuals, shadows, noir atmospheres, fog.
        - FINANCE/MINIMALISM: "Clean" visuals, geometric lines, modern architecture, quiet luxury.
        - SILENT VLOG/ASMR: Natural visuals, macro details, textures.

        RULE 4: AUDIO STRATEGY (SFX FOCUS)
        - The script must implicitly suggest environmental sounds. 
        - Voice Speed: -10% for noir/moody stories, +10% for facts/finance.

        ---------------------------------------------------------
        MANDATORY: Return ONLY a SINGLE JSON object. Use ONLY the provided schema keys.
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

        if not response.text:
            return None
        
        # Parsing sicuro
        raw_data = json.loads(response.text)
        if isinstance(raw_data, list):
            raw_data = raw_data[0]
            
        return VideoScript.model_validate(raw_data).model_dump()

    except Exception as e:
        st.error(f"AI Engine Error: {str(e)}")
        return None