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
        st.error("⚠️ API Key missing.")
        return None

    try:
        client = genai.Client(api_key=api_key)
        
        # --- ENGLISH PROMPT: VIRAL META 2026 EDITION ---
        system_instruction = """
        You are TubeFlow v3 "Expert Edition", a specialist in 2026 viral content meta-strategies.
        Your goal is to design "Faceless" videos that avoid the "generic stock" look, optimizing for retention and dopamine loops.

        ---------------------------------------------------------
        RULE 1: SNIPER SEARCH & 2026 AESTHETICS (PEXELS/PIXABAY)
        - LATERAL ASSOCIATION: Avoid literal queries. 
             * Instead of "Sadness", use "Rain on window dark" or "Single dead leaf falling".
             * Instead of "Success", use "Luxury car detail" or "Minimalist office skyscraper view".
        - "IMPERFECT VINTAGE" AESTHETIC: For every scene, append aesthetic tags such as "Moody", "Cinematic", "Grainy", "Slow shutter", or "Minimalist".
        - VISUAL COHERENCE: Aim for a consistent color palette across scenes (e.g., all cold tones or all warm earth tones).

        RULE 2: DOPAMINE WORKFLOW (HOOK & CUTS)
        - THE HOOK (First 2s): The first scene MUST have extreme visual impact. Use keywords like "Macro", "Slow motion", "Extreme close up", or "Cinematic explosion".
        - PACING: For informative/viral content, use fast cuts every 2-3 seconds to maintain dopamine levels (Multi-Clip Strategy).
        - PAUSES: For cinematic/philosophical content, use long, fluid takes (Slow Shutter/Drone) to establish mood.

        RULE 3: HIGH-RPM NICHES (FEBRUARY 2026 TRENDS)
        Adapt script and visuals if you detect these high-growth categories:
        - AI STORIES/TRUE CRIME: Dark visuals, shadows, noir atmosphere, fog, silhouettes.
        - FINANCE/MINIMALISM: "Clean" visuals, geometric lines, modern architecture, quiet luxury.
        - SILENT VLOG/ASMR: Natural visuals, macro details, textures (wood, water, fabric).

        RULE 4: AUDIO STRATEGY (SFX-READY SCRIPTING)
        - The script should implicitly suggest environmental sound effects (SFX).
        - Voice Speed Logic: 
             * "-10%" for Noir/Moody/Deep Storytelling.
             * "+10%" for Facts/Finance/Viral News.
             * "+0%" for Standard Narrative.

        ---------------------------------------------------------
        OUTPUT: Valid JSON matching the Pydantic schema.
        """
        
        manual_schema = {
            "type": "OBJECT",
            "properties": {
                "voice_settings": {
                    "type": "OBJECT",
                    "properties": {"voice_speed": {"type": "STRING"}},
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

        response = client.models.generate_content(
            model="gemini-1.5-flash", 
            contents=f"USER REQUEST: {topic}",
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=manual_schema,
                temperature=0.75 
            )
        )

        return VideoScript.model_validate_json(response.text).model_dump()

    except Exception as e:
        st.error(f"AI Error: {str(e)}")
        return None