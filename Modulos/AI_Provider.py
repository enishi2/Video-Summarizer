import os
from dotenv import load_dotenv
import time

load_dotenv()

"""
ai_provider
Detecta qual provedor de IA está disponível e com créditos funcionando.
Tenta OpenAI primeiro, depois Claude.
"""


def _testar_groq():
    chave = os.getenv("GROQ_API_KEY", "").strip()
    if not chave:
        return False, "Chave não configurada"
    try:
        from groq import Groq
        cliente = Groq(api_key=chave)
        cliente.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "oi"}],
            max_tokens=5,
        )
        return True, "ok"
    except Exception as e:
        return False, str(e)


def _testar_openai():
    chave = os.getenv("OPENAI_API_KEY", "").strip()
    if not chave:
        return False, "chave não configurada"
    try:
        from openai import OpenAI
        cliente = OpenAI(api_key=chave)
        cliente.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "oi"}],
            max_tokens=5,
        )
        return True, "OpenAI funcionando"
    except Exception as e:
        return False, str(e)

def _testar_claude():
    chave = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not chave:
        return False, "chave não configurada"
    try:
        import anthropic
        cliente = anthropic.Anthropic(api_key=chave)
        cliente.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=5,
            messages=[{"role": "user", "content": "oi"}], 
        )
        return True, "ok"
    except Exception as e:
        return False, str(e)
    

def detectar_provedor():
    """
    Retorna 'openai' ou 'claude'.
    Testa OpenAI primeiro; se falhar, testa Claude.
    """
    print("Verificando provedores de IA disponíveis...")

    ok, motivo = _testar_groq()
    if ok:
        print("Groq disponível e funcionando.")
        return "groq"
    else:
        print(f"Groq indisponível: {motivo}")

    ok, motivo = _testar_openai()
    if ok:
        print("OpenAI disponível e funcionando.")
        return "openai"
    else:
        print(f"OpenAI indisponível: {motivo}")

    ok, motivo = _testar_claude()
    if ok:
        print("Claude (Anthropic) disponível e funcionando.")
        return "claude"
    else:
        print(f"Claude indisponível: {motivo}")

    raise RuntimeError(
        "Nenhum provedor de IA disponível.\n"
        "Verifique suas chaves no arquivo .env."
    )


import time

def _chamar_ia_direto(provedor: str, mensagens: list, max_tokens: int = 1024) -> str:
    """Faz a chamada direta ao provedor sem retry."""
    if provedor == "openai":
        from openai import OpenAI
        cliente = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        resposta = cliente.chat.completions.create(
            model="gpt-4o-mini",
            messages=mensagens,
            max_tokens=max_tokens,
        )
        return resposta.choices[0].message.content.strip()

    elif provedor == "groq":
        from groq import Groq
        cliente = Groq(api_key=os.getenv("GROQ_API_KEY"))
        resposta = cliente.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=mensagens,
            max_tokens=max_tokens,
        )
        return resposta.choices[0].message.content.strip()

    elif provedor == "claude":
        import anthropic
        system_msg = ""
        msgs_filtradas = []
        for m in mensagens:
            if m["role"] == "system":
                system_msg = m["content"]
            else:
                msgs_filtradas.append(m)

        cliente = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        kwargs = dict(
            model="claude-haiku-4-5-20251001",
            max_tokens=max_tokens,
            messages=msgs_filtradas,
        )
        if system_msg:
            kwargs["system"] = system_msg

        resposta = cliente.messages.create(**kwargs)
        return resposta.content[0].text.strip()

    else:
        raise ValueError(f"Provedor desconhecido: {provedor}")


def chamar_ia(provedor: str, mensagens: list, max_tokens: int = 1024) -> str:
    """
    Chama o provedor escolhido com retry automático em caso de rate limit.
    Formato: [{"role": "user"/"assistant"/"system", "content": "..."}]
    Retorna o texto da resposta.
    """
    tentativas = 3
    espera = 3  # começa com 3s, dobra a cada falha: 3s → 6s → 12s

    for tentativa in range(tentativas):
        try:
            return _chamar_ia_direto(provedor, mensagens, max_tokens)
        except Exception as e:
            erro = str(e)
            if "429" in erro or "rate_limit" in erro.lower():
                if tentativa < tentativas - 1:
                    print(f"   Rate limit atingido. Aguardando {espera}s antes de tentar novamente...")
                    time.sleep(espera)
                    espera *= 2
                else:
                    raise RuntimeError(
                        "Rate limit atingido após 3 tentativas. "
                        "Aguarde alguns segundos e tente novamente."
                    )
            else:
                raise  # qualquer outro erro sobe normalmente