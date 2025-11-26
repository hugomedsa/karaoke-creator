"""
gerar_legenda.py
Gera arquivo de legenda (.srt) com timestamps das partes cantadas, usando o áudio mp3 e a letra da música.
Requisitos: pip install openai-whisper srt
"""

import whisper
import srt
from pathlib import Path

# Função para transcrever áudio e obter segmentos
def transcrever_audio(audio_path, model_size="small"):
    model = whisper.load_model(model_size)
    result = model.transcribe(str(audio_path), word_timestamps=True)
    return result['segments']

# Função para ler letra da música
def ler_letra(letra_path):
    with open(letra_path, encoding="utf-8") as f:
        return f.read()

# Função para gerar legendas SRT a partir dos segmentos
def gerar_srt(segments, output_path):
    subs = []
    for i, seg in enumerate(segments):
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
    parser = argparse.ArgumentParser(description="Gera legenda SRT a partir de áudio MP3 e letra da música.")
    parser.add_argument("--audio", required=True, help="Caminho do arquivo MP3")
    parser.add_argument("--letra", required=True, help="Caminho do arquivo de letra (txt)")
    parser.add_argument("--out", default="legenda.srt", help="Arquivo de saída SRT")
    args = parser.parse_args()

    print("Transcrevendo áudio...")
    segmentos = transcrever_audio(args.audio)
    print("Lendo letra...")
    letra = ler_letra(args.letra)
    # (Opcional) Alinhar letra com transcrição para melhorar precisão
    # Aqui, apenas salva a transcrição como legenda
    gerar_srt(segmentos, args.out)
