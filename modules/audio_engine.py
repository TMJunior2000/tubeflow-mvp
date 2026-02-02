import edge_tts
import asyncio
import os

async def _create_voice_file(text, voice, rate, output_file):
    # Rate format: "+10%" or "-10%"
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(output_file)

def generate_voiceover_file(text, voice, speed_rate="+0%"):
    """Genera audio con controllo velocità (intonazione indiretta)"""
    output_path = "voiceover.mp3"
    try:
        asyncio.run(_create_voice_file(text, voice, speed_rate, output_path))
        return output_path
    except Exception as e:
        print(f"TTS Error: {e}")
        return None