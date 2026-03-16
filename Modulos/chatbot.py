from Modulos.AI_Provider import chamar_ia

"""
chatbot.py
Chatbot interativo que responde perguntas sobre o vídeo.
Usa apenas o conteúdo do vídeo — não inventa informações.
"""


SYSTEM_PROMPT = """Você é um assistente especializado em responder \
perguntas sobre um vídeo específico.

REGRAS IMPORTANTES:
1. Responda APENAS com base no conteúdo do vídeo fornecido abaixo.
2. Se a informação não estiver no vídeo, diga claramente:
   "Essa informação não foi mencionada no vídeo."
3. Nunca invente ou suponha informações.
4. Seja claro, objetivo e amigável.
5. Se a pergunta for vaga, peça esclarecimento.

CONTEÚDO DO VÍDEO:
{conteudo}
"""


def iniciar_chatbot(transcricao_corrigida: str, resumo: str, provedor: str):
    """
    Loop interativo do chatbot.
    Usa transcrição + resumo como contexto para a IA.
    """
    # Combina resumo + transcrição para contexto completo
    conteudo_video = (
        f"=== RESUMO ===\n{resumo}\n\n"
        f"=== TRANSCRIÇÃO COMPLETA ===\n{transcricao_corrigida}"
    )

    # Injeta o conteúdo no system prompt
    system = SYSTEM_PROMPT.format(conteudo=conteudo_video[:15000])

    historico = []  # memória da conversa

    print("\n" + "="*60)
    print("CHATBOT — Pergunte sobre o vídeo")
    print("="*60)
    print("Digite sua pergunta e pressione Enter.")
    print("Para sair: sair, exit ou quit\n")

    while True:
        try:
            pergunta = input("Você: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nChatbot encerrado.")
            break

        if not pergunta:
            continue

        if pergunta.lower() in {"sair", "exit", "quit", "q"}:
            print("Até mais!")
            break

        # Adiciona pergunta ao histórico
        historico.append({"role": "user", "content": pergunta})

        # Monta: system + todo o histórico
        mensagens = [{"role": "system", "content": system}] + historico

        try:
            resposta = chamar_ia(provedor, mensagens, max_tokens=800)
        except Exception as e:
            print(f"Erro: {e}")
            historico.pop()  # remove pergunta sem resposta
            continue

        historico.append({"role": "assistant", "content": resposta})
        print(f"\nBot: {resposta}\n")

        # Limita histórico para não estourar contexto
        if len(historico) > 20:
            historico = historico[-20:]