import streamlit as st
import os
import json
from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import List

# --- DATA MODELS ---
class Scene(BaseModel):
    scene_number: int
    voiceover: str
    keyword: str
    duration: int

class VoiceSettings(BaseModel):
    voice_speed: str

class VideoScript(BaseModel):
    voice_settings: VoiceSettings
    scenes: List[Scene]

def generate_script(topic: str) -> dict:
    api_key = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
    if not api_key:
        st.error("⚠️ API Key missing.")
        return None

    try:
        client = genai.Client(http_options={'api_version': 'v1alpha'}, api_key=api_key)
        
        target_schema = {
            "type": "OBJECT",
            "properties": {
                "voice_settings": {
                    "type": "OBJECT",
                    "properties": { "voice_speed": {"type": "STRING"} },
                    "required": ["voice_speed"]
                },
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
            "required": ["voice_settings", "scenes"]
        }

        # --- IL PROMPT DEFINITIVO (Basato su Documentazione API) ---
        system_instruction = """
        Sei TubeFlow v3, un Curatore esperto di Stock Footage ottimizzato per le API di Pexels e Pixabay.
        Il tuo compito è generare query di ricerca che sfruttino i parametri nativi di questi database.

        --- REGOLE DI RICERCA API (PEXELS & PIXABAY) ---
        - TRADUZIONE FISICA: I database sono testuali. Converti concetti astratti in OGGETTI REALI.
            * Esempio: "Disciplina" -> "Man waking up early" o "Cold water splash face".
        - KEYWORD FORMAT: [Soggetto] + [Ambiente] + [Stile]. Solo INGLESE (max 4 parole).
        - CATEGORIE API PIXABAY: Se pertinente, orienta la ricerca verso categorie supportate: 
          (nature, science, education, feelings, health, people, religion, places, animals, industry, computer, food, sports, transportation, travel, buildings, business, music).
        - TAG QUALITÀ: Includi sempre tag tecnici come '4k', 'Cinematic', 'Slow motion', 'Macro', o 'Drone'.

        --- STRATEGIA DI MONTAGGIO (META 2026) ---
        - DURATA: Ogni scena DEVE avere una durata tra 2 e 4 secondi per massimizzare la retention (Dopamina).
        - NUMERO CLIP: Se l'utente specifica un numero (es. 7 clip), genera ESATTAMENTE quel numero di scene.
        - HOOK: La Scena 1 deve essere un impatto visivo estremo (es. "Extreme close up" o "Explosion").

        --- LOGICA AUDIO ---
        - Voiceover incalzante per adattarsi ai tagli rapidi.
        - Velocità: +10% per contenuti dinamici, -10% per contenuti profondi/noir.

        MANDATORIO: Restituisci SOLO un oggetto JSON pulito. Nessun decimale nelle durate.
        """

        response = client.models.generate_content(
            model="gemini-3-flash-preview", 
            contents=f"RICHIESTA UTENTE: {topic}. Ricorda: Tagli veloci (2-4s), usa keyword inglesi ottimizzate per API.",
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                thinking_config=types.ThinkingConfig(thinking_level=types.ThinkingLevel.LOW),
                temperature=1.0,
                response_mime_type="application/json",
                response_schema=target_schema 
            )
        )

        raw_data = json.loads(response.text)
        if isinstance(raw_data, list): raw_data = raw_data[0]
            
        return VideoScript.model_validate(raw_data).model_dump()

    except Exception as e:
        st.error(f"AI Engine Error: {str(e)}")
        return None