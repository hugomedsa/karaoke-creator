"""
gerar_legenda_dinamica.py - VERSÃO OTIMIZADA

Gera um arquivo de legenda de karaokê (.ass) com destaque palavra por palavra.

OTIMIZAÇÃO: Como o SRT já foi gerado com Whisper usando apenas vocals,
este script PULA a transcrição e vai direto para o alinhamento palavra-por-palavra.

Requisitos:
- whisperX (e suas dependências, incluindo torch)
- ffmpeg instalado e no PATH do sistema
"""

import whisperx
import argparse
from pathlib import Path
import srt


def srt_para_segmentos(srt_path):
    """Lê um arquivo .srt e o converte para o formato de segmento do whisperX."""
    with open(srt_path, 'r', encoding='utf-8') as f:
        subs = list(srt.parse(f.read()))
    
    segmentos = []
    for sub in subs:
        segmentos.append({
            'text': sub.content.strip(),
            'start': sub.start.total_seconds(),
            'end': sub.end.total_seconds(),
        })
    return segmentos


def format_time(seconds):
    """Converte segundos para o formato de tempo do .ass (H:MM:SS.ss)."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds - int(seconds)) * 100)
    return f"{h:01}:{m:02}:{s:02}.{cs:02}"


def gerar_arquivo_ass(result, output_path):
    """
    Gera um arquivo .ass com efeito de karaokê a partir do resultado do alinhamento.
    """
    header = """[Script Info]
Title: Legenda de Karaokê
ScriptType: v4.00+
WrapStyle: 0
PlayResX: 1280
PlayResY: 720

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,48,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,1,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(header)

        for segment in result['segments']:
            start_time = format_time(segment['start'])
            end_time = format_time(segment['end'])
            
            line_text = []
            if 'words' not in segment or not segment['words']:
                continue

            for word_info in segment['words']:
                # Duração do destaque da palavra em centissegundos
                k_duration = int((word_info['end'] - word_info['start']) * 100)
                
                # Adiciona a tag de tempo do karaokê e a palavra
                line_text.append("{\\k" + str(k_duration) + "}" + word_info['word'])
            
            # Junta as palavras com um espaço
            full_line = " ".join(line_text).strip()
            
            # Escreve a linha de diálogo no arquivo .ass
            dialogue_line = f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{full_line}\n"
            f.write(dialogue_line)


def gerar_legenda_karaoke(audio_path, srt_path, output_path):
    """
    Gera legenda de karaokê usando alinhamento palavra-por-palavra.
    
    OTIMIZADO: Pula a transcrição (já feita com Whisper no SRT)
    e vai direto para o alinhamento com WhisperX.
    
    Args:
        audio_path (str): Caminho do áudio (vocals.wav)
        srt_path (str): Caminho do arquivo .srt gerado anteriormente
        output_path (str): Caminho de saída do arquivo .ass
    """
    print("📖 Carregando segmentos do SRT...")
    segmentos_srt = srt_para_segmentos(srt_path)
    print(f"   ✓ {len(segmentos_srt)} segmentos carregados")
    
    print("🎧 Carregando áudio (vocals)...")
    audio = whisperx.load_audio(audio_path)
    print(f"   ✓ Áudio carregado")
    
    print("🔗 Carregando modelo de alinhamento...")
    # Detectar idioma automaticamente (será PT para português)
    align_model, metadata = whisperx.load_align_model(
        language_code="pt",  # Forçar português para melhor precisão
        device="cuda"
    )
    print(f"   ✓ Modelo carregado (idioma: {metadata['language']})")
    
    print("⏱️  Alinhando palavras com o áudio...")
    result = whisperx.align(
        segmentos_srt,           # Segmentos do SRT (já transcritos)
        align_model,
        metadata,
        audio,
        device="cuda",
        return_char_alignments=False
    )
    print(f"   ✓ Alinhamento concluído")
    
    print("✍️  Gerando arquivo .ass...")
    gerar_arquivo_ass(result, output_path)
    print(f"✅ Legenda gerada com sucesso: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Gera legenda de karaokê (.ass) alinhando áudio com SRT existente."
    )
    parser.add_argument(
        "--audio", 
        required=False, 
        help="Caminho do arquivo de áudio vocals.wav (padrão: detecta automaticamente)"
    )
    parser.add_argument(
        "--srt", 
        required=False, 
        help="Caminho do arquivo .srt (padrão: detecta automaticamente)"
    )
    parser.add_argument(
        "--out", 
        default=None, 
        help="Arquivo de saída .ass (padrão: subtitle_ass/[nome].ass)"
    )
    parser.add_argument(
        "--nome",
        required=False,
        help="Nome base da música (para auto-detectar arquivos)"
    )
    args = parser.parse_args()

    # ===== AUTO-DETECÇÃO DE ARQUIVOS =====
    nome_base = args.nome
    
    # Detectar áudio (vocals.wav)
    if not args.audio:
        if nome_base:
            # Procurar em audio_separado/[nome]/vocals.wav
            vocals_path = Path("audio_separado") / nome_base / "vocals.wav"
            if vocals_path.exists():
                args.audio = str(vocals_path)
            else:
                raise FileNotFoundError(f"Arquivo não encontrado: {vocals_path}")
        else:
            # Procurar o primeiro vocals.wav em audio_separado/
            audio_separado_dir = Path("audio_separado")
            if not audio_separado_dir.exists():
                raise FileNotFoundError("Pasta audio_separado/ não encontrada.")
            
            vocals_files = list(audio_separado_dir.glob("*/vocals.wav"))
            if not vocals_files:
                raise FileNotFoundError("Nenhum arquivo vocals.wav encontrado em audio_separado/")
            
            args.audio = str(vocals_files[0])
            nome_base = vocals_files[0].parent.name
            print(f"🎵 Detectado: {nome_base}")

    # Detectar SRT
    if not args.srt:
        if not nome_base:
            nome_base = Path(args.audio).parent.name
        
        srt_path = Path("subtitle_srt") / f"{nome_base}.srt"
        if not srt_path.exists():
            # Tentar outras variações
            srt_dir = Path("subtitle_srt")
            possiveis = list(srt_dir.glob(f"{nome_base}*.srt"))
            if possiveis:
                args.srt = str(possiveis[0])
            else:
                raise FileNotFoundError(f"Arquivo .srt não encontrado para '{nome_base}'")
        else:
            args.srt = str(srt_path)

    # Definir saída
    if not args.out:
        if not nome_base:
            nome_base = Path(args.audio).parent.name
        
        out_dir = Path("subtitle_ass")
        out_dir.mkdir(exist_ok=True, parents=True)
        args.out = str(out_dir / f"{nome_base}.ass")

    print(f"\n{'='*60}")
    print(f"📋 GERANDO LEGENDA DE KARAOKÊ (ASS)")
    print(f"{'='*60}")
    print(f"🎧 Áudio: {args.audio}")
    print(f"📖 SRT:   {args.srt}")
    print(f"💾 Saída: {args.out}")
    print(f"{'='*60}\n")
    
    gerar_legenda_karaoke(args.audio, args.srt, args.out)