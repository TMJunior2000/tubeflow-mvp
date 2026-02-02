import edge_tts
import asyncio
import uuid
import os

async def _create_voice_file(text, voice, rate, output_file):
    """Funzione asincrona interna per comunicare con Edge TTS"""
    # Rate deve essere stringa esatta: "+10%" o "-10%"
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(output_file)

def generate_voiceover_file(text, voice, speed_rate="+0%"):
    """
    Genera audio con controllo velocità (intonazione indiretta).
    Include gestione errori per formato stringa e asyncio loop per Streamlit.
    """
    
    # --- 1. SANIFICAZIONE INPUT VELOCITÀ ---
    # Gemini potrebbe restituire "10%", " 10 %", o "+10". edge-tts richiede "+10%" esatto.
    if not speed_rate:
        speed_rate = "+0%"
        
    clean_rate = str(speed_rate).replace(" ", "").strip()
    
    # Se manca il simbolo %, aggiungilo
    if "%" not in clean_rate:
        clean_rate += "%"
    
    # Se manca il segno + o -, aggiungi + (assumiamo incremento positivo)
    if not clean_rate.startswith(("+", "-")):
        clean_rate = "+" + clean_rate
        
    # Fallback di sicurezza se la stringa è corrotta o vuota
    if len(clean_rate) < 3: 
        clean_rate = "+0%"

    # --- 2. NOME FILE UNIVOCO ---
    # Usiamo UUID per evitare conflitti di scrittura se l'utente rigenera velocemente
    output_path = f"voice_{uuid.uuid4().hex}.mp3"

    try:
        # --- 3. GESTIONE ASYNCIO PER STREAMLIT ---
        # Streamlit gira in un thread loop proprietario. asyncio.run() puro può fallire.
        # Creiamo un nuovo loop specifico per questa operazione.
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(_create_voice_file(text, voice, clean_rate, output_path))
            loop.close()
        except RuntimeError:
            # Fallback per ambienti dove il loop è già gestito diversamente
            asyncio.run(_create_voice_file(text, voice, clean_rate, output_path))

        # Verifica finale: il file esiste?
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return output_path
        else:
            print("TTS Error: File creato ma vuoto o inesistente.")
            return None

    except Exception as e:
        print(f"TTS Critical Error: {e}")
        return None