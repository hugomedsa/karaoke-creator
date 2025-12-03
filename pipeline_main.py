#!/usr/bin/env python3
# pipeline_main.py - VERSÃO OTIMIZADA

"""
Orquestrador otimizado: 
download -> separar instrumental -> gerar SRT (com vocals) -> gerar ASS (com vocals) -> juntar vídeo.

NOVA ORDEM: Separa os vocals PRIMEIRO para melhorar a detecção de letra no Whisper e alinhamento no WhisperX.
"""

from pathlib import Path
import argparse
import shutil
import sys

# importa funções dos módulos existentes
from download_youtube_mp3 import download_youtube_audio
from separar_instrumental import separar_faixas
from gerar_legenda_base import transcrever_audio, gerar_srt
from gerar_legenda_dinamica import gerar_legenda_karaoke
from video_karaoke_join_all import combinar_faixas_instrumentais, criar_video_com_legenda

def main():
    parser = argparse.ArgumentParser(
        description="Pipeline otimizado: download -> separar -> legenda SRT (vocals) -> legenda ASS (vocals) -> vídeo"
    )
    parser.add_argument(
        "--etapa", 
        type=int, 
        choices=[1, 2, 3, 4, 5], 
        default=1, 
        help="Etapa inicial do pipeline (1 a 5, padrão: 1)"
    )
    parser.add_argument(
        "--nome", 
        help="Nome base do projeto (sem extensão). Se não informado, usa o mais recente na etapa correspondente."
    )
    parser.add_argument(
        "url", 
        nargs='?', 
        help="URL do vídeo YouTube (obrigatório se etapa=1)"
    )
    parser.add_argument(
        "--trim", 
        type=int, 
        default=None, 
        help="Cortar áudio para primeiros N segundos"
    )
    parser.add_argument(
        "--imagem", 
        default="karaoke-hugo.jpg", 
        help="Imagem de fundo para o vídeo final"
    )
    args = parser.parse_args()

    # Validações iniciais
    if args.etapa == 1 and not args.url:
        parser.error("A URL é obrigatória quando etapa=1.")

    try:
        # ========== FUNÇÃO PARA BUSCAR ARQUIVO MAIS RECENTE ==========
        def buscar_mais_recente(pasta, padrao):
            """Retorna o Path do arquivo mais recente que corresponde ao padrão."""
            dir_path = Path(pasta)
            if not dir_path.exists():
                return None
            arquivos = list(dir_path.glob(padrao))
            if not arquivos:
                return None
            # Retorna o arquivo com timestamp de modificação mais recente
            return max(arquivos, key=lambda x: x.stat().st_mtime)

        # ========== DETERMINAR O NOME BASE DO PROJETO ==========
        nome_base = None
        
        if args.nome:
            # Usa o nome fornecido explicitamente
            nome_base = args.nome
            print(f"  -> Usando nome base fornecido: '{nome_base}'")
        else:
            # Tenta descobrir o nome base automaticamente baseado na etapa
            if args.etapa >= 2:
                # Para etapa 2+, busca o áudio mais recente em audio/
                audio_recente = buscar_mais_recente("audio", "*.mp3")
                if audio_recente:
                    nome_base = audio_recente.stem
                    print(f"  -> Nome base detectado do áudio mais recente: '{nome_base}'")
                else:
                    raise FileNotFoundError("Nenhum arquivo .mp3 encontrado em audio/. Use --nome para especificar.")
            else:
                # Para etapa 1, o nome será gerado a partir do download
                pass

        # Garantir pastas de saída (sempre criadas quando necessário)
        subtitle_srt_dir = Path("subtitle_srt")
        subtitle_srt_dir.mkdir(exist_ok=True, parents=True)
        subtitle_ass_dir = Path("subtitle_ass")
        subtitle_ass_dir.mkdir(exist_ok=True, parents=True)
        audio_separado_base = Path("audio_separado")
        audio_separado_base.mkdir(exist_ok=True, parents=True)
        karaokes_dir = Path("karaokes_completos")
        karaokes_dir.mkdir(exist_ok=True, parents=True)

        # ========== ETAPA 1: Download do áudio ==========
        if args.etapa <= 1:
            print("1️⃣  Download do áudio...")
            if not args.url:
                raise ValueError("URL do YouTube é necessária para a etapa 1.")
            
            downloaded = download_youtube_audio(args.url, trim_seconds=args.trim)
            audio_path = Path(downloaded)
            if not audio_path.exists():
                raise FileNotFoundError(f"Arquivo baixado não encontrado: {audio_path}")
            
            nome_base = audio_path.stem  # Atualiza o nome base com o do download
            print(f"  -> Arquivo obtido: {audio_path.name}")
        else:
            # Para etapas 2+, constrói o caminho do áudio baseado no nome
            audio_dir = Path("audio")
            audio_path = audio_dir / f"{nome_base}.mp3"
            if not audio_path.exists():
                # Tenta encontrar qualquer arquivo de áudio com esse nome base
                possiveis = list(audio_dir.glob(f"{nome_base}.*"))
                if possiveis:
                    audio_path = possiveis[0]
                    print(f"  -> Usando arquivo de áudio: {audio_path.name}")
                else:
                    raise FileNotFoundError(f"Nenhum arquivo de áudio encontrado para '{nome_base}' em audio/")
            else:
                print(f"  -> Usando arquivo de áudio: {audio_path.name}")

        # ========== ETAPA 2: Separar instrumental (NOVO - ANTES da legenda) ==========
        if args.etapa <= 2:
            print("2️⃣  Separando faixas (Demucs) - extraindo vocals.wav...")
            out_separado_dir = audio_separado_base / nome_base
            separar_faixas(str(audio_path), str(out_separado_dir))
            print(f"  -> Faixas salvas em: {out_separado_dir}")
            
            # Caminho do vocals.wav para as próximas etapas
            vocals_path = out_separado_dir / "vocals.wav"
            if not vocals_path.exists():
                raise FileNotFoundError(f"Arquivo vocals.wav não encontrado em {out_separado_dir}")
            print(f"  -> Usando vocals para detecção: {vocals_path}")
        else:
            # Para etapas 3+, constrói o caminho do vocals
            out_separado_dir = audio_separado_base / nome_base
            vocals_path = out_separado_dir / "vocals.wav"
            if not vocals_path.exists():
                raise FileNotFoundError(f"Arquivo vocals.wav não encontrado em {out_separado_dir}. Execute etapa 2 primeiro.")
            print(f"  -> Usando vocals: {vocals_path}")

        # ========== ETAPA 3: Gerar legenda base (.srt) COM VOCALS ==========
        if args.etapa <= 3:
            print("3️⃣  Gerando legenda SRT (legenda base) usando VOCALS...")
            print(f"  -> Transcrevendo: {vocals_path}")
            segmentos = transcrever_audio(str(vocals_path))
            srt_out = subtitle_srt_dir / f"{nome_base}.srt"
            gerar_srt(segmentos, str(srt_out))
            print(f"  -> SRT gerado: {srt_out}")
        else:
            # Para etapas 4+, encontra o SRT correspondente
            srt_out = subtitle_srt_dir / f"{nome_base}.srt"
            if not srt_out.exists():
                # Tenta encontrar qualquer arquivo SRT com esse nome base
                possiveis = list(subtitle_srt_dir.glob(f"{nome_base}*.srt"))
                if possiveis:
                    srt_out = possiveis[0]  # Pega o primeiro que encontrar
                    print(f"  -> Usando arquivo SRT: {srt_out.name}")
                else:
                    raise FileNotFoundError(f"Nenhum arquivo .srt encontrado para '{nome_base}' em subtitle_srt/")
            else:
                print(f"  -> Usando arquivo SRT: {srt_out.name}")

        # ========== ETAPA 4: Gerar legenda dinâmica (.ass) COM VOCALS ==========
        if args.etapa <= 4:
            print("4️⃣  Gerando legenda dinâmica (.ass) karaokê usando VOCALS...")
            print(f"  -> Alinhando: {vocals_path}")
            ass_out = subtitle_ass_dir / f"{nome_base}.ass"
            gerar_legenda_karaoke(str(vocals_path), str(srt_out), str(ass_out))
            print(f"  -> ASS gerado: {ass_out}")
        else:
            # Para etapa 5, encontra o ASS
            ass_out = subtitle_ass_dir / f"{nome_base}.ass"
            if not ass_out.exists():
                possiveis = list(subtitle_ass_dir.glob(f"{nome_base}*.ass"))
                if possiveis:
                    ass_out = possiveis[0]
                    print(f"  -> Usando arquivo ASS: {ass_out.name}")
                else:
                    raise FileNotFoundError(f"Nenhum arquivo .ass encontrado para '{nome_base}' em subtitle_ass/")
            else:
                print(f"  -> Usando arquivo ASS: {ass_out.name}")

        # ========== ETAPA 5: Juntar vídeo ==========
        if args.etapa <= 5:
            print("5️⃣  Combinando instrumentais e criando vídeo final...")
            
            arquivo_audio_temp = karaokes_dir / f"{nome_base}_instrumental.mp3"
            combinar_faixas_instrumentais(out_separado_dir, arquivo_audio_temp)

            arquivo_video_final = karaokes_dir / f"{nome_base}_karaoke.mp4"

            imagem_fundo = Path(args.imagem)
            if not imagem_fundo.exists():
                raise FileNotFoundError(f"Imagem de fundo não encontrada: {imagem_fundo}")

            criar_video_com_legenda(arquivo_audio_temp, ass_out, arquivo_video_final, imagem_fundo)

            # remover temporário
            if arquivo_audio_temp.exists():
                arquivo_audio_temp.unlink()
            print(f"  -> Vídeo final: {arquivo_video_final}")

        print("\n✅ Pipeline concluído com sucesso!")
        print(f"📁 Vídeo: {karaokes_dir / f'{nome_base}_karaoke.mp4'}")

    except Exception as e:
        print(f"\n❌ Erro durante o pipeline: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()