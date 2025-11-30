"""
gerar_legenda_dinamica.py

Gera um arquivo de legenda de karaokê (.ass) com destaque palavra por palavra.

Requisitos:
- whisperX (e suas dependências, incluindo torch)
- ffmpeg instalado e no PATH do sistema

Este script utiliza o whisperX para alinhar o áudio de uma música com uma legenda
existente (no formato .srt), gerando timestamps precisos para cada palavra.
Em seguida, cria um arquivo .ass com efeitos de estilo para simular um karaokê,
onde cada palavra é destacada à medida que é cantada.
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
    # Estilos para a legenda
    # - Fonte, tamanho, cores, sombra, etc.
    # - A cor primária será a cor de preenchimento do karaokê.
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

            for i, word_info in enumerate(segment['words']):
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
    Gera uma legenda de karaokê no formato .ass.

    Args:
        audio_path (str): Caminho para o arquivo de áudio (ex: .mp3).
        srt_path (str): Caminho para o arquivo de legenda corrigida (ex: .srt).
        output_path (str): Caminho para salvar o arquivo .ass de saída.
    """
    print("Carregando modelo de alinhamento do whisperX...")
    align_model, metadata = whisperx.load_align_model(
        language_code="pt",
        device="cuda")

    print("Carregando e preparando os segmentos da legenda SRT...")
    segmentos_srt = srt_para_segmentos(srt_path)

    print("Alinhando a legenda com o áudio... (Isso pode levar um tempo)")
    result = whisperx.align(
        segmentos_srt,
        align_model,
        metadata,
        audio_path,
        "cuda",
        return_char_alignments=False
    )

    print("Gerando arquivo de legenda .ass com efeito de karaokê...")
    gerar_arquivo_ass(result, output_path)

    print(f"\nLegenda de karaokê gerada com sucesso em: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gera legenda de karaokê (.ass) a partir de áudio e legenda .srt.")
    parser.add_argument("--audio", required=False, help="Caminho do arquivo de áudio (padrão: pasta audio_base/).")
    parser.add_argument("--srt", required=False, help="Caminho do arquivo .srt corrigido (padrão: pasta subtitle_srt/).")
    parser.add_argument("--out", default=None, help="Arquivo/pasta de saída .ass (padrão: pasta subtitle_ass/).")
    args = parser.parse_args()

    # Verificar pasta audio_base
    if not args.audio:
        base_dir = Path("audio_base")
        if not base_dir.exists():
            raise FileNotFoundError("Pasta audio_base/ não encontrada.")
        mp3s = list(base_dir.glob("*.mp3"))
        if not mp3s:
            raise FileNotFoundError("Nenhum arquivo .mp3 encontrado na pasta audio_base/")
        args.audio = str(mp3s[0])
        print(f"Usando arquivo de áudio: {args.audio}")

    # Verificar arquivo SRT
    if not args.srt:
        srt_dir = Path("subtitle_srt")
        if not srt_dir.exists():
            raise FileNotFoundError("Pasta subtitle_srt/ não encontrada.")
        
        audio_stem = Path(args.audio).stem
        srt_file = srt_dir / f"{audio_stem}.srt"
        if not srt_file.exists():
            raise FileNotFoundError(f"Arquivo {srt_file} não encontrado.")
        args.srt = str(srt_file)

    # Criar pasta de saída apenas se não existir
    out_dir = Path("subtitle_ass")
    if not out_dir.exists():
        out_dir.mkdir(parents=True, exist_ok=True)
        print(f"Pasta de saída criada: {out_dir}")

    # Definir caminho de saída
    if not args.out:
        audio_stem = Path(args.audio).stem
        args.out = str(out_dir / f"{audio_stem}.ass")

    print(f"Processando: {args.audio} -> {args.srt} -> {args.out}")
    gerar_legenda_karaoke(args.audio, args.srt, args.out)