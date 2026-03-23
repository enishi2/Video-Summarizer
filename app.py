"""
app.py
------
Interface web com Streamlit.
Substitui o terminal — roda no navegador, local ou em servidor.
"""

import os
import streamlit as st

# ── Configuração da página ─────────────────────────────────────────────────
st.set_page_config(
    page_title="YouTube Summarizer",
    page_icon="▶",
    layout="centered",
)

# ── Lê chaves: Streamlit Secrets (deploy) ou .env (local) ─────────────────
def _carregar_chaves():
    """
    Em produção (Streamlit Cloud) as chaves vêm de st.secrets.
    Em desenvolvimento local as chaves vêm do .env via modules.
    """
    try:
        # Streamlit Cloud — chaves configuradas no painel
        for chave in ["GROQ_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"]:
            valor = st.secrets.get(chave, "")
            if valor:
                os.environ[chave] = valor
    except Exception:
        # Local — o load_dotenv() dentro dos módulos já cuida disso
        pass

_carregar_chaves()

from Modulos.AI_Provider import detectar_provedor, chamar_ia
from Modulos.transcript import obter_transcricao
from Modulos.processor import corrigir_texto, gerar_resumo

# ── Inicializa session_state ────────────────────────────────────────────────
# session_state é a memória da página — persiste enquanto o usuário está na aba
if "provedor" not in st.session_state:
    st.session_state.provedor = None
if "resumo" not in st.session_state:
    st.session_state.resumo = None
if "transcricao" not in st.session_state:
    st.session_state.transcricao = None
if "historico_chat" not in st.session_state:
    st.session_state.historico_chat = []
if "url_processada" not in st.session_state:
    st.session_state.url_processada = None

# ── Detecta provedor uma vez por sessão ────────────────────────────────────
if st.session_state.provedor is None:
    try:
        st.session_state.provedor = detectar_provedor()
    except RuntimeError as e:
        st.error(str(e))
        st.stop()

# ── Header ─────────────────────────────────────────────────────────────────
st.title("YouTube Video Summarizer")
st.caption(f"AI provider: **{st.session_state.provedor.upper()}**")
st.divider()

# ── Seção 1: URL + botão ───────────────────────────────────────────────────
url = st.text_input(
    "YouTube URL",
    placeholder="https://www.youtube.com/watch?v=...",
    label_visibility="collapsed",
)

botao = st.button("Summarize", type="primary", use_container_width=True)

# ── Processamento ──────────────────────────────────────────────────────────
if botao and url:
    # Se a URL mudou, limpa o estado anterior
    if url != st.session_state.url_processada:
        st.session_state.resumo = None
        st.session_state.transcricao = None
        st.session_state.historico_chat = []
        st.session_state.url_processada = url

    provedor = st.session_state.provedor

    with st.status("Processing video...", expanded=True) as status:
        try:
            st.write("Fetching transcript...")
            transcricao_bruta, metodo = obter_transcricao(url, provedor)
            metodo_label = "YouTube captions" if metodo == "legenda" else "audio transcription"
            st.write(f"Transcript obtained via {metodo_label}.")

            st.write("Correcting text...")
            transcricao_corrigida = corrigir_texto(transcricao_bruta, provedor)

            st.write("Generating summary...")
            resumo = gerar_resumo(transcricao_corrigida, provedor)

            st.session_state.transcricao = transcricao_corrigida
            st.session_state.resumo = resumo

            status.update(label="Done!", state="complete", expanded=False)

        except Exception as e:
            status.update(label="Error", state="error")
            st.error(f"{e}")
            st.stop()

elif botao and not url:
    st.warning("Paste a YouTube URL first.")

# ── Seção 2: Resumo ────────────────────────────────────────────────────────
if st.session_state.resumo:
    st.divider()
    st.subheader("Summary")
    st.markdown(st.session_state.resumo)

    with st.expander("View full transcript"):
        st.text(st.session_state.transcricao)

# ── Seção 3: Chatbot ───────────────────────────────────────────────────────
if st.session_state.resumo:
    st.divider()
    st.subheader("Ask about this video")

    SYSTEM_PROMPT = """You are an assistant that answers questions about a specific video.

RULES:
1. Answer ONLY based on the video content below.
2. If the information is not in the video, say: "That was not mentioned in the video."
3. Never invent information.
4. Be clear and concise.

VIDEO CONTENT:
{conteudo}"""

    conteudo = (
        f"=== SUMMARY ===\n{st.session_state.resumo}\n\n"
        f"=== FULL TRANSCRIPT ===\n{st.session_state.transcricao}"
    )
    system = SYSTEM_PROMPT.format(conteudo=conteudo[:15000])

    # Exibe histórico de mensagens
    for msg in st.session_state.historico_chat:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Campo de pergunta
    pergunta = st.chat_input("Ask anything about the video...")

    if pergunta:
        # Mostra a pergunta imediatamente
        with st.chat_message("user"):
            st.write(pergunta)
        st.session_state.historico_chat.append({"role": "user", "content": pergunta})

        # Gera resposta
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                mensagens = [{"role": "system", "content": system}]
                mensagens += st.session_state.historico_chat

                try:
                    resposta = chamar_ia(
                        st.session_state.provedor,
                        mensagens,
                        max_tokens=800,
                    )
                    st.write(resposta)
                    st.session_state.historico_chat.append({
                        "role": "assistant",
                        "content": resposta,
                    })

                    # Limita histórico a 20 mensagens
                    if len(st.session_state.historico_chat) > 20:
                        st.session_state.historico_chat = st.session_state.historico_chat[-20:]

                except Exception as e:
                    st.error(f"Error: {e}")
                    st.session_state.historico_chat.pop()
