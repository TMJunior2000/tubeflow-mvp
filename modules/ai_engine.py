import json
import streamlit as st
import os
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
    """
    Genera lo script usando l'SDK Unificato google-genai con gestione errori Human-Friendly.
    """
    
    # 1. Recupero API Key
    api_key = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
    if not api_key:
        # Errore interno (non colpa dell'utente), mostriamo un messaggio generico
        st.error("⚠️ Servizio momentaneamente non disponibile (Configurazione mancante).")
        return []

    # 2. Inizializzazione Client
    try:
        client = genai.Client(api_key=api_key)
    except Exception:
        st.error("⚠️ Errore di connessione ai servizi AI.")
        return []
    
    # 3. Preparazione Prompt (Versione Human-Centric)
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
    
    OUTPUT: Restituisci SOLO un array JSON valido.
    """
    
    user_prompt = f"TOPIC: {topic}\nVIBE: {vibe}\nLUNGHEZZA: 30-60 secondi."

    try:
        # 4. Chiamata API (Usiamo il modello stabile 1.5)
        response = client.models.generate_content(
            model="gemini-1.5-flash", 
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=VideoScript,
                temperature=0.7
            )
        )
        
        # 5. Parsing & Validazione
        if not response.text:
            st.warning("🤔 L'AI non ha saputo rispondere a questo argomento. Prova a riformulare.")
            return []

        try:
            script_obj = VideoScript.model_validate_json(response.text)
            return [scene.model_dump() for scene in script_obj.scenes]
        except Exception:
            st.warning("Format error. Riprova, a volte l'AI si confonde.")
            return []

    # --- 🛡️ GESTIONE ERRORI "HUMAN FRIENDLY" ---
    except Exception as e:
        error_msg = str(e)
        
        # Caso 1: Troppe richieste (429 Quota Exceeded)
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
             st.warning("🚦 Traffico intenso sui server AI! Siamo in Free Tier, attendi 30 secondi e riprova.")
             # Non stampiamo nulla di tecnico a schermo
             return []
        
        # Caso 2: Contenuto bloccato (Safety Filters)
        elif "finish_reason" in error_msg and "SAFETY" in error_msg:
            st.warning("🛡️ L'AI si è rifiutata di generare questo contenuto per motivi di sicurezza. Cambia argomento.")
            return []
            
        # Caso 3: Errore generico (Internet, Server Down, ecc.)
        else:
            # Messaggio vago ma utile per l'utente
            st.error("❌ Errore di comunicazione con il cervello digitale. Riprova tra poco.")
            # Stampiamo l'errore vero SOLO nella console dello sviluppatore (invisibile all'utente)
            print(f"DEBUG LOG (Hidden from user): {error_msg}")
            return []