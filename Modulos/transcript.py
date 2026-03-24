import os
import re
import tempfile
from dotenv import load_dotenv


"""
transcript.py
Obtém transcrição do vídeo:
  1. Tenta legenda do YouTube (rápido, sem custo)
  2. Se não houver, baixa áudio e transcreve com Whisper
"""

load_dotenv()

def _extrair_video_id(url: str) -> str:
    """Extrai o ID do vídeo de diferentes formatos de URL."""
    padroes = [
        r"v=([A-Za-z0-9_-]{11})",       # youtube.com/watch?v=XXXXXXXXXXX
        r"youtu\.be/([A-Za-z0-9_-]{11})",  # youtu.be/XXXXXXXXXXX
        r"embed/([A-Za-z0-9_-]{11})",    # youtube.com/embed/XXXXXXXXXXX
        r"shorts/([A-Za-z0-9_-]{11})",   # youtube.com/shorts/XXXXXXXXXXX
    ]
    for p in padroes:
        m = re.search(p, url)
        if m:
            return m.group(1)  # retorna só o ID, sem o resto
    raise ValueError(f"Não foi possível extrair o ID da URL: {url}")




def _buscar_legenda(video_id: str) -> str | None:
    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        api = YouTubeTranscriptApi()
        lista = api.list(video_id)

        # coleta todos os códigos de idioma disponíveis
        todos = [(t.language_code, t.is_generated) for t in lista]
        print(f"   Legendas disponíveis: {todos}")

        idiomas_pref = os.getenv("TRANSCRIPT_LANGUAGES", "pt,en").split(",")
        idiomas_pref = [i.strip() for i in idiomas_pref]

        transcript = None

        # 1. tenta legenda manual nos idiomas preferidos
        for idioma in idiomas_pref:
            try:
                transcript = lista.find_transcript([idioma])
                if not transcript.is_generated:
                    print(f"   Usando legenda manual: {idioma}")
                    break
                transcript = None  # era gerada, continua procurando manual
            except Exception:
                continue

        # 2. tenta legenda gerada automaticamente nos idiomas preferidos
        if transcript is None:
            for idioma in idiomas_pref:
                try:
                    transcript = lista.find_transcript([idioma])
                    print(f"   Usando legenda automática: {idioma}")
                    break
                except Exception:
                    continue

        # 3. pega qualquer legenda disponível como último recurso
        if transcript is None:
            try:
                transcript = next(iter(lista))
                print(f"   Usando primeira legenda disponível: {transcript.language_code}")
            except StopIteration:
                return None

        dados = transcript.fetch()
        texto = " ".join(item.text for item in dados)
        print(f"✅ Legenda encontrada ({len(texto)} caracteres).")
        return texto

    except Exception as e:
        print(f"Erro ao buscar legenda: {e}")
        return None
    


def _transcrever_audio(url: str, provedor: str) -> str:
    """
    Baixa áudio com yt-dlp e transcreve com Whisper.
    Funciona com Groq (grátis) ou OpenAI.
    Claude não tem Whisper — avisa o usuário.
    """
    if provedor == "claude":
        raise RuntimeError(
            "Transcrição de áudio não está disponível com Claude.\n"
            "Este vídeo não tem legenda.\n"
            "Solução: adicione GROQ_API_KEY no .env (é grátis em console.groq.com)"
        )

    import yt_dlp

    print("Baixando áudio do vídeo (pode demorar)...")

    with tempfile.TemporaryDirectory() as pasta_temp:
        opcoes_ydl = {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(pasta_temp, "audio.%(ext)s"),
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "32",
            }],
            "quiet": True,
                # Simula um navegador comum para evitar o bloqueio
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    },
        }

        with yt_dlp.YoutubeDL(opcoes_ydl) as ydl:
            ydl.download([url])

        # Encontra o arquivo gerado
        caminho_audio = None
        for arquivo in os.listdir(pasta_temp):
            if arquivo.startswith("audio"):
                caminho_audio = os.path.join(pasta_temp, arquivo)
                break

        tamanho = os.path.getsize(caminho_audio) / (1024 * 1024)
        print(f"Áudio baixado ({tamanho:.1f} MB). Transcrevendo com Whisper...")

        # ── Groq ──────────────────────────────────────────────
        if provedor == "groq":
            from groq import Groq
            cliente = Groq(api_key=os.getenv("GROQ_API_KEY"))
            with open(caminho_audio, "rb") as f:
                resultado = cliente.audio.transcriptions.create(
                    model="whisper-large-v3-turbo",  # modelo mais rápido do Groq
                    file=f,
                    response_format="text",
                )

        # ── OpenAI ────────────────────────────────────────────
        elif provedor == "openai":
            from openai import OpenAI
            cliente = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            with open(caminho_audio, "rb") as f:
                resultado = cliente.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
                    response_format="text",
                )

    print(f"Transcrição por áudio concluída ({len(resultado)} chars).")
    return resultado



def obter_transcricao(url: str, provedor: str) -> tuple[str, str]:
    """
    Ponto de entrada principal.
    Retorna (texto_transcrito, metodo_usado).
    metodo_usado: 'legenda' ou 'audio'
    """
    video_id = _extrair_video_id(url)
    print(f"ID do vídeo: {video_id}")

    print("Buscando legenda...")
    legenda = _buscar_legenda(video_id)

    if legenda:
        return legenda, "legenda"

    print("Sem legenda. Tentando via áudio...")
    audio_texto = _transcrever_audio(url, provedor)
    return audio_texto, "audio"