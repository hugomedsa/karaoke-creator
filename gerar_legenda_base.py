"""
gerar_legenda.py
Gera arquivo de legenda (.srt) com timestamps das partes cantadas, usando o áudio mp3 e a letra da música.
Requisitos: pip install openai-whisper srt
"""

import whisper
from typing import Any
import srt
from pathlib import Path

# Função para transcrever áudio e obter segmentos
def transcrever_audio(audio_path, model_size="large-v3"): #try "medium" and large-v3
    model = whisper.load_model(model_size)
    result = model.transcribe(str(audio_path), word_timestamps=True)
    return result['segments']


# Função para gerar legendas SRT a partir dos segmentos
def gerar_srt(segments, output_path):
    subs = []
    for i, seg in enumerate[Any](segments):
        subs.append(srt.Subtitle(
            index=i+1,
            start=srt.timedelta(seconds=seg['start']),
            end=srt.timedelta(seconds=seg['end']),
            content=seg['text']

        ))
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(srt.compose(subs))
    print(f"Legenda gerada em: {output_path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Gera legenda SRT a partir de áudio MP3 usando Whisper.")
    parser.add_argument("--audio", required=False, help="Caminho do arquivo MP3 (pasta audio/)")
    parser.add_argument("--out", default=None, help="Arquivo de saída SRT (pasta subtitles/)")
    args = parser.parse_args()

    if not args.audio:
        base_dir = Path("audio_base")
        mp3s = list(base_dir.glob("*.mp3"))
        if not mp3s:
            raise FileNotFoundError("Nenhum arquivo .mp3 encontrado na pasta audio_base/")
        args.audio = str(mp3s[0])
    
    print("Transcrevendo áudio...")
    segmentos = transcrever_audio(args.audio)
    out_path = args.out or f"subtitle_srt/{Path(args.audio).stem}.srt"
    Path("subtitle_srt").mkdir(exist_ok=True)
    gerar_srt(segmentos, out_path)