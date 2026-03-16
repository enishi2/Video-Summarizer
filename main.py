from Modulos.AI_Provider import detectar_provedor
from Modulos.transcript import obter_transcricao
from Modulos.processor import corrigir_texto, gerar_resumo
from Modulos.chatbot import iniciar_chatbot

"""
main.py
Ponto de entrada do programa.
Orquestra todas as etapas em sequência.
"""



def main():
    print("\n" + "="*60)
    print("RESUMIDOR DE VÍDEOS DO YOUTUBE")
    print("="*60 + "\n")

    # ── 1. Detectar provedor ──────────────────────────────────
    try:
        provedor = detectar_provedor()
    except RuntimeError as e:
        print(f"\n{e}")
        return

    # ── 2. Receber URL ────────────────────────────────────────
    print()
    url = input("Cole a URL do vídeo: ").strip()
    if not url:
        print("URL não pode ser vazia.")
        return

    # ── 3. Obter transcrição ──────────────────────────────────
    print()
    try:
        transcricao_bruta, metodo = obter_transcricao(url, provedor)
        metodo_label = "legenda" if metodo == "legenda" else "transcrição de áudio"
        print(f"   Método: {metodo_label}")
    except Exception as e:
        print(f"\nErro ao obter transcrição: {e}")
        return

    # ── 4. Corrigir texto ─────────────────────────────────────
    print()
    try:
        transcricao_corrigida = corrigir_texto(transcricao_bruta, provedor)
    except Exception as e:
        print(f"\nErro na correção: {e}")
        return

    # ── 5. Gerar resumo ───────────────────────────────────────
    print()
    try:
        resumo = gerar_resumo(transcricao_corrigida, provedor)
    except Exception as e:
        print(f"\nErro ao gerar resumo: {e}")
        return

    # ── Exibir resumo ─────────────────────────────────────────
    print("\n" + "="*60)
    print("RESUMO DO VÍDEO")
    print("="*60)
    print(resumo)
    print("="*60 + "\n")

    # ── 6. Chatbot ────────────────────────────────────────────
    resp = input("Deseja perguntar sobre o vídeo? (s/n): ").strip().lower()
    if resp in {"s", "sim", "y", "yes"}:
        iniciar_chatbot(transcricao_corrigida, resumo, provedor)

    print("\nPrograma encerrado. Até mais!")

if __name__ == "__main__":
    main()