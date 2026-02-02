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
                You are a Stock Footage Curator Algorithm.
                Your goal is to generate search tags that PERFECTLY MATCH Pexels/Pixabay indexing logic.

                CRITICAL TAGGING RULES:
                1. HIERARCHY (Subject + Location):
                - NEVER search for complex actions (e.g., "Climbing"). Search for the Context.
                - BAD: "Penguin looking at sea" -> GOOD: "Penguin Beach"
                - BAD: "Man working hard" -> GOOD: "Man Office" or "Typing"

                2. AESTHETICS & LIGHT (The "Vibe" Hack):
                - Stock engines index LIGHT better than EMOTION.
                - Instead of "Sadness", use: "Rain Window", "Dark Room", "Shadow".
                - Instead of "Success", use: "Mountain Top", "Sunlight", "Golden Hour".
                - Instead of "Tech", use: "Blue Light", "Neon", "Server Room".

                3. SAFE KEYWORDS (The Jokers):
                - Time passing -> "Timelapse", "Clouds moving".
                - Thinking/Mind -> "Forest fog", "Ocean waves".
                - Business -> "Office", "Glass Building", "Handshake".

                4. FORMATTING:
                - Keyword MUST be a string of 2-3 words max.
                - Format: [Noun/Subject] [Environment] [Lighting/Vibe]
                - Example: "Lion Savanna Golden"
                - ENGLISH ONLY. NO "Vertical" (system handles it).

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
            model="gemini-flash-latest", 
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