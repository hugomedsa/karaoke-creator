#!/usr/bin/env python3
"""download_youtube_mp3.py
Baixa apenas o áudio de um vídeo do YouTube em formato MP3.
Requisitos: pip install yt_dlp ; ffmpeg no PATH
"""

from pathlib import Path
from yt_dlp import YoutubeDL
import sys
from pydub import AudioSegment

def progress_hook(d):
    status = d.get('status')
    if status == 'downloading':
        total = d.get('total_bytes') or d.get('total_bytes_estimate')
        dl = d.get('downloaded_bytes', 0)
        if total:
            pct = dl / total * 100
            sys.stdout.write(f"\rBaixando: {pct:5.1f}%")
        else:
            sys.stdout.write(f"\rBaixando: {dl} bytes")
        sys.stdout.flush()
    elif status == 'finished':
        print(f"\nConcluído: {d.get('filename')}")

def download_youtube_audio(video_url: str, output_dir: str = "musicas", trim_seconds: int = 90): # Para audio inteiro, colocar trim_seconds: None
    outdir = Path(output_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': str(outdir / '%(title)s.%(ext)s'),
        'restrictfilenames': True,
        'noplaylist': True,
        'progress_hooks': [progress_hook],
        'quiet': False,
        'no_warnings': True,
        'prefer_ffmpeg': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=True)
        raw_name = ydl.prepare_filename(info)
        final = Path(raw_name).with_suffix('.mp3')
        print(f"Arquivo salvo como: {final}")

        # Se trim_seconds for definido, corta o áudio
        if trim_seconds is not None:
            try:
                audio = AudioSegment.from_file(final)
                audio_cortado = audio[:trim_seconds * 1000]
                audio_cortado.export(final, format="mp3")
                print(f"Áudio cortado para {trim_seconds} segundos: {final}")
            except Exception as e:
                print(f"Erro ao cortar áudio: {e}")
        return str(final)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Baixa apenas o áudio de vídeos do YouTube em MP3.")
    parser.add_argument('url', help='URL do vídeo (YouTube).')
    parser.add_argument('--out', default='musicas', help='Pasta de saída (padrão: musicas)')
    parser.add_argument('--trim', type=int, default=None, help='Corta o áudio para os primeiros N segundos (ex: 90 para 1m30s)')
    args = parser.parse_args()

    print(f"Iniciando download de: {args.url}")
    try:
        download_youtube_audio(args.url, output_dir=args.out, trim_seconds=args.trim)
    except Exception as e:
        print("Erro:", e)
