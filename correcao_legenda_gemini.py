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


def extrair_texto_resposta(response):
    """
    Extrai texto de uma resposta do Gemini com tolerância a casos bloqueados ou sem parts.
    Lança uma exceção com detalhes úteis quando não houver conteúdo utilizável.
    """
    try:
        # Tenta via acessor rápido
        return response.text
    except Exception:
        candidates = getattr(response, "candidates", []) or []
        if not candidates:
            feedback = getattr(response, "prompt_feedback", None)
            raise RuntimeError(f"Resposta vazia ou bloqueada. prompt_feedback={feedback}")

        c0 = candidates[0]
        finish = getattr(c0, "finish_reason", None)
        parts = getattr(getattr(c0, "content", None), "parts", []) or []
        text_parts = [getattr(p, "text", "") for p in parts if hasattr(p, "text")]
        if text_parts and any(tp for tp in text_parts):
            return "".join(text_parts)

        feedback = getattr(response, "prompt_feedback", None)
        raise RuntimeError(f"Resposta sem texto (finish_reason={finish}). Detalhes={feedback}")

def corrigir_legenda_gemini(legenda_srt, letra):
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise Exception("GEMINI_API_KEY não configurada")

    genai.configure(api_key=api_key)
    config_genai = {
        "temperature": 0.2,
        "top_p": 1,
        # Aumenta o limite para evitar finish_reason = MAX_TOKENS
        "max_output_tokens": 8192,
    }
    # Relaxe bloqueios de segurança, pois letras de música podem conter termos sensíveis
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUAL", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]
    prompt = (
        "Você é um assistente de legendas para karaokê. Recebe uma legenda SRT e a letra original da música. "
        "Corrija apenas os trechos que não estejam gramaticalmente ou literalmente corretos, sem alucinar, mantendo os timestamps e as palavras na linha em que já estão."
        "Não mude as palavras para linhas diferentes."
        "Responda exclusivamente com o conteúdo SRT corrigido, sem comentários ou explicações."
        "\n\nLetra:\n" + letra + "\n\nLegenda SRT:\n" + legenda_srt
    )
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(
        prompt,
        generation_config=config_genai,
        safety_settings=safety_settings,
    )
    return extrair_texto_resposta(response)

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
    try:
        legenda_corrigida = corrigir_legenda_gemini(legenda_srt, letra)
    except Exception as e:
        print(f"Falha ao corrigir a legenda: {e}")
        # Como fallback, salva a legenda original para não perder o fluxo
        legenda_corrigida = legenda_srt
    out_path = args.out or args.srt.replace(".srt", "_corrigida.srt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(legenda_corrigida)
    print(f"Legenda corrigida salva em: {out_path}")
