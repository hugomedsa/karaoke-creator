"""
gerar_legenda.py
Gera arquivo de legenda (.srt) com timestamps das partes cantadas, usando o áudio mp3 e a letra da música.
Requisitos: pip install openai-whisper srt
"""

import whisper
import srt
from pathlib import Path
import os
import requests
from dotenv import load_dotenv
# Função para validar/corrigir legendas usando Gemini
def corrigir_legenda_gemini(legenda_srt, letra, gemini_api_key):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
    headers = {"Content-Type": "application/json"}
    prompt = (
        "Você é um assistente de legendas para karaokê. Recebe uma legenda SRT e a letra original da música. "
        "Corrija apenas os trechos que não estejam gramaticalmente ou literalmente corretos, sem alucinar, mantendo os timestamps. "
        "Retorne o arquivo SRT corrigido.\n\nLetra:\n" + letra + "\n\nLegenda SRT:\n" + legenda_srt
    )
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    params = {"key": gemini_api_key}
    response = requests.post(url, headers=headers, params=params, json=data)
    if response.status_code == 200:
        # Gemini retorna o texto corrigido em response.json()['candidates'][0]['content']['parts'][0]['text']
        try:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        except Exception:
            print("Erro ao extrair resposta do Gemini:", response.text)
            return legenda_srt
    else:
        print("Erro na requisição Gemini:", response.text)
        return legenda_srt

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
    parser.add_argument("--audio", required=True, help="Caminho do arquivo MP3 (pasta audio/)")
    parser.add_argument("--letra", required=True, help="Caminho do arquivo de letra (pasta lyrics/)")
    parser.add_argument("--out", default=None, help="Arquivo de saída SRT (pasta subtitles/)")
    parser.add_argument("--corrigir", action="store_true", help="Valida/corrige a legenda usando Gemini e a letra")
    args = parser.parse_args()

    print("Transcrevendo áudio...")
    segmentos = transcrever_audio(args.audio)
    print("Lendo letra...")
    letra = ler_letra(args.letra)
    out_path = args.out or f"subtitles/{Path(args.audio).stem}.srt"
    Path("subtitles").mkdir(exist_ok=True)
    # Gera legenda inicial
    gerar_srt(segmentos, out_path)

    # (Opcional) Alinhar letra com transcrição para melhorar precisão
    if args.corrigir:
        print("Validando/corrigindo legenda com Gemini...")
        load_dotenv()
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        with open(out_path, encoding="utf-8") as f:
            legenda_srt = f.read()
        legenda_corrigida = corrigir_legenda_gemini(legenda_srt, letra, gemini_api_key)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(legenda_corrigida)
        print(f"Legenda corrigida salva em: {out_path}")
