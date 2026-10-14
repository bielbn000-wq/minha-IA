
import json
import time
import uuid

import streamlit as st
import streamlit.components.v1 as components
from groq import Groq

MODELO_NORMAL = "openai/gpt-oss-20b"
MODELO_ADM = "cognitivecomputations/dolphin-mistral-24b-venice-edition"

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

st.title("🤖 JoyToy AI")
st.caption("Converse diretamente com o JoyToy, a sua inteligência artificial.")

if "mensagens" not in st.session_state:
    st.session_state.mensagens = []

if "adm_pendentes" not in st.session_state:
    st.session_state.adm_pendentes = {}

if "adm_resultados" not in st.session_state:
    st.session_state.adm_resultados = {}

if "adm_id" not in st.session_state:
    st.session_state.adm_id = None

modo = st.radio(
    "Modo de conversa",
    ["Normal", "ADM"],
    horizontal=True,
)

if modo == "ADM":
    st.session_state.adm_id = (
        st.session_state.adm_id or uuid.uuid4().hex
    )

# Exibe o histórico no layout nativo do Streamlit.
for mensagem in st.session_state.mensagens:
    with st.chat_message(mensagem["role"]):
        st.markdown(mensagem["content"])

# O componente usa um canal de armazenamento do navegador como ponte.
# A chamada ao Puter ocorre no navegador; não usa uma chave de API Python.
if modo == "ADM":
    components.html(
        """
        <script src="https://js.puter.com/v2/"></script>
        <script>
        (function () {
          const KEY = "joytoy_adm_queue";
          const RESULT = "joytoy_adm_result";

          async function processQueue() {
            try {
              if (!window.puter || !puter.ai) return;

              const raw = localStorage.getItem(KEY);
              if (!raw) return;

              const job = JSON.parse(raw);
              if (!job || !job.id || job.status === "running") return;

              job.status = "running";
              localStorage.setItem(KEY, JSON.stringify(job));

              try {
                const result = await puter.ai.chat(job.prompt, {
                  model: job.model
                });

                let answer = "";
                if (typeof result === "string") {
                  answer = result;
                } else {
                  const content =
                    result?.message?.content ??
                    result?.choices?.[0]?.message?.content ??
                    result?.text;

                  answer = typeof content === "string"
                    ? content
                    : JSON.stringify(content ?? result);
                }

                localStorage.setItem(RESULT, JSON.stringify({
                  id: job.id,
                  answer: answer,
                  error: null
                }));
              } catch (error) {
                localStorage.setItem(RESULT, JSON.stringify({
                  id: job.id,
                  answer: "",
                  error: error?.message || String(error)
                }));
              } finally {
                localStorage.removeItem(KEY);
              }
            } catch (e) {
              // Evita quebrar o componente em caso de erro de armazenamento.
            }
          }

          processQueue();
          setInterval(processQueue, 1000);
        })();
        </script>
        """,
        height=0,
        scrolling=False,
    )

    # Ler o resultado no Python exige um componente que devolva dados
    # do navegador. components.html não oferece esse canal de retorno.
    st.caption(
        "O chat ADM usa a interface nativa, mas a comunicação de retorno "
        "do Puter precisa de um componente Streamlit com suporte a "
        "JavaScript ↔ Python."
    )

    pergunta = st.chat_input("Digite sua mensagem...")

    if pergunta and pergunta.strip():
        st.session_state.mensagens.append({
            "role": "user",
            "content": pergunta.strip(),
        })
        st.rerun()

else:
    try:
        chave_api = st.secrets["GROQ_API_KEY"]
        cliente = Groq(api_key=chave_api)
    except Exception:
        st.error("Configure GROQ_API_KEY em Streamlit → Settings → Secrets.")
        st.stop()

    pergunta = st.chat_input("Digite sua mensagem...")

    if pergunta and pergunta.strip():
        texto_usuario = pergunta.strip()

        st.session_state.mensagens.append({
            "role": "user",
            "content": texto_usuario,
        })

        with st.chat_message("assistant"):
            try:
                resposta = cliente.chat.completions.create(
                    model=MODELO_NORMAL,
                    messages=[
                        {"role": "system", "content": PROMPT_PADRAO},
                        *st.session_state.mensagens,
                    ],
                    max_completion_tokens=2048,
                )

                texto = (
                    resposta.choices[0].message.content
                    or "Não recebi uma resposta da IA."
                )

                st.markdown(texto)
                st.session_state.mensagens.append({
                    "role": "assistant",
                    "content": texto,
                })

            except Exception as erro:
                st.error("Não foi possível obter uma resposta da Groq.")
                st.code(f"{type(erro).__name__}: {str(erro)[:500]}")

if st.session_state.mensagens:
    if st.button("Limpar conversa", use_container_width=True):
        st.session_state.mensagens = []
        st.session_state.adm_pendentes = {}
        st.session_state.adm_resultados = {}
        st.rerun()
