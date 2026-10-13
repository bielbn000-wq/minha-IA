import streamlit as st
from groq import Groq

MODELO = "openai/gpt-oss-20b"

st.set_page_config(
    page_title="Minha IA",
    page_icon="🤖",
    layout="centered",
)

st.title("🤖 Minha IA")
st.caption("Converse diretamente com a inteligência artificial.")

# O histórico existe apenas na sessão atual do Streamlit. Não é gravado em arquivo.
if "mensagens" not in st.session_state:
    st.session_state.mensagens = []

try:
    chave_api = st.secrets["GROQ_API_KEY"]
except Exception:
    st.error("A chave GROQ_API_KEY não foi configurada nos Secrets do Streamlit.")
    st.stop()

cliente = Groq(api_key=chave_api)

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
                model=MODELO,
                messages=st.session_state.mensagens,
                max_completion_tokens=2048,
            )
            texto_resposta = resposta.choices[0].message.content or "Não recebi uma resposta da IA."
            area_resposta.markdown(texto_resposta)
            st.session_state.mensagens.append(
                {"role": "assistant", "content": texto_resposta}
            )
        except Exception as erro:
            # Mostra o motivo útil sem revelar a chave da API.
            status = getattr(erro, "status_code", None)
            detalhe = str(erro).replace(str(chave_api), "[CHAVE OCULTA]").strip()
            detalhe = detalhe[:700] if detalhe else "Sem detalhes fornecidos pela biblioteca."

            if status == 401:
                orientacao = "A Groq recusou a autenticação. Confira se GROQ_API_KEY está correto, completo e ativo nos Secrets."
            elif status == 403:
                orientacao = "A chave foi reconhecida, mas a conta não tem permissão para esta operação ou modelo."
            elif status == 404:
                orientacao = f"O modelo ou endpoint não foi encontrado. Modelo configurado: {MODELO}."
            elif status == 429:
                orientacao = "O limite de requisições ou tokens da Groq foi atingido. Aguarde a renovação do limite ou confira o painel da Groq."
            elif status == 400:
                orientacao = "A Groq recusou os parâmetros ou o formato das mensagens enviados."
            elif status is not None and status >= 500:
                orientacao = "A API da Groq retornou um erro no servidor. Tente novamente em alguns minutos."
            elif erro.__class__.__name__ in ("APIConnectionError", "APITimeoutError"):
                orientacao = "Não foi possível conectar à API da Groq. Confira a conexão e tente novamente."
            else:
                orientacao = "Confira o detalhe técnico abaixo; ele indica a causa que a mensagem anterior escondia."

            area_resposta.error(orientacao)
            st.code(f"Erro: {erro.__class__.__name__}" + (f" | HTTP {status}" if status else "") + f"\n{detalhe}", language="text")

if st.session_state.mensagens:
    if st.button("Limpar conversa", use_container_width=True):
        st.session_state.mensagens = []
        st.rerun()
