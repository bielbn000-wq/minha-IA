
import streamlit as st
from groq import Groq

MODELO = "openai/gpt-oss-20b"

PROMPT_PADRAO = """
Você é o JoyToy AI, uma inteligência artificial amigável.

Responda em português quando o usuário falar português.
Seja natural, inteligente e direto.
Explique assuntos difíceis de forma simples.
Não invente informações; admita quando não souber.
"""

st.set_page_config(
    page_title="JoyToy AI",
    page_icon="🤖",
    layout="centered",
)

st.title("JoyToy AI")
st.caption(
    "Converse diretamente com o JoyToy, "
    "a sua inteligência artificial."
)

# O histórico existe apenas na sessão atual.
# Não é gravado em arquivos.
if "mensagens" not in st.session_state:
    st.session_state.mensagens = []

# Obter a chave da API
try:
    chave_api = st.secrets["GROQ_API_KEY"]
except Exception:
    st.error(
        "A chave GROQ_API_KEY não foi configurada "
        "nos Secrets do Streamlit."
    )
    st.stop()

# Inicializar o cliente
try:
    cliente = Groq(api_key=chave_api)
except Exception as erro:
    st.error("Não foi possível inicializar a conexão com a Groq.")
    st.code(
        f"Erro: {type(erro).__name__}\n{str(erro)[:500]}",
        language="text",
    )
    st.stop()

# Exibir o histórico da sessão
for mensagem in st.session_state.mensagens:
    with st.chat_message(mensagem["role"]):
        st.markdown(mensagem["content"])

# Campo de mensagem
pergunta = st.chat_input("Digite sua mensagem...")

if pergunta and pergunta.strip():
    texto_usuario = pergunta.strip()

    # Guardar a mensagem do usuário na sessão
    st.session_state.mensagens.append({
        "role": "user",
        "content": texto_usuario,
    })

    with st.chat_message("user"):
        st.markdown(texto_usuario)

    with st.chat_message("assistant"):
        area_resposta = st.empty()

        try:
            resposta = cliente.chat.completions.create(
                model=MODELO,
                messages=[
                    {
                        "role": "system",
                        "content": PROMPT_PADRAO,
                    },
                    *st.session_state.mensagens,
                ],
                max_completion_tokens=2048,
            )

            texto_resposta = (
                resposta.choices[0].message.content
                or "Não recebi uma resposta da IA."
            )

            area_resposta.markdown(texto_resposta)

            # Guardar a resposta na sessão
            st.session_state.mensagens.append({
                "role": "assistant",
                "content": texto_resposta,
            })

        except Exception as erro:
            status = getattr(erro, "status_code", None)

            # Evitar mostrar a chave da API na mensagem técnica
            detalhe = str(erro)
            if chave_api:
                detalhe = detalhe.replace(
                    str(chave_api),
                    "[CHAVE OCULTA]",
                )

            detalhe = (
                detalhe[:700]
                if detalhe
                else "Sem detalhes fornecidos pela biblioteca."
            )

            if status == 401:
                orientacao = (
                    "A Groq recusou a autenticação. "
                    "Confira se GROQ_API_KEY está correta "
                    "e ativa nos Secrets."
                )
            elif status == 403:
                orientacao = (
                    "A conta não tem permissão para esta "
                    "operação ou modelo."
                )
            elif status == 404:
                orientacao = (
                    f"O modelo ou endpoint não foi encontrado: {MODELO}."
                )
            elif status == 429:
                orientacao = (
                    "O limite da Groq foi atingido. "
                    "Confira sua cota e tente novamente mais tarde."
                )
            elif status == 400:
                orientacao = (
                    "A Groq recusou os parâmetros ou as mensagens."
                )
            elif status is not None and status >= 500:
                orientacao = (
                    "A API da Groq apresentou um erro no servidor. "
                    "Tente novamente mais tarde."
                )
            elif type(erro).__name__ in (
                "APIConnectionError",
                "APITimeoutError",
            ):
                orientacao = (
                    "Não foi possível conectar à Groq. "
                    "Confira a conexão e tente novamente."
                )
            else:
                orientacao = (
                    "Não foi possível obter uma resposta. "
                    "Confira o erro técnico abaixo."
                )

            area_resposta.error(orientacao)

            st.code(
                f"Erro: {type(erro).__name__}"
                + (f" | HTTP {status}" if status else "")
                + f"\n{detalhe}",
                language="text",
            )

# Limpar o histórico temporário
if st.session_state.mensagens:
    if st.button("Limpar conversa", use_container_width=True):
        st.session_state.mensagens = []
        st.rerun()
