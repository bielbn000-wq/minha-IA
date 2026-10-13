import streamlit as st
from groq import Groq

st.set_page_config(
    page_title="Minha IA",
    page_icon="🤖",
    layout="centered",
)

st.title("🤖 Minha IA")
st.caption("Um chat simples com inteligência artificial")

if "mensagens" not in st.session_state:
    st.session_state.mensagens = []

try:
    api_key = st.secrets["GROQ_API_KEY"]
except Exception:
    st.error("Configure GROQ_API_KEY nos Secrets do Streamlit.")
    st.stop()

cliente = Groq(api_key=api_key)

for mensagem in st.session_state.mensagens:
    with st.chat_message(mensagem["role"]):
        st.markdown(mensagem["content"])

pergunta = st.chat_input("Digite sua mensagem...")

if pergunta:
    st.session_state.mensagens.append({"role": "user", "content": pergunta})
    with st.chat_message("user"):
        st.markdown(pergunta)

    with st.chat_message("assistant"):
        area = st.empty()
        try:
            resposta = cliente.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=st.session_state.mensagens,
                temperature=0.7,
                max_completion_tokens=2048,
            )
            texto = resposta.choices[0].message.content or "Não recebi uma resposta da IA."
            area.markdown(texto)
            st.session_state.mensagens.append({"role": "assistant", "content": texto})
        except Exception as erro:
            area.error("Não foi possível obter uma resposta. Confira a chave da API, a conexão e o modelo configurado.")
            # Detalhes técnicos ficam apenas nos logs do servidor, não são expostos no chat.
            print(f"Erro na chamada da API Groq: {erro}")

if st.button("Limpar conversa", use_container_width=True):
    st.session_state.mensagens = []
    st.rerun()
