# 🎤 Criador de Karaokê Automático

Este projeto automatiza a criação de vídeos de karaokê a partir de vídeos do YouTube. Ele baixa o vídeo, separa a música em faixas instrumentais e vocais, gera legendas dinâmicas (estilo karaokê) e, finalmente, combina tudo em um vídeo MP4 com o instrumental e as legendas sincronizadas.

## ✨ Funcionalidades

- **Download de Vídeo**: Baixa o áudio e vídeo de um link do YouTube.
- **Separação de Áudio**: Utiliza Demucs para separar o áudio em vocais, baixo, bateria e outros instrumentos. Requer uma GPU NVIDIA para melhor desempenho.
- **Transcrição e Legendas**: Gera um arquivo de legenda base (`.srt`) a partir do áudio.
- **Legendas Dinâmicas**: Converte a legenda base em uma legenda de karaokê (`.ass`) com efeito de preenchimento de cor.
- **Criação de Vídeo Final**: Junta o vídeo original (sem som), o áudio instrumental e as legendas dinâmicas em um único arquivo de vídeo `.mp4`.

## ⚙️ Pré-requisitos

Antes de começar, garanta que você tenha os seguintes softwares instalados:

1.  **Python 3.8+**: [python.org](https://www.python.org/)
2.  **FFmpeg**: Essencial para manipulação de áudio e vídeo.
    - **Windows**: Baixe em [ffmpeg.org](https://ffmpeg.org/download.html) e adicione o caminho da pasta `bin` às variáveis de ambiente do sistema (PATH).
3.  **GPU NVIDIA (Recomendado)**: Para a separação de áudio com `demucs`, uma GPU com CUDA é fortemente recomendada para um processamento rápido.

## 🚀 Instalação Rápida

A ordem de instalação é **crucial** para o funcionamento correto do suporte a GPU (CUDA). Siga estes passos **exatamente**.

1.  **Clone o repositório e crie o ambiente virtual:**
    ```bash
    git clone https://github.com/hugofabricio/karaoke-creator.git
    cd karaoke-creator
    python -m venv venv
    venv\Scripts\activate
    ```

2.  **Instale as dependências na ordem correta:**

    **A. PyTorch com CUDA:**
    ```bash
    # Instale o PyTorch primeiro para garantir o suporte a GPU.
    pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
    ```

    **B. WhisperX e OpenAI-Whisper (sem dependências):**
    ```bash
    # Instale o WhisperX e o OpenAI-Whisper com --no-deps para não sobrescrever o PyTorch.
    pip install --no-deps git+https://github.com/m-bain/whisperX.git
    pip install --no-deps openai-whisper
    ```

    **C. Restante das bibliotecas:**
    ```bash
    # Agora, instale todo o resto.
    pip install -r requirements.txt
    ```

##  workflow Passo a Passo

Siga os passos abaixo na ordem correta para criar seu vídeo de karaokê.

### Passo 1: Baixar o Vídeo do YouTube

Use o script `download_youtube_mp3.py` para baixar o vídeo e o áudio. O vídeo será salvo em `video_oficial/`.

**Como usar:**
```bash
python download_youtube_mp3.py --url "URL_DO_VIDEO_NO_YOUTUBE"
```
*Exemplo:*
```bash
python download_youtube_mp3.py --url "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

### Passo 2: Separar as Faixas de Áudio

Execute `separar_instrumental.py` para separar o áudio do vídeo baixado. As faixas (`vocals.wav`, `bass.wav`, `drums.wav`, `other.wav`) serão salvas em uma subpasta dentro de `audio_separado/`.

**Como usar:**
O script processa automaticamente todos os vídeos da pasta `video_oficial/` que ainda não foram separados.
```bash
python separar_instrumental.py
```
> ⚠️ **Atenção**: Este processo é intensivo e pode demorar. O uso de uma GPU NVIDIA é altamente recomendado.

### Passo 3: Gerar a Legenda Base (.srt)

Use `gerar_legenda_base.py` para transcrever o áudio dos vocais e criar uma legenda `.srt`.

**Como usar:**
O script encontra automaticamente as faixas de vocais na pasta `audio_separado/` e gera a legenda correspondente em `subtitle_srt/`.
```bash
python gerar_legenda_base.py
```

### Passo 4: Gerar a Legenda Dinâmica de Karaokê (.ass)

Transforme a legenda `.srt` em uma legenda `.ass` com efeito de karaokê usando `gerar_legenda_dinamica.py`.

**Como usar:**
Ele processa os arquivos `.srt` da pasta `subtitle_srt/` e salva os arquivos `.ass` em `subtitle_ass/`.
```bash
python gerar_legenda_dinamica.py
```

### Passo 5: Criar o Vídeo de Karaokê Final

Finalmente, junte tudo com `gerar_video_karaoke.py`. Este script combina o vídeo original, o áudio instrumental (sem os vocais) e a legenda dinâmica.

**Como usar:**
O script localiza automaticamente os arquivos necessários nas pastas e cria o vídeo final em `karaokes_completos/`.
```bash
python gerar_video_karaoke.py
```

Após executar todos os passos, seu vídeo de karaokê estará pronto na pasta `karaokes_completos/`!

## 📜 Scripts do Projeto

- **`download_youtube_mp3.py`**: Baixa vídeo do YouTube.
- **`separar_instrumental.py`**: Separa o áudio em faixas instrumentais e vocais.
- **`gerar_legenda_base.py`**: Cria legendas `.srt` a partir dos vocais.
- **`gerar_legenda_dinamica.py`**: Converte `.srt` para `.ass` com estilo de karaokê.
- **`gerar_video_karaoke.py`**: Monta o vídeo de karaokê final.
- **`requirements.txt`**: Lista de dependências do Python.

