import streamlit as st
from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import List

# Modelli Pydantic per validazione
class Scene(BaseModel):
    scene_number: int
    voiceover: str
    keyword: str
    duration: int

class VideoScript(BaseModel):
    scenes: List[Scene]

def generate_script(topic: str, vibe: str, api_key: str) -> List[dict]:
    """
    Genera uno script video strutturato usando Google Gemini.
    Richiede API Key utente (BYOK).
    """
    if not api_key:
        st.error("⚠️ API Key mancante. Inseriscila nella sidebar.")
        return []

    try:
        client = genai.Client(api_key=api_key)
        
        # Prompt ottimizzato per Social Video
        system_instruction = """
        You are an expert Video Director for TikTok/Reels.
        Create a fast-paced plan (3-5 scenes). Total length: 15-30 seconds.
        
        RULES:
        1. 'voiceover': Direct, engaging, max 2 short sentences per scene.
        2. 'keyword': Visual search term (English noun + adjective). E.g. "Cyberpunk city", "Happy dog".
        3. 'duration': 3 to 6 seconds per scene.
        
        OUTPUT: Valid JSON only matching the schema.
        """
        
        user_prompt = f"TOPIC: {topic}\nVIBE: {vibe}"

        # Schema JSON "Low Level" per compatibilità Gemini 1.5
        manual_schema = {
            "type": "OBJECT",
            "properties": {
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
            "required": ["scenes"]
        }

        # Chiamata API
        response = client.models.generate_content(
            model="gemini-1.5-flash", 
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=manual_schema,
                temperature=0.7
            )
        )

        if not response.text:
            return []

        # Parsing
        script_obj = VideoScript.model_validate_json(response.text)
        return [scene.model_dump() for scene in script_obj.scenes]

    except Exception as e:
        st.error(f"Errore AI: {str(e)}")
        return []