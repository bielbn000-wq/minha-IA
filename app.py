```python
import streamlit as st
from groq import Groq
from openai import OpenAI

# =========================
# JOYTOY AI - CONFIGURAÇÃO
# =========================

MODELO_NORMAL = "openai/gpt-oss-20b"
MODELO_ADM = "dolphin3"

PROMPT_PADRAO = """
Você é o JoyToy AI, uma inteligência artificial amigável.

Responda em português quando o usuário falar português.
Seja inteligente, natural, útil e direto.
Explique assuntos difíceis de forma simples.
Use o histórico da conversa para manter o contexto.
"""

st.set_page_config(
    page_title="JoyToy AI",
    page_icon="🤖",
    layout="centered",
)

st.title("🤖 JoyToy AI")
st.caption("Sua inteligência artificial")

# =========================
# ESTADO DA CONVERSA
# =========================

if "mensagens" not in st.session_state:
    st.session_state.mensagens = []

# =========================
# SELEÇÃO DO MODO
# =========================

modo = st.radio(
    "Modo de conversa",
    ["Normal", "ADM"],
    horizontal=True,
)

if modo == "Normal":
    st.caption(f"Modelo: {MODELO_NORMAL} | Provedor: Groq")
else:
    st.caption(f"Modelo: {MODELO_ADM} | Provedor: Ollama Cloud")

# =========================
# LIMPAR CONVERSA
# =========================

if st.button("🗑️ Limpar conversa"):
    st.session_state.mensagens = []
    st.rerun()

# =========================
# EXIBIR HISTÓRICO
# =========================

for mensagem in st.session_state.mensagens:
    with st.chat_message(mensagem["role"]):
        st.markdown(mensagem["content"])

# =========================
# ENVIAR MENSAGEM
# =========================

pergunta = st.chat_input("Converse com o JoyToy...")

if pergunta:
    st.session_state.mensagens.append({
        "role": "user",
        "content": pergunta,
    })

    with st.chat_message("user"):
        st.markdown(pergunta)

    mensagens_api = [
        {
            "role": "system",
            "content": PROMPT_PADRAO,
        },
        *st.session_state.mensagens,
    ]

    with st.chat_message("assistant"):
        try:
            with st.spinner("JoyToy está pensando..."):

                # MODO NORMAL: GROQ
                if modo == "Normal":
                    api_key = st.secrets.get(
                        "GROQ_API_KEY", ""
                    )

                    if not api_key:
                        raise ValueError(
                            "Configure GROQ_API_KEY nos "
                            "Secrets do Streamlit."
                        )

                    cliente = Groq(
                        api_key=api_key,
                        timeout=30.0,
                    )

                    resposta = cliente.chat.completions.create(
                        model=MODELO_NORMAL,
                        messages=mensagens_api,
                        temperature=0.7,
                        max_completion_tokens=2048,
                    )

                # MODO ADM: OLLAMA CLOUD
                else:
                    api_key = st.secrets.get(
                        "OLLAMA_API_KEY", ""
                    )

                    if not api_key:
                        raise ValueError(
                            "Configure OLLAMA_API_KEY nos "
                            "Secrets do Streamlit."
                        )

                    cliente = OpenAI(
                        base_url="https://ollama.com/v1",
                        api_key=api_key,
                        timeout=15.0,
                    )

                    resposta = cliente.chat.completions.create(
                        model=MODELO_ADM,
                        messages=mensagens_api,
                        temperature=0.7,
                    )

                texto = (
                    resposta.choices[0].message.content or ""
                ).strip()

                if not texto:
                    texto = "O modelo retornou uma resposta vazia."

                st.markdown(texto)

                st.session_state.mensagens.append({
                    "role": "assistant",
                    "content": texto,
                })

        except Exception as erro:
            st.error(f"Erro no modo {modo}: {erro}")
```
