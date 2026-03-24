"""
processor.py
Recebe o texto bruto da transcrição e faz dois passos:
  1. Correção: remove ruídos de legendas automáticas
  2. Resumo: gera resumo estruturado
"""

from Modulos.AI_Provider import chamar_ia

# Máximo de caracteres enviados de uma vez para a IA
# Transcrições longas são divididas em partes menores
TAMANHO_CHUNK = 8000


def _dividir_em_chunks(texto: str, tamanho: int = TAMANHO_CHUNK) -> list[str]:
    """Divide o texto em partes de no máximo 'tamanho' caracteres,
    sempre cortando no fim de uma frase (ponto final)."""
    if len(texto) <= tamanho:
        return [texto]  # não precisa dividir

    partes = []
    while len(texto) > tamanho:
        # Procura o último ponto antes do limite
        corte = texto.rfind(". ", 0, tamanho)
        if corte == -1:
            corte = tamanho  # fallback: corta no limite mesmo
        partes.append(texto[:corte + 1].strip())
        texto = texto[corte + 1:].strip()

    if texto:  # adiciona o restante
        partes.append(texto)

    return partes


def corrigir_texto(transcricao: str, provedor: str) -> str:
    """
    Usa IA para corrigir erros comuns de transcrições automáticas:
    pontuação, capitalização, repetições, ruídos como [música].
    """
    print("Corrigindo texto da transcrição...")

    partes = _dividir_em_chunks(transcricao)
    partes_corrigidas = []

    for i, parte in enumerate(partes):
        if len(partes) > 1:
            print(f"   Parte {i+1}/{len(partes)}...")

        mensagens = [
            {
                "role": "system",
                "content": (
                    "Você é um editor de texto. Corrija o texto de uma "
                    "transcrição automática. Faça APENAS:\n"
                    "- Adicionar pontuação adequada\n"
                    "- Corrigir capitalização\n"
                    "- Remover repetições óbvias\n"
                    "- Remover marcações: [música], [aplausos], [inaudível]\n"
                    "NÃO resuma. NÃO adicione informações. "
                    "Retorne APENAS o texto corrigido."
                ),
            },
            {"role": "user", "content": parte},
        ]

        corrigida = chamar_ia(provedor, mensagens, max_tokens=2000)
        partes_corrigidas.append(corrigida)

    return "\n\n".join(partes_corrigidas)



def gerar_resumo(texto_corrigido: str, provedor: str, idioma: str = "English") -> str:
    """Gera resumo estruturado no idioma escolhido."""
    print(f"Gerando resumo em {idioma}...")

    partes = _dividir_em_chunks(texto_corrigido, tamanho=10000)

    if len(partes) == 1:
        return _resumir_parte(partes[0], provedor, final=True, idioma=idioma)
    resumos_parciais = []
    for i, parte in enumerate(partes):
        print(f"   Resumindo parte {i+1}/{len(partes)}...")
        resumo_parcial = _resumir_parte(parte, provedor, final=False, idioma=idioma)
        resumos_parciais.append(resumo_parcial)

    print("   Consolidando resumos...")
    texto_consolidar = "\n\n---\n\n".join(resumos_parciais)
    return _resumir_parte(texto_consolidar, provedor, final=True, idioma=idioma)


def _resumir_parte(texto: str, provedor: str, final: bool, idioma: str = "English") -> str:
    """Resume uma parte do texto no idioma escolhido."""
    if final:
        instrucao = (
            f"IMPORTANT: You must write your ENTIRE response in {idioma} only. "
            f"Do NOT use any other language. "
            f"Even if the input text is in Portuguese, Spanish, or any other language, "
            f"your response must be 100% in {idioma}.\n\n"
            f"Create a complete summary of this video using exactly this format:\n\n"
            f"## Main Topic\n"
            f"[One sentence describing the central subject]\n\n"
            f"## Key Points\n"
            f"[List of the most important topics and ideas]\n\n"
            f"## Relevant Details\n"
            f"[Specific information, examples, data mentioned]\n\n"
            f"## Conclusion\n"
            f"[Final message of the video]\n\n"
            f"Respond exclusively in {idioma}. This is mandatory."
        )
    else:
        instrucao = (
            f"IMPORTANT: Respond exclusively in {idioma}. "
            f"Do NOT use any other language regardless of the input language.\n\n"
            f"Summarize this part of a video transcript keeping all important points. "
            f"Write everything in {idioma}. This is mandatory."
        )

    mensagens = [
        {"role": "system", "content": instrucao},
        {"role": "user", "content": texto},
    ]
    return chamar_ia(provedor, mensagens, max_tokens=1500)


