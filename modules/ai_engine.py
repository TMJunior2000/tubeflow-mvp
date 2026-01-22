import json
import streamlit as st
import os
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List, Optional

# --- DEFINIZIONE STRUTTURA DATI (PYDANTIC) ---
class Scene(BaseModel):
    scene_number: int = Field(..., description="Numero progressivo della scena")
    voiceover: str = Field(..., description="Il testo che lo speaker deve dire (max 20 parole)")
    keyword: str = Field(..., description="UNA singola parola chiave IN INGLESE per la ricerca video (es. 'sunset', 'coding')")
    duration: int = Field(..., description="Durata stimata della scena in secondi")

class VideoScript(BaseModel):
    scenes: List[Scene]

def generate_script(topic: str, vibe: str) -> List[dict]:
    """
    Genera lo script usando l'SDK Unificato google-genai con gestione Type-Safe.
    """
    
    # 1. Recupero API Key
    api_key = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
    if not api_key:
        st.error("❌ Errore API Key: Manca la configurazione di Google.")
        return []

    # 2. Inizializzazione Client
    client = genai.Client(api_key=api_key)
    
    # 3. Preparazione Prompt (AGGIORNATO PER EVITARE CANI/GATTI)
    system_instruction = """
    Sei un Regista esperto di YouTube Shorts e TikTok.
    Il tuo compito è creare una SCALETTA DI PRODUZIONE VIDEO (Script + Visuals).
    
    Regole:
    1. Struttura il video in 3-5 scene brevi.
    2. Per ogni scena, scrivi il 'voiceover' (max 20 parole).
    3. Per ogni scena, fornisci una 'visual_keyword' IN INGLESE.
    
    REGOLA D'ORO PER I VISUAL (PER EVITARE ERRORI):
    - Devi SEMPRE specificare il SOGGETTO UMANO se l'azione è umana.
    - NON scrivere mai solo l'azione (es. NO "drinking water", NO "running").
    - SCRIVI: "Soggetto + Azione + Contesto + Stile".
    
    Esempi di correzione:
    - Sbagliato: "drinking water" (Esce un cane) -> Corretto: "handsome man drinking water glass kitchen"
    - Sbagliato: "stretching" -> Corretto: "girl yoga morning living room"
    - Sbagliato: "writing" -> Corretto: "pov hand writing notebook desk close up"
    - Sbagliato: "focus" -> Corretto: "man working laptop night office neon"

    OUTPUT: Restituisci SOLO un array JSON valido.
    """
    
    user_prompt = f"TOPIC: {topic}\nVIBE: {vibe}\nLUNGHEZZA: 30-60 secondi."

    try:
        # 4. Chiamata API (MODIFICATO IL MODELLO QUI SOTTO)
        response = client.models.generate_content(
            model="gemini-flash-latest",  # <--- CAMBIATO DA 2.0 A 1.5 PER STABILITÀ
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=VideoScript,
                temperature=0.7
            )
        )
        
        # 5. Parsing Type-Safe
        if not response.text:
            st.error("L'AI ha restituito una risposta vuota.")
            return []

        try:
            script_obj = VideoScript.model_validate_json(response.text)
            return [scene.model_dump() for scene in script_obj.scenes]
        except Exception as e:
            st.error(f"Errore nel formato JSON ricevuto: {e}")
            return []

    # --- GESTIONE ERRORE SPECIFICA PER QUOTA (Migliorata) ---
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
             st.warning("🚦 Traffico intenso sui server AI (Errore 429). Attendi 30 secondi e riprova.")
             # Evita di mostrare tutto il JSON brutto all'utente
             print(f"DEBUG ERROR: {error_msg}") 
             return []
        else:
            st.error(f"Errore connessione AI: {e}")
            return []