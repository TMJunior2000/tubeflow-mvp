import asyncio
from typing import Optional
import edge_tts
import tempfile

async def _generate_tts_async(text, voice, output_path):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

def generate_voiceover_file(text: str, voice: str = "en-US-ChristopherNeural") -> Optional[str]:
    """
    Crea un MP3 temporaneo e ritorna il path (o i bytes).
    """
    try:
        # File temporaneo che non si cancella subito
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        temp_file.close()
        
        # Esecuzione Async in contesto Sync
        asyncio.run(_generate_tts_async(text, voice, temp_file.name))
        
        return temp_file.name
    except Exception as e:
        print(f"TTS Error: {e}")
        return None