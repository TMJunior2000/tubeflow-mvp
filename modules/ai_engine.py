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

class VoiceSettings(BaseModel):
    voice_speed: str

class VideoScript(BaseModel):
    voice_settings: VoiceSettings
    scenes: List[Scene]

def generate_script(topic: str) -> dict:
    api_key = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
    if not api_key:
        st.error("⚠️ API Key mancante.")
        return None

    try:
        client = genai.Client(api_key=api_key)
        
        system_instruction = """
        Sei TubeFlow v3, un Regista AI capace di adattare il montaggio allo stile del contenuto.
        Il tuo obiettivo è decidere autonomamente come strutturare le clip (Pexels/Pixabay) in base alla richiesta.

        ---------------------------------------------------------
        DINAMICA DI MONTAGGIO (IL TUO GIUDIZIO)
        Non esiste una regola fissa, ma segui questa logica editoriale:
        
        1. STRATEGIA "MONO-CLIP" (POV / Mood / Deep):
           - Se l'utente chiede un video riflessivo, estetico o un'atmosfera singola, puoi usare UNA sola clip lunga (es. 15-30s).
           - In questo caso, lo script scorre tutto su un'unica immagine potente.
        
        2. STRATEGIA "MULTI-CLIP" (Tutorial / Listicle / Fast Facts):
           - Se il contenuto è informativo o ritmato, usa tagli frequenti (2-5s per clip).
           - Cambia clip ogni volta che l'argomento trattato nello script cambia.
        
        3. RISPETTO DEGLI ORDINI:
           - Se l'utente specifica "X clip", dimentica la tua strategia e genera esattamente X scene.

        REGOLE VISIVE (PEXELS/PIXABAY)
        - Traduci concetti astratti in OGGETTI CONCRETI.
        - KEYWORD: [Soggetto] + [Ambiente]. Solo INGLESE, max 3 parole.
        - Se usi una clip singola lunga, assicurati che la keyword cerchi qualcosa di visivamente "ricco" (es: "Night city timelapse", "Forest stream flow").

        VELOCITÀ VOCE & TONO
        - Adatta la velocità (-10%, +0%, +10%) al "vibe" del video.
        - Lo script deve essere naturale, evita i cliché banali e punta al coinvolgimento.

        OUTPUT: Oggetto JSON valido corrispondente allo schema.
        """
        
        manual_schema = {
            "type": "OBJECT",
            "properties": {
                "voice_settings": {
                    "type": "OBJECT",
                    "properties": {
                        "voice_speed": {"type": "STRING"}
                    },
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

        response = client.models.generate_content(
            model="gemini-1.5-flash", 
            contents=f"RICHIESTA UTENTE: {topic}",
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=manual_schema,
                temperature=0.8 # Un po' di varietà in più
            )
        )

        if not response.text:
            return None
        
        return VideoScript.model_validate_json(response.text).model_dump()

    except Exception as e:
        st.error(f"AI Error: {str(e)}")
        return None