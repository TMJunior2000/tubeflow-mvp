import json
import streamlit as st
import os
import traceback # <--- Nuovo import per vedere i dettagli dell'errore
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List, Optional

# --- DEFINIZIONE STRUTTURA DATI ---
class Scene(BaseModel):
    scene_number: int = Field(..., description="Numero progressivo della scena")
    voiceover: str = Field(..., description="Il testo che lo speaker deve dire (max 20 parole)")
    keyword: str = Field(..., description="UNA singola parola chiave IN INGLESE per la ricerca video (es. 'sunset', 'coding')")
    duration: int = Field(..., description="Durata stimata della scena in secondi")

class VideoScript(BaseModel):
    scenes: List[Scene]

def generate_script(topic: str, vibe: str) -> List[dict]:
    print(f"--- INIZIO GENERAZIONE SCRIPT ---", flush=True) # <--- Debug Forzato
    
    # 1. Recupero API Key e DEBUG
    api_key = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
    
    # CONTROLLO SE LA CHIAVE ESISTE
    if not api_key:
        print("❌ ERRORE CRITICO: API KEY è None o Vuota!", flush=True)
        st.error("⚠️ Configurazione mancante: API Key non trovata.")
        return []
    else:
        # Stampiamo solo i primi 4 caratteri per sicurezza
        print(f"✅ API Key trovata. Inizia con: {api_key[:4]}...", flush=True)

    # 2. Inizializzazione Client
    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        print(f"❌ Errore Inizializzazione Client: {e}", flush=True)
        st.error("⚠️ Errore di connessione ai servizi AI.")
        return []
    
    # 3. Prompt
    system_instruction = """
    You are an expert Video Director. Create a plan with 3-5 scenes.
    For visuals: describe the subject (e.g. 'Man drinking water') not just action.
    OUTPUT: Valid JSON only.
    """
    
    user_prompt = f"TOPIC: {topic}\nVIBE: {vibe}\nLENGTH: 30-60 seconds."

    try:
        print("⏳ Invio richiesta a Google Gemini 1.5 Flash...", flush=True)
        
        # 4. Chiamata API
        response = client.models.generate_content(
            model="gemini-1.5-flash",  # <--- MODELLO SICURO
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=VideoScript,
                temperature=0.7
            )
        )
        
        print("✅ Risposta ricevuta da Google!", flush=True)

        # 5. Parsing
        if not response.text:
            print("⚠️ Risposta vuota dall'AI", flush=True)
            return []

        script_obj = VideoScript.model_validate_json(response.text)
        return [scene.model_dump() for scene in script_obj.scenes]

    # --- CATTURA QUALSIASI ERRORE E STAMPALO ---
    except Exception as e:
        print("\n\n🔥 ERRORE FATALE RILEVATO 🔥", flush=True)
        print(f"TIPO ERRORE: {type(e).__name__}", flush=True)
        print(f"MESSAGGIO: {str(e)}", flush=True)
        print("TRACEBACK COMPLETO:", flush=True)
        traceback.print_exc() # Stampa tutto l'albero dell'errore
        print("----------------------------------\n", flush=True)
        
        # Mostriamo l'errore a video solo se non è un segreto
        st.error("❌ Errore tecnico. Controlla i logs nella dashboard.")
        return []