import os
import re
import tempfile
from dotenv import load_dotenv
import time

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




def _buscar_legenda(video_id: str) -> tuple[str | None, str]:
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        from youtube_transcript_api.proxies import WebshareProxyConfig
        import os

        proxy_user = os.getenv("PROXY_USERNAME")
        proxy_pass = os.getenv("PROXY_PASSWORD")

        if proxy_user and proxy_pass:
            print("Usando proxy...")
            api = YouTubeTranscriptApi(
                proxy_config=WebshareProxyConfig(
                    proxy_username=proxy_user,
                    proxy_password=proxy_pass,
                    proxy_host="p.webshare.io",
                    proxy_port=80,
                )
            )
        else:
            print("Sem proxy...")
            api = YouTubeTranscriptApi()

        lista = api.list(video_id)

        idiomas_pref = os.getenv("TRANSCRIPT_LANGUAGES", "pt,en").split(",")
        idiomas_pref = [i.strip() for i in idiomas_pref]

        transcript = None

        for idioma in idiomas_pref:
            try:
                t = lista.find_transcript([idioma])
                if not t.is_generated:
                    transcript = t
                    break
            except:
                continue

        if transcript is None:
            for idioma in idiomas_pref:
                try:
                    transcript = lista.find_transcript([idioma])
                    break
                except:
                    continue

        if transcript is None:
            try:
                transcript = next(iter(lista))
            except StopIteration:
                return None, "No captions available"

        dados = transcript.fetch()
        texto = " ".join(item.text for item in dados)

        return texto, ""

    except Exception as e:
        return None, str(e)







# def _buscar_legenda(video_id: str) -> tuple[str | None, str]:
#     """
#     Retorna (texto, "") se achou legenda.
#     Retorna (None, motivo_do_erro) se não achou.
#     """
#     try:
#         from youtube_transcript_api import YouTubeTranscriptApi

#         api = YouTubeTranscriptApi()
#         lista = api.list(video_id)

#         todos = [(t.language_code, t.is_generated) for t in lista]
#         print(f"   Legendas disponíveis: {todos}")

#         idiomas_pref = os.getenv("TRANSCRIPT_LANGUAGES", "pt,en").split(",")
#         idiomas_pref = [i.strip() for i in idiomas_pref]

#         transcript = None

#         # 1. tenta legenda manual nos idiomas preferidos
#         for idioma in idiomas_pref:
#             try:
#                 t = lista.find_transcript([idioma])
#                 if not t.is_generated:
#                     transcript = t
#                     print(f"   Usando legenda manual: {idioma}")
#                     break
#             except Exception:
#                 continue

#         # 2. tenta legenda automática nos idiomas preferidos
#         if transcript is None:
#             for idioma in idiomas_pref:
#                 try:
#                     transcript = lista.find_transcript([idioma])
#                     print(f"   Usando legenda automática: {idioma}")
#                     break
#                 except Exception:
#                     continue

#         # 3. qualquer legenda disponível como último recurso
#         if transcript is None:
#             try:
#                 transcript = next(iter(lista))
#                 print(f"   Usando: {transcript.language_code}")
#             except StopIteration:
#                 return None, "No captions available for this video"

#         dados = transcript.fetch()
#         texto = " ".join(item.text for item in dados)
#         print(f"Legenda encontrada ({len(texto)} caracteres).")
#         return texto, ""

#     except Exception as e:
#         # agora o erro aparece na tela em vez de sumir
#         return None, str(e)
    


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

            "extractor_args": {
                "youtube": {
                    "player_client": ["android"]
                }
            },

                # Simula um navegador comum para evitar o bloqueio
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    },
        }


        for tentativa in range(3):
            try:
                print(f"Tentando baixar áudio... (tentativa {tentativa+1})")

                with yt_dlp.YoutubeDL(opcoes_ydl) as ydl:
                    ydl.download([url])

                print("Download concluído!")
                break

            except Exception as e:
                print(f"Tentativa {tentativa+1} falhou: {e}")
                time.sleep(2)

        else:
            raise RuntimeError("Falha ao baixar áudio após várias tentativas")




        # Encontra o arquivo gerado
        caminho_audio = None
        for arquivo in os.listdir(pasta_temp):
            if arquivo.startswith("audio"):
                caminho_audio = os.path.join(pasta_temp, arquivo)
                break

        if not caminho_audio:
            raise RuntimeError("Arquivo de áudio não encontrado após download")

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

    texto_final = str(resultado)
    print(f"Transcrição por áudio concluída ({len(texto_final)} chars).")
    return texto_final



def obter_transcricao(url: str, provedor: str) -> tuple[str, str]:
    """
    Ponto de entrada principal.
    Retorna (texto_transcrito, metodo_usado).
    metodo_usado: 'legenda' ou 'audio'
    """
    video_id = _extrair_video_id(url)
    print(f"ID do vídeo: {video_id}")

    print("Buscando legenda...")
    legenda, erro_legenda = _buscar_legenda(video_id)

    if legenda:
        return legenda, "legenda"

    print("Legenda falhou, tentando áudio...")
    texto_audio = _transcrever_audio(url, provedor)

    return texto_audio, "audio"

    # # Se não achou legenda, lança erro claro — sem tentar áudio no cloud
    # raise RuntimeError(
    #     f"No captions found for this video. "
    #     f"Caption error: {erro_legenda}"
    # )