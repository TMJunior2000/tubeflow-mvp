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
        
        # --- YOUR META 2026 PROMPT (Translated to English) ---
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
        - PACING: If the script is informative, use cuts every 2-3 seconds to maintain high dopamine (Multi-Clip Strategy).
        - PAUSES: If the script is cinematic/reflective, use long clips with fluid camera movements (Slow Shutter).

        RULE 3: HIGH-RPM NICHES (FEBRUARY 2026)
        Adapt the script and visuals if you detect these niches:
        - AI STORIES/CRIME: Dark visuals, shadows, noir atmospheres, fog.
        - FINANCE/MINIMALISM: "Clean" visuals, geometric lines, modern architecture, quiet luxury.
        - SILENT VLOG/ASMR: Natural visuals, macro details, textures.

        RULE 4: AUDIO STRATEGY (SFX FOCUS)
        - The script must implicitly suggest environmental sounds. 
        - Example: "The wind was blowing..." (User will add wind SFX).
        - Voice Speed: -10% for noir/moody stories, +10% for facts/finance.

        ---------------------------------------------------------
        MANDATORY: Return ONLY a SINGLE JSON object. Do not use markdown blocks.
        REQUIRED FORMAT: JSON consistent with the Pydantic schema.
        """

        # Optimized call based on Gemini 3 documentation
        response = client.models.generate_content(
            model="gemini-3-flash-preview", 
            contents=f"USER REQUEST: {topic}",
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                # Docs: 'low' reduces latency and helps avoid 503 Overloaded errors
                thinking_config=types.ThinkingConfig(thinking_level=types.ThinkingLevel.LOW),
                # Docs: 1.0 is mandatory for Gemini 3 stability
                temperature=1.0,
                response_mime_type="application/json"
            )
        )

        if not response.text:
            return None
        
        # Safe parsing to avoid Validation Errors (lists vs objects)
        raw_data = json.loads(response.text)
        if isinstance(raw_data, list):
            raw_data = raw_data[0]
            
        return VideoScript.model_validate(raw_data).model_dump()

    except Exception as e:
        if "503" in str(e):
            st.error("🚀 Gemini 3 Server overloaded. Please try again in a few seconds.")
        elif "429" in str(e):
            st.error("🚫 Daily Quota (20 RPD) exhausted. Change your API project.")
        else:
            st.error(f"AI Engine Error: {str(e)}")
        return None