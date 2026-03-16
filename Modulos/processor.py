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



def gerar_resumo(texto_corrigido: str, provedor: str) -> str:
    """Gera resumo estruturado. Para textos longos, divide e consolida."""
    print("Gerando resumo...")

    partes = _dividir_em_chunks(texto_corrigido, tamanho=10000)

    if len(partes) == 1:
        return _resumir_parte(partes[0], provedor, final=True)

    # Textos longos: resume cada parte, depois consolida
    resumos_parciais = []
    for i, parte in enumerate(partes):
        print(f"   Resumindo parte {i+1}/{len(partes)}...")
        resumo_parcial = _resumir_parte(parte, provedor, final=False)
        resumos_parciais.append(resumo_parcial)

    print("   Consolidando resumos...")
    texto_consolidar = "\n\n---\n\n".join(resumos_parciais)
    return _resumir_parte(texto_consolidar, provedor, final=True)




def _resumir_parte(texto: str, provedor: str, final: bool) -> str:
    """Resume uma parte do texto. Se final=True, usa formato estruturado."""
    if final:
        instrucao = (
            "Crie um resumo completo e bem estruturado deste vídeo.\n\n"
            "Use exatamente este formato:\n\n"
            "## Tema Principal\n"
            "[Uma frase descrevendo o assunto central]\n\n"
            "## Pontos Principais\n"
            "[Lista dos tópicos e ideias mais importantes]\n\n"
            "## Detalhes Relevantes\n"
            "[Informações específicas, exemplos, dados mencionados]\n\n"
            "## Conclusão\n"
            "[Mensagem final do vídeo]\n\n"
            "Seja detalhado e fiel ao conteúdo original."
        )
    else:
        instrucao = (
            "Faça um resumo detalhado desta parte de uma transcrição. "
            "Mantenha todos os pontos importantes. "
            "Este resumo será usado para criar um resumo final."
        )

    mensagens = [
        {"role": "system", "content": instrucao},
        {"role": "user", "content": texto},
    ]
    return chamar_ia(provedor, mensagens, max_tokens=1500)


