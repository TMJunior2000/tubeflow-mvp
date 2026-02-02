import streamlit as st
import os
from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import List

# Modelli Dati
class Scene(BaseModel):
    scene_number: int
    voiceover: str
    keyword: str
    duration: int

class VideoScript(BaseModel):
    scenes: List[Scene]

def generate_script(topic: str, vibe: str) -> List[dict]:
    """Genera script usando la chiave Admin dai secrets."""
    
    # Recupera la chiave dai secrets (Gestione centralizzata)
    api_key = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
    
    if not api_key:
        st.error("⚠️ Errore Server: Chiave API mancante. Contattare l'amministratore.")
        return []

    try:
        client = genai.Client(api_key=api_key)
        
        # PROMPT "SNIPER PROTOCOL" (Mantenuto perché performante)
        system_instruction = """
        You are an expert TikTok/Reels Video Director.
        Create a high-retention plan with 3-5 scenes based on the user topic.

        STRICT SEARCH RULES:
        1. 'voiceover': Engaging, direct. Max 2 sentences.
        2. 'keyword': A STRING of 2-4 concrete visual tags. 
           - MUST include a visual noun and action.
           - Format: "[Subject] [Action] Vertical"
           - Example: "Business man running city Vertical"
        3. 'duration': 3-5 seconds.
        4. Total length: 15-30s.

        OUTPUT: Valid JSON only matching the schema.
        """
        
        user_prompt = f"TOPIC: {topic}\nVIBE: {vibe}"

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

        if not response.text: return []
        
        script_obj = VideoScript.model_validate_json(response.text)
        return [scene.model_dump() for scene in script_obj.scenes]

    except Exception as e:
        st.error(f"Errore AI: {str(e)}")
        return []