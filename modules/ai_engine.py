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
        
        # --- THE SNIPER PROMPT (META 2026) ---
        system_instruction = """
        You are TubeFlow v3 "Expert Edition", the elite Video Architect for 2026 viral content.
        Your goal is to translate User Requests into high-retention Faceless videos using Pexels/Pixabay.

        MANDATORY: Return a SINGLE JSON OBJECT. Do not use markdown blocks.

        ---------------------------------------------------------
        RULE 1: SNIPER SEARCH & 2026 AESTHETICS
        - LATERAL ASSOCIATION: Avoid literal/abstract queries. 
             * "Success" -> "Luxury watch detail" or "Skyscraper top view".
             * "Solitude" -> "Lone boat on lake" or "Rainy window moody".
        - SEARCH STRATEGY: Use [Subject] + [Environment]. Keywords must be in ENGLISH, max 3 words.
        - ESTHETIC TAGS: Append tags like "Moody", "Cinematic", "Grainy", or "Minimalist" to keywords.

        RULE 2: DOPAMINE WORKFLOW
        - THE HOOK (First 2s): Scene 1 MUST have extreme visual impact (Macro, Slow motion, Extreme close-up).
        - ADAPTIVE PACING: 
             * For info/viral facts: Fast cuts every 2-3 seconds.
             * For mood/philosophical: Single long takes (15-30s) or slow cinematic pans.
        - FORMAT AWARENESS: TikTok (9:16) likes loops and single-take aesthetics; YouTube (16:9) likes variety.

        RULE 3: VOICE & TONAL CONTROL
        - Voice Speed: 
             * "-10%" for Noir/Deep/Moody stories.
             * "+10%" for Viral Facts/Hype/Finance.
             * "+0%" for Standard Narrative.
        
        ---------------------------------------------------------
        JSON SCHEMA:
        {
          "voice_settings": {"voice_speed": "string"},
          "scenes": [{"scene_number": int, "voiceover": "string", "keyword": "string", "duration": int}]
        }
        """

        response = client.models.generate_content(
            model="gemini-3-flash-preview", 
            contents=f"USER REQUEST: {topic}",
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                thinking_config=types.ThinkingConfig(thinking_level=types.ThinkingLevel.LOW),
                response_mime_type="application/json",
                temperature=1.0 
            )
        )

        if not response.text:
            return None
        
        # --- ANTI-CRASH PARSING LOGIC ---
        try:
            raw_data = json.loads(response.text)
            if isinstance(raw_data, list):
                raw_data = raw_data[0] # Fixes the "AI returned a list" error
            
            # Pydantic validation
            return VideoScript.model_validate(raw_data).model_dump()
        except Exception as parse_err:
            print(f"Parsing failed. Raw response: {response.text}")
            raise parse_err

    except Exception as e:
        if "429" in str(e):
            st.error("🚫 QUOTA EXCEEDED. Create a NEW Google Project to reset the 20-request limit.")
        else:
            st.error(f"AI Engine Error: {str(e)}")
        return None