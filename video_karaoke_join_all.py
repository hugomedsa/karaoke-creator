"""
video_karaoke_join_all.py

Combina automaticamente as faixas instrumentais (tudo exceto vocals.wav),
uma imagem de fundo e legendas .ass para criar vídeos MP4 de karaokê completos.

Funcionamento automático:
- Procura por pastas em audio_separado/
- Usa legendas da pasta subtitle_ass/
- Usa a imagem karaoke-hugo.jpg como padrão
- Salva vídeos em karaokes_completos/

Requisitos:
- ffmpeg instalado e no PATH
- pydub (para processamento de áudio)
"""

import argparse
from pathlib import Path
import subprocess
import sys
import os
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
            print(f"  - Adicionando: {arquivo.name}")
    
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
    audio_combinado.export(arquivo_saida_audio, format="mp3", bitrate="128k")
    print(f"Áudio instrumental combinado salvo em: {arquivo_saida_audio}")

# CORREÇÃO CRÍTICA: Adicionado 'arquivo_imagem' na definição da função
def criar_video_com_legenda(arquivo_audio, arquivo_legenda, arquivo_saida_video, arquivo_imagem):
    """
    Cria um vídeo MP4 com áudio instrumental, imagem de fundo estática e legenda .ass embutida.
    
    Args:
        arquivo_audio (Path): Arquivo de áudio combinado
        arquivo_legenda (Path): Arquivo de legenda .ass
        arquivo_saida_video (Path): Caminho para salvar o vídeo final
        arquivo_imagem (Path): Arquivo de imagem a ser usado como fundo
    """
    print(f"Criando vídeo com imagem e legenda...")

    # 1. Obter a duração do áudio
    try:
        duracao_audio_cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(arquivo_audio)
        ]
        duracao_segundos = subprocess.check_output(duracao_audio_cmd).decode('utf-8').strip()
    except subprocess.CalledProcessError:
        print("Erro: Não foi possível obter a duração do áudio com ffprobe.")
        raise

    # 2. Comando ffmpeg CORRIGIDO
    comando_base = [
        "ffmpeg",
        "-y",               # Sobrescrever arquivo existente
        "-loop", "1",       # Loop na imagem deve vir antes da imagem
        "-i", str(arquivo_imagem),  # 1ª entrada: A imagem (input 0)
        "-i", str(arquivo_audio),   # 2ª entrada: O áudio (input 1)
        "-t", duracao_segundos,     # Define a duração total
        "-vf", f"scale=1280:-2,format=yuv420p,ass={arquivo_legenda}",
        "-c:a", "aac",      # Codec de áudio
        "-b:a", "128k",
        "-shortest",
        str(arquivo_saida_video),
        # "-c:v", "libx264",
        # "-preset", "medium",
        # "-crf", "23",
        "-c:v", "h264_nvenc",
        "-preset", "p4",        # p1-p7 (p4=balanço bom)
        "-cq", "21",            # Qualidade (0-51, menor=melhor)
        "-rc", "vbr",
        "-b:v", "5M",           # Bitrate máximo
        "-gpu", "0",            # ID da GPU
    ]

    try:
        print("Executando ffmpeg... (isso pode levar alguns minutos)")
        subprocess.run(comando_base, check=True, capture_output=True, text=True)
        print(f"Vídeo criado com sucesso: {arquivo_saida_video}")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar ffmpeg: {e}")
        print(f"Stderr: {e.stderr}")
        raise

def encontrar_musicas_e_legendas():
    """Encontra automaticamente todas as músicas com áudio separado e legendas correspondentes."""
    
    # Criar pastas se não existirem
    Path("audio_separado").mkdir(exist_ok=True)
    Path("subtitle_ass").mkdir(exist_ok=True) # Usando o novo nome da pasta
    Path("karaokes_completos").mkdir(exist_ok=True)
    
    print("🔍 Procurando músicas e legendas...")
    
    # Encontrar todas as pastas de áudio separado
    pares = []
    
    for pasta_audio in Path("audio_separado").iterdir():
        if pasta_audio.is_dir():
            nome_musica = pasta_audio.name
            
            # Verificar se existe legenda correspondente na pasta subtitle_ass
            possiveis_legendas = [
                Path("subtitle_ass") / f"{nome_musica}.ass",
                Path("subtitle_ass") / f"{nome_musica}_legenda.ass",
                Path("subtitle_ass") / f"{nome_musica}_subtitles.ass"
            ]
            
            legenda_encontrada = None
            for legenda in possiveis_legendas:
                if legenda.exists():
                    legenda_encontrada = legenda
                    break
            
            if legenda_encontrada:
                pares.append((pasta_audio, legenda_encontrada, nome_musica))
                print(f"  ✅ {nome_musica} - legenda encontrada")
            else:
                print(f"  ⚠️  {nome_musica} - nenhuma legenda encontrada em 'subtitle_ass/'")
    
    return pares

