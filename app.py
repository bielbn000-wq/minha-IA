import streamlit as st
from groq import Groq
from openai import OpenAI

MODELO_NORMAL = "openai/gpt-oss-20b"

PROMPT_PADRAO = """
Você é o JoyToy AI, uma inteligência artificial amigável.
Responda em português quando o usuário falar português.
Seja natural, inteligente e direto.
Explique assuntos difíceis de forma simples.
Não invente informações; admita quando não souber.
"""

st.set_page_config(page_title="JoyToy AI", page_icon="🤖", layout="centered")
st.title("JoyToy AI")
st.caption("Converse diretamente com o JoyToy, a sua inteligência artificial.")

if "mensagens" not in st.session_state:
    st.session_state.mensagens = []

modo = st.radio(
    "Modo de conversa",
    ["Normal", "ADM"],
    horizontal=True,
    help="Normal usa a Groq. ADM usa a API privada configurada nos Secrets.",
)

cliente = None
modelo = None
nome_provedor = ""

try:
    if modo == "Normal":
        chave_api = st.secrets["GROQ_API_KEY"]
        cliente = Groq(api_key=chave_api)
        modelo = MODELO_NORMAL
        nome_provedor = "Groq"
    else:
        chave_api = st.secrets["JOYTOY_API_KEY"]
        modelo = st.secrets["JOYTOY_MODEL"]
        base_url = st.secrets["JOYTOY_BASE_URL"]
        cliente = OpenAI(api_key=chave_api, base_url=base_url)
        nome_provedor = "JOYTOY"
except KeyError as erro:
    faltando = str(erro).strip("'")
    if modo == "Normal":
        st.error(f"Configure {faltando} em Streamlit → Settings → Secrets.")
    else:
        st.error(
            f"Configure {faltando} em Streamlit → Settings → Secrets. "
            "O modo ADM precisa da chave, do nome do modelo e da URL "
            "base fornecidos pelo provedor."
        )
    st.stop()
except Exception as erro:
    st.error(f"Não foi possível inicializar a API selecionada ({modo}).")
    st.code(f"{type(erro).__name__}: {str(erro)[:500]}", language="text")
    st.stop()

for mensagem in st.session_state.mensagens:
    with st.chat_message(mensagem["role"]):
        st.markdown(mensagem["content"])

pergunta = st.chat_input("Digite sua mensagem...")

if pergunta and pergunta.strip():
    texto_usuario = pergunta.strip()
    st.session_state.mensagens.append({"role": "user", "content": texto_usuario})

    with st.chat_message("user"):
        st.markdown(texto_usuario)

    with st.chat_message("assistant"):
        area_resposta = st.empty()
        try:
            resposta = cliente.chat.completions.create(
                model=modelo,
                messages=[
                    {"role": "system", "content": PROMPT_PADRAO},
                    *st.session_state.mensagens,
                ],
                max_completion_tokens=2048,
            )
            texto_resposta = (
                resposta.choices[0].message.content
                or "Não recebi uma resposta da IA."
            )
            area_resposta.markdown(texto_resposta)
            st.session_state.mensagens.append(
                {"role": "assistant", "content": texto_resposta}
            )
        except Exception as erro:
            status = getattr(erro, "status_code", None)
            detalhe = str(erro)
            if chave_api:
                detalhe = detalhe.replace(str(chave_api), "[CHAVE OCULTA]")
            detalhe = detalhe[:700] or "Sem detalhes fornecidos pela biblioteca."

            if status == 401:
                orientacao = f"A API de {nome_provedor} recusou a chave. Confira o Secret correspondente."
            elif status == 403:
                orientacao = f"A conta não tem permissão para usar este modelo na API de {nome_provedor}."
            elif status == 404:
                orientacao = f"O modelo ou endpoint não foi encontrado. Confira o modelo e a URL da API de {nome_provedor}."
            elif status == 429:
                orientacao = f"O limite de uso da API de {nome_provedor} foi atingido. Confira sua cota e tente novamente mais tarde."
            elif status == 400:
                orientacao = f"A API de {nome_provedor} recusou os parâmetros ou o formato das mensagens."
            elif status is not None and status >= 500:
                orientacao = f"A API de {nome_provedor} apresentou um erro no servidor. Tente novamente mais tarde."
            elif type(erro).__name__ in ("APIConnectionError", "APITimeoutError"):
                orientacao = f"Não foi possível conectar à API de {nome_provedor}. Confira a URL base e a conexão."
            else:
                orientacao = f"Não foi possível obter uma resposta da API de {nome_provedor}."

            area_resposta.error(orientacao)
            st.code(
                f"Erro: {type(erro).__name__}"
                + (f" | HTTP {status}" if status else "")
                + f"\n{detalhe}",
                language="text",
            )

if st.session_state.mensagens:
    if st.button("Limpar conversa", use_container_width=True):
        st.session_state.mensagens = []
        st.rerun()
