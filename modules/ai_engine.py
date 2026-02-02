import streamlit as st
from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import List

# --- STRUTTURA DATI ---
class Scene(BaseModel):
    scene_number: int
    voiceover: str
    keyword: str
    duration: int

class VideoScript(BaseModel):
    scenes: List[Scene]

def generate_script(topic: str, vibe: str, api_key: str) -> List[dict]:
    """
    Genera script ottimizzato con il 'Sniper Protocol' per asset stock precisi.
    """
    if not api_key:
        st.error("⚠️ API Key mancante. Inseriscila nella sidebar.")
        return []

    try:
        client = genai.Client(api_key=api_key)
        
        # --- QUI INSERIAMO IL TUO PROMPT "SNIPER PROTOCOL" ---
        system_instruction = """
        You are an expert TikTok/Reels Video Director specialized in stock footage curation.
        Create a high-retention, fast-paced plan with 3-5 scenes based on the user topic.

        STRICT SEARCH RULES (The "Sniper Protocol"):
        1. 'voiceover': Engaging, direct, ready for TTS. Max 2 sentences.
        2. 'keyword': A STRING of 2-4 concrete visual tags separated by spaces. 
           - MUST include a visual noun (Subject) and an action/context.
           - AVOID abstract concepts (e.g., DO NOT use "Success", USE "Man in suit shaking hands").
           - MANDATORY: Append "Vertical" or "Portrait" to every keyword string to match TikTok format.
           - Format: "[Subject] [Action/Adjective] [Setting] Vertical"
           - Example: "Business meeting shaking hands office Vertical"
        3. 'duration': 3-6 seconds.
        4. Total length: 15-30s.

        OUTPUT: Valid JSON only matching the requested schema.
        """
        
        user_prompt = f"TOPIC: {topic}\nVIBE: {vibe}"

        # Schema JSON manuale (Fix per compatibilità Gemini 1.5)
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

        # Parsing e Validazione
        script_obj = VideoScript.model_validate_json(response.text)
        return [scene.model_dump() for scene in script_obj.scenes]

    except Exception as e:
        print(f"🔥 AI Error: {e}")
        st.error(f"Errore generazione script: {str(e)}")
        return []