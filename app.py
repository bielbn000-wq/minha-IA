import json
import time
import uuid
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from groq import Groq

if "mensagens" not in st.session_state:
    st.session_state.mensagens = []
if "adm_job" not in st.session_state:
    st.session_state.adm_job = None

modo = st.radio("Modo de conversa", ["Normal", "ADM"], horizontal=True)

# O componente recebe o trabalho pendente e devolve um dicionário quando terminar.
if modo == "ADM":
    job = st.session_state.adm_job
    resultado = puter_bridge(job=job, key="joytoy_puter_bridge")

    if (
        job is not None
        and isinstance(resultado, dict)
        and resultado.get("id") == job.get("id")
    ):
        erro = resultado.get("error")
        texto = (resultado.get("answer") or "").strip()

        if erro:
            st.session_state.mensagens.append({
                "role": "assistant",
                "content": f"Não consegui obter uma resposta do ADM: {erro}",
            })
        elif texto:
            st.session_state.mensagens.append({
                "role": "assistant",
                "content": texto,
            })
        else:
            st.session_state.mensagens.append({
                "role": "assistant",
                "content": "O modelo retornou uma resposta vazia. Tente novamente.",
            })

        st.session_state.adm_job = None
        st.rerun()

# Histórico compartilhado e renderizado com a interface nativa do Streamlit.
for mensagem in st.session_state.mensagens:
    with st.chat_message(mensagem["role"]):
        st.markdown(mensagem["content"])

aguardando_adm = modo == "ADM" and st.session_state.adm_job is not None
pergunta = st.chat_input(
    "Aguarde a resposta do ADM..." if aguardando_adm else "Digite sua mensagem...",
    disabled=aguardando_adm,
)

if pergunta and pergunta.strip():
    texto_usuario = pergunta.strip()
    st.session_state.mensagens.append({
        "role": "user",
        "content": texto_usuario,
    })

    if modo == "ADM":
        # Monta o contexto com o histórico, incluindo a mensagem recém-enviada.
        partes = ["INSTRUÇÕES DO SISTEMA:\n" + PROMPT_PADRAO]
        for item in st.session_state.mensagens:
            rotulo = "Usuário" if item["role"] == "user" else "JoyToy"
            partes.append(f"{rotulo}: {item['content']}")
        partes.append("JoyToy:")

        st.session_state.adm_job = {
            "id": uuid.uuid4().hex,
            "prompt": "\n\n".join(partes),
            "model": MODELO_ADM,
        }
        st.rerun()

    else:
        try:
            chave_api = st.secrets["GROQ_API_KEY"]
            cliente = Groq(api_key=chave_api)
        except Exception:
            st.error("Configure GROQ_API_KEY em Streamlit → Settings → Secrets.")
            st.stop()

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
                texto = resposta.choices[0].message.content or "Não recebi uma resposta da IA."
                st.markdown(texto)
                st.session_state.mensagens.append({
                    "role": "assistant",
                    "content": texto,
                })
            except Exception as erro:
                st.error("Não foi possível obter uma resposta da Groq.")
                st.code(f"{type(erro).__name__}: {str(erro)[:500]}")

if st.session_state.mensagens or st.session_state.adm_job:
    if st.button("Limpar conversa", use_container_width=True):
        st.session_state.mensagens = []
        st.session_state.adm_job = None
        st.rerun()
