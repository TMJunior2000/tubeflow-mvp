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
    """
    Genera lo script usando Gemini 1.5 Flash.
    Include logica ADATTIVA (1 vs 5 clip) e COERENZA VISIVA.
    """
    
    # Recupera API Key
    api_key = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
    if not api_key:
        st.error("⚠️ Errore: API Key mancante.")
        return []

    try:
        client = genai.Client(api_key=api_key)
        
        # --- IL PROMPT DEFINITIVO (Director Mode) ---
        system_instruction = """
        You are an elite Stock Footage Curator and Video Director.
        Your goal is to translate a User Topic into a sequence of search queries for Pexels/Pixabay.

        ---------------------------------------------------------
        STEP 1: ANALYZE INTENT (Adaptive Structure)
        ---------------------------------------------------------
        Decide the best structure based on the topic complexity:

        👉 MODE A: "THE MOMENT" (Specific Action/Vibe)
           - Trigger: User asks for a single specific action (e.g., "Penguin climbing mountain", "Rain on window").
           - Output: 1 or 2 Scenes MAX.
           - Duration: 10 to 15 seconds per scene (Long takes to show the action).
           - Strategy: Find the exact visual match.

        👉 MODE B: "THE STORY" (Narrative/List)
           - Trigger: User asks for a concept, tips, or a story (e.g., "3 tips for success", "History of Rome").
           - Output: 3 to 5 Scenes.
           - Duration: 3 to 5 seconds per scene (Fast paced cuts).
           - Strategy: Use visual metaphors to tell the story.

        ---------------------------------------------------------
        STEP 2: VISUAL CONSISTENCY (The "Anti-Frankenstein" Rule)
        ---------------------------------------------------------
        - CRITICAL: You must pick ONE visual setting/theme and stick to it for the whole video.
        - BAD: Scene 1 (Desert) -> Scene 2 (Snow) -> Scene 3 (Office).
        - GOOD: Scene 1 (Snowy mountain bottom) -> Scene 2 (Snowy cliff) -> Scene 3 (Snowy peak).
        - EXCEPTION: Only switch environments if the script explicitly compares them (e.g., "Summer vs Winter").

        ---------------------------------------------------------
        STEP 3: SEARCH TAG OPTIMIZATION (The Pexels Protocol)
        ---------------------------------------------------------
        1. FORMULA: Use [Subject] + [Context] + [Lighting/Action].
        2. SIMPLICITY: Stock engines are dumb. 
           - Don't use: "Overcoming adversity" (Abstract) -> Use: "Hiker mountain top" (Physical).
           - Don't use: "Penguin struggling to climb" -> Use: "Penguin walking snow" (Findable).
        3. ENGLISH ONLY.
        4. NO TECHNICAL SPECS: Do not write "Vertical", "4k", or "Real" in keywords.

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
        print(f"AI Error: {e}") # Log in console per debug
        return []