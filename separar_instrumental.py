"""
separar_instrumental.py

Usa o Demucs para separar o instrumental e os vocais de um arquivo de áudio.

Requisitos:
- demucs (e suas dependências, incluindo torch e torchaudio)
- ffmpeg instalado e no PATH do sistema

Este script carrega um modelo pré-treinado do Demucs e o aplica a um arquivo
de áudio de entrada. Ele salva as faixas separadas (instrumental e vocais)
em um diretório de saída especificado.
"""

import torch
import torchaudio
from demucs.apply import apply_model
from demucs.pretrained import get_model
from demucs.audio import AudioFile
import argparse
from pathlib import Path

def separar_faixas(audio_path, output_dir, model_name= "htdemucs_6s"): #"htdemucs_ft"):
    """
    Separa as faixas de um arquivo de áudio usando Demucs.

    Args:
        audio_path (str): Caminho para o arquivo de áudio.
        output_dir (str): Diretório para salvar as faixas separadas.
        model_name (str): Nome do modelo Demucs a ser usado.
    """
    if not torch.cuda.is_available():
        print("Erro: A GPU (CUDA) não está disponível. Verifique a instalação do PyTorch e dos drivers da NVIDIA.")
        exit(1)
    device = "cuda"
    print(f"Usando dispositivo: {device}")

    print(f"Carregando modelo Demucs: {model_name}...")
    model = get_model(name=model_name)
    model.to(device)

    print(f"Carregando áudio: {audio_path}...")
    wav = AudioFile(audio_path).read(streams=0, samplerate=model.samplerate, channels=model.audio_channels)
    wav = wav.to(device)
    ref = wav.mean(0)
    wav = (wav - ref.mean()) / ref.std()

    print("Separando as fontes de áudio... (Isso pode levar um tempo)")
    sources = apply_model(model, wav[None], device=device, progress=True, num_workers=4)[0]
    sources = sources * ref.std() + ref.mean()

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print("Salvando faixas separadas...")
    for source, name in zip(sources, model.sources):
        stem = output_path / f"{name}.wav"
        torchaudio.save(str(stem), source.cpu(), sample_rate=model.samplerate)
        print(f"  - Faixa salva: {stem}")

    print("\nSeparação concluída!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Separa instrumental e vocais de um arquivo de áudio usando Demucs.")
    parser.add_argument("--audio", default="audio_base", help="Diretório ou arquivo de áudio (default: audio_base).")
    parser.add_argument("--out_dir", default="audio_separado", help="Diretório de saída para as faixas separadas (default: audio_separado).")
    args = parser.parse_args()

    audio_dir = Path(args.audio)
    
    # Se o argumento for um arquivo, usa-o. Se for um diretório, pega o primeiro mp3.
    if audio_dir.is_file():
        audio_file = audio_dir
    elif audio_dir.is_dir():
        audio_files = list(audio_dir.glob("*.mp3"))
        if not audio_files:
            print(f"Erro: Nenhum arquivo .mp3 encontrado em '{audio_dir}'")
            sys.exit(1)
        audio_file = audio_files[0]
    else:
        print(f"Erro: O caminho especificado '{audio_dir}' não é um arquivo ou diretório válido.")
        sys.exit(1)
    audio_files = list(audio_dir.glob("*.mp3"))
    if not audio_files:
        print(f"Erro: Nenhum arquivo .mp3 encontrado em '{audio_dir}'")
        exit(1)
    audio_file = audio_files[0]

    print(f"Usando arquivo de áudio: {audio_file}")

    output_dir_base = Path(args.out_dir)    
    output_dir = output_dir_base / audio_file.stem

    print(f"As faixas serão salvas em: {output_dir}")

    separar_faixas(str(audio_file), str(output_dir))
