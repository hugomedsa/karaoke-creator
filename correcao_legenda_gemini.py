"""
correcao_legenda_gemini.py
Corrige legendas SRT geradas por Whisper usando a letra original da música e o modelo Gemini-2.5-flash.
Requisitos: python-dotenv, google-generativeai
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai


def ler_arquivo(path):
    with open(path, encoding="utf-8") as f:
        return f.read()

def corrigir_legenda_gemini(legenda_srt, letra):
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise Exception("GEMINI_API_KEY não configurada")

    genai.configure(api_key=api_key)
    config_genai = {
        "temperature": 0.2,
        "top_p": 1,
        "max_output_tokens": 2048
    }
    prompt = (
        "Você é um assistente de legendas para karaokê. Recebe uma legenda SRT e a letra original da música. "
        "Corrija apenas os trechos que não estejam gramaticalmente ou literalmente corretos, sem alucinar, mantendo os timestamps. "
        "Retorne o arquivo SRT corrigido.\n\nLetra:\n" + letra + "\n\nLegenda SRT:\n" + legenda_srt
    )
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(
        prompt,
        generation_config=config_genai
    )
    return response.text

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Corrige legenda SRT usando Gemini-2.5-flash e letra da música.")
    parser.add_argument("--srt", required=True, help="Arquivo SRT gerado pela transcrição (pasta subtitles/)")
    parser.add_argument("--letra", required=True, help="Arquivo de letra (pasta lyrics/)")
    parser.add_argument("--out", default=None, help="Arquivo de saída SRT corrigido (pasta subtitles/)")
    args = parser.parse_args()

    legenda_srt = ler_arquivo(args.srt)
    letra = ler_arquivo(args.letra)
    print("Corrigindo legenda com Gemini-2.5-flash...")
    legenda_corrigida = corrigir_legenda_gemini(legenda_srt, letra)
    out_path = args.out or args.srt.replace(".srt", "_corrigida.srt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(legenda_corrigida)
    print(f"Legenda corrigida salva em: {out_path}")