def main():
    parser = argparse.ArgumentParser(description="Cria vídeos de karaokê automaticamente combinando faixas instrumentais e legendas .ass")
    parser.add_argument("--musica", help="Nome específico da música para processar (opcional)")
    # NOVO ARGUMENTO: Imagem de fundo opcional
    parser.add_argument("--imagem", required=False, help="Caminho do arquivo de imagem de fundo (padrão: karaoke-hugo.jpg).")
    
    args = parser.parse_args()
    
    # Encontrar todas as músicas com legendas
    pares = encontrar_musicas_e_legendas()
    
    if not pares:
        print("❌ Nenhuma música com legenda encontrada!")
        print("\n📋 Estrutura esperada:")
        print("audio_separado/nome_da_musica/ [com arquivos .wav separados]")
        print("subtitle_ass/nome_da_musica.ass [arquivo de legenda]") # CORREÇÃO: nome da pasta
        sys.exit(1)
    
    # Filtrar por música específica se solicitado
    if args.musica:
        pares = [(pasta, legenda, nome) for pasta, legenda, nome in pares if nome == args.musica]
        if not pares:
            print(f"❌ Música '{args.musica}' não encontrada ou sem legenda")
            sys.exit(1)
    
    print(f"\n🎵 Encontradas {len(pares)} música(s) com legendas:")

    # Definir o caminho da imagem de fundo com fallback (lógica automática)
    ARQUIVO_IMAGEM_FUNDO = Path(args.imagem) if args.imagem else Path("karaoke-hugo.jpg")
    
    if not ARQUIVO_IMAGEM_FUNDO.exists():
        print(f"❌ Erro: Imagem de fundo '{ARQUIVO_IMAGEM_FUNDO}' não encontrada.")
        print("Certifique-se de que a imagem 'karaoke-hugo.jpg' ou a imagem especificada exista no diretório de execução.")
        sys.exit(1)
        
    print(f"🖼️ Usando imagem de fundo: {ARQUIVO_IMAGEM_FUNDO}")

    # Processar cada música
    for pasta_audio, arquivo_legenda, nome_musica in pares:
        print(f"\n🎤 Processando: {nome_musica}")
        print(f"   Áudio: {pasta_audio}")
        print(f"   Legenda: {arquivo_legenda}")
        
        # Caminhos dos arquivos
        pasta_saida = Path("karaokes_completos")
        arquivo_audio_temp = pasta_saida / f"{nome_musica}_instrumental.mp3"
        arquivo_video_final = pasta_saida / f"{nome_musica}_karaoke.mp4"
        
        # Processar
        try:
            combinar_faixas_instrumentais(pasta_audio, arquivo_audio_temp)
            # Passar o caminho da imagem
            criar_video_com_legenda(arquivo_audio_temp, arquivo_legenda, arquivo_video_final, ARQUIVO_IMAGEM_FUNDO)
            
            # Limpar arquivo temporário
            arquivo_audio_temp.unlink()
            print(f"   ✅ Vídeo salvo em: {arquivo_video_final}")
            
        except Exception as e:
            print(f"   ❌ Erro ao processar {nome_musica}: {e}")
            # Limpar arquivo temporário em caso de erro
            if arquivo_audio_temp.exists():
                arquivo_audio_temp.unlink()
    
    print(f"\n🎉 Processamento concluído! Verifique a pasta 'karaokes_completos/'")
    print(f"📁 {len(pares)} vídeo(s) de karaokê criado(s)")

if __name__ == "__main__":
    main()