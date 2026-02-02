import streamlit as st
import os
from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import List, Optional

# --- MODELLI DATI (SNELLITI: Niente più Music Settings) ---
class Scene(BaseModel):
    scene_number: int
    voiceover: str
    keyword: str
    duration: int

class VoiceSettings(BaseModel):
    voice_speed: str
    # Abbiamo rimosso Genre e Mood. Inutile calcolarli se non li usiamo.

class VideoScript(BaseModel):
    voice_settings: VoiceSettings # Rinominato da audio_settings
    scenes: List[Scene]

def generate_script(topic: str) -> Optional[dict]:
    
    api_key = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
    if not api_key:
        st.error("⚠️ API Key mancante.")
        return None

    try:
        client = genai.Client(api_key=api_key)
        
        # --- IL NUOVO PROMPT "TIKTOK STRATEGIST" ---
        system_instruction = """
        You are a Viral Content Strategist for TikTok and Reels.
        Your goal is to create a high-retention short video script.

        PHASE 1: VISUAL KEYWORDS (The "Pexels Rule")
        - You must generate search queries for Stock Footage.
        - THE RULE: Keywords must be CONCRETE NOUNS. No abstract concepts.
        - BAD: "Sadness and solitude" (Abstract -> No results).
        - BAD: "Cinematic 4k detailed samurai" (Too long -> No results).
        - GOOD: "Samurai rain" (Concrete).
        - GOOD: "Lonely man sitting" (Concrete).
        
        PHASE 2: VOICE PACING
        - Determine the voice speed based on the topic intensity.
        - "-10%" for Sad/Deep/Philosophical/Horror.
        - "+10%" for Facts/Curiosities/Hype/Motivation.
        - "+0%" for Narrative/Storytelling.

        PHASE 3: SCRIPTING
        - Scene 1 MUST be a "Hook" (catch the attention in 3 seconds).
        - Keep sentences short and punchy.
        - Total duration: 30-60 seconds max.

        OUTPUT: JSON Object only.
        """
        
        manual_schema = {
            "type": "OBJECT",
            "properties": {
                "voice_settings": {
                    "type": "OBJECT",
                    "properties": {
                        "voice_speed": {"type": "STRING"}
                    },
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
            model="gemini-flash-latest", 
            contents=f"TOPIC: {topic}",
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=manual_schema,
                temperature=0.7
            )
        )

        if not response.text:
            st.error("AI Error: Risposta vuota.")
            return None
        
        return VideoScript.model_validate_json(response.text).model_dump()

    except Exception as e:
        st.error(f"AI Error: {str(e)}")
        return None