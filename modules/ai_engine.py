import streamlit as st
import os
from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import List

# --- MODELLI DATI ---
class Scene(BaseModel):
    scene_number: int
    voiceover: str
    keyword: str
    duration: int

class VideoScript(BaseModel):
    scenes: List[Scene]

# --- FUNZIONE PRINCIPALE ---
def generate_script(topic: str, vibe: str) -> List[dict]:
    
    # Recupera API Key
    api_key = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
    if not api_key:
        st.error("⚠️ Errore: API Key mancante.")
        return []

    try:
        client = genai.Client(api_key=api_key)
        
        # --- IL NUOVO PROMPT "ONE-SHOT SUPREMACY" ---
        system_instruction = """
        You are a Stock Footage Curator.
        Your goal is to find the BEST video assets.

        ---------------------------------------------------------
        CORE LOGIC: THE "ONE-SHOT" RULE
        ---------------------------------------------------------
        Videos on social media perform better if they are continuous.
        
        👉 DEFAULT BEHAVIOR (Priority 1):
        If the user describes a visual action or atmosphere (e.g., "Penguin climbing mountain", "Sunset at beach", "Man working"), you MUST generate ONLY 1 SCENE.
        - Scenes: 1 (One)
        - Duration: 15 to 20 seconds.
        - Keyword: The exact broad subject (e.g., "Penguin walking snow").
        - Goal: Let the user see the full clip without interruptions.

        👉 EXCEPTION BEHAVIOR (Priority 2):
        Only switch to Multi-Scene mode if the user explicitly asks for a LIST, a STEP-BY-STEP guide, or contrasting concepts.
        - Example: "3 tips for..." -> 3 Scenes.
        - Example: "Summer vs Winter" -> 2 Scenes.
        - Example: "Past, Present, Future" -> 3 Scenes.
        
        ---------------------------------------------------------
        TAGGING RULES (Critical for Pexels/Pixabay)
        ---------------------------------------------------------
        1. MAIN SUBJECT ALWAYS: Every keyword MUST start with the main subject.
           - User: "Penguin climbing mountain"
           - BAD Keywords: "Mountain peak", "Snow", "Ice" (Subject is missing!)
           - GOOD Keyword: "Penguin walking snow" (Subject is present).
           
        2. SIMPLIFY ACTIONS:
           - Stock sites do not have "Climbing Mt Everest". They have "Walking in snow".
           - Always downgrade complex verbs to simple states (Walk, Run, Sit, Look).

        3. ENGLISH ONLY.
        
        OUTPUT: Valid JSON only matching the schema.
        """
        
        user_prompt = f"TOPIC: {topic}\nSTYLE/VIBE: {vibe}"

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

        # Chiamata a Gemini
        response = client.models.generate_content(
            model="gemini-1.5-flash", 
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=manual_schema,
                temperature=0.5 # Abbassato temperatura per essere più rigoroso
            )
        )

        if not response.text: return []
        
        script_obj = VideoScript.model_validate_json(response.text)
        return [scene.model_dump() for scene in script_obj.scenes]

    except Exception as e:
        print(f"AI Error: {e}") 
        return []