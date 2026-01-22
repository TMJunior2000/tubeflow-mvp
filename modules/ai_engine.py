import json
import streamlit as st
import os
import traceback
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List, Optional

# --- DEFINIZIONE STRUTTURA DATI (Solo per output finale) ---
class Scene(BaseModel):
    scene_number: int
    voiceover: str
    keyword: str
    duration: int

class VideoScript(BaseModel):
    scenes: List[Scene]

def generate_script(topic: str, vibe: str) -> List[dict]:
    print(f"--- INIZIO GENERAZIONE SCRIPT ---", flush=True)
    
    # 1. Recupero API Key
    api_key = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
    
    if not api_key:
        print("❌ ERRORE: API KEY non trovata nei Secrets!", flush=True)
        st.error("⚠️ Configurazione mancante: API Key non trovata.")
        return []
    
    # 2. Inizializzazione Client
    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        print(f"❌ Errore Client: {e}", flush=True)
        st.error("⚠️ Errore di connessione ai servizi AI.")
        return []
    
    # 3. Prompt & SCHEMA MANUALE (Il trucco per risolvere l'errore)
    system_instruction = """
    You are an expert Video Director. Create a plan with 3-5 scenes.
    For visuals: describe the subject (e.g. 'Man drinking water') not just action.
    OUTPUT: Valid JSON only matching the schema.
    """
    
    user_prompt = f"TOPIC: {topic}\nVIBE: {vibe}\nLENGTH: 30-60 seconds."

    # DEFINIZIONE SCHEMA "A BASSO LIVELLO" (Dizionario Python Puro)
    # Questo aggira il bug di compatibilità tra Pydantic e Google SDK
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

    try:
        print("⏳ Invio richiesta a Google Gemini 1.5 Flash...", flush=True)
        
        # 4. Chiamata API
        response = client.models.generate_content(
            model="gemini-flash-latest", 
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=manual_schema, # <--- USIAMO IL DIZIONARIO MANUALE
                temperature=0.7
            )
        )
        
        print("✅ Risposta ricevuta da Google!", flush=True)

        # 5. Parsing & Validazione
        if not response.text:
            print("⚠️ Risposta vuota dall'AI", flush=True)
            return []

        # Usiamo Pydantic solo ora che i dati sono arrivati
        script_obj = VideoScript.model_validate_json(response.text)
        return [scene.model_dump() for scene in script_obj.scenes]

    except Exception as e:
        print("\n🔥 ERRORE NEL MOTORE AI 🔥", flush=True)
        print(f"MESSAGGIO: {str(e)}", flush=True)
        traceback.print_exc()
        
        st.error("❌ Errore tecnico durante la generazione. Riprova.")
        return []