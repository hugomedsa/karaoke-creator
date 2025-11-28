"""
criar_video_karaoke.py

Combina as faixas instrumentais (tudo exceto vocals.wav) de uma pasta audio_separado
com uma legenda .ass para criar um vídeo MP4 de karaokê completo.

Requisitos:
- ffmpeg instalado e no PATH
- pydub (para processamento de áudio)
"""

import argparse
from pathlib import Path
import subprocess
import sys
from pydub import AudioSegment

def combinar_faixas_instrumentais(pasta_audio_separado, arquivo_saida_audio):
    """
    Combina todas as faixas instrumentais (exceto vocals.wav) em um único arquivo de áudio.
    
    Args:
        pasta_audio_separado (Path): Caminho para a pasta com as faixas separadas
        arquivo_saida_audio (Path): Caminho para salvar o áudio combinado
    """
    print(f"Combinando faixas instrumentais de: {pasta_audio_separado}")
    
    # Encontrar todos os arquivos .wav exceto vocals.wav
    arquivos_audio = []
    for arquivo in pasta_audio_separado.glob("*.wav"):
        if arquivo.name != "vocals.wav":
            arquivos_audio.append(arquivo)
            print(f"  - Adicionando: {arquivo.name}")
    
    if not arquivos_audio:
        raise ValueError(f"Nenhuma faixa instrumental encontrada em {pasta_audio_separado}")
    
    # Carregar e combinar as faixas
    audio_combinado = None
    for arquivo in arquivos_audio:
        audio = AudioSegment.from_wav(arquivo)
        if audio_combinado is None:
            audio_combinado = audio
        else:
            audio_combinado = audio_combinado.overlay(audio)
    
    # Exportar áudio combinado
    audio_combinado.export(arquivo_saida_audio, format="mp3", bitrate="192k")
    print(f"Áudio instrumental combinado salvo em: {arquivo_saida_audio}")

def criar_video_com_legenda(arquivo_audio, arquivo_legenda, arquivo_saida_video):
    """
    Cria um vídeo MP4 com áudio instrumental e legenda .ass embutida.
    
    Args:
        arquivo_audio (Path): Arquivo de áudio combinado
        arquivo_legenda (Path): Arquivo de legenda .ass
        arquivo_saida_video (Path): Caminho para salvar o vídeo final
    """
    print(f"Criando vídeo com legenda...")
    
    # Comando ffmpeg para criar vídeo com áudio e legenda
    comando = [
        "ffmpeg",
        "-y",  # Sobrescrever arquivo existente
        "-i", str(arquivo_audio),  # Arquivo de áudio de entrada
        "-vf", f"ass={arquivo_legenda}",  # Filtro de vídeo para a legenda
        "-c:a", "aac",  # Codec de áudio
        "-b:a", "192k",  # Bitrate de áudio
        "-c:v", "libx264",  # Codec de vídeo
        "-preset", "medium",  # Preset de encoding
        "-crf", "23",  # Qualidade do vídeo
        "-pix_fmt", "yuv420p",  # Formato de pixel compatível
        "-shortest",  # Terminar quando o áudio acabar
        str(arquivo_saida_video)
    ]
    
    try:
        print("Executando ffmpeg... (isso pode levar alguns minutos)")
        resultado = subprocess.run(comando, check=True, capture_output=True, text=True)
        print(f"Vídeo criado com sucesso: {arquivo_saida_video}")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar ffmpeg: {e}")
        print(f"Stderr: {e.stderr}")
        raise

def main():
    parser = argparse.ArgumentParser(description="Cria vídeo de karaokê combinando faixas instrumentais e legenda .ass")
    parser.add_argument("--pasta_audio", required=True, help="Pasta com as faixas separadas (ex: audio_separado/nome_musica)")
    parser.add_argument("--legenda", required=True, help="Arquivo de legenda .ass")
    parser.add_argument("--nome_saida", help="Nome do arquivo de saída (sem extensão)")
    
    args = parser.parse_args()
    
    pasta_audio = Path(args.pasta_audio)
    arquivo_legenda = Path(args.legenda)
    
    if not pasta_audio.exists():
        print(f"Erro: Pasta de áudio não encontrada: {pasta_audio}")
        sys.exit(1)
    
    if not arquivo_legenda.exists():
        print(f"Erro: Arquivo de legenda não encontrado: {arquivo_legenda}")
        sys.exit(1)
    
    # Criar pasta de saída
    pasta_saida = Path("karaokes_completos")
    pasta_saida.mkdir(exist_ok=True)
    
    # Nome do arquivo de saída
    if args.nome_saida:
        nome_base = args.nome_saida
    else:
        nome_base = pasta_audio.name
    
    # Caminhos dos arquivos
    arquivo_audio_temp = pasta_saida / f"{nome_base}_instrumental.mp3"
    arquivo_video_final = pasta_saida / f"{nome_base}_karaoke.mp4"
    
    # Processar
    combinar_faixas_instrumentais(pasta_audio, arquivo_audio_temp)
    criar_video_com_legenda(arquivo_audio_temp, arquivo_legenda, arquivo_video_final)
    
    # Limpar arquivo temporário
    arquivo_audio_temp.unlink()
    print(f"Processo concluído! Vídeo salvo em: {arquivo_video_final}")

if __name__ == "__main__":
    main()