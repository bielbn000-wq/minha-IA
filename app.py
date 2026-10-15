import uuid
import streamlit as st
from groq import Groq

# =====================================
# JOYTOY AI
# =====================================

MODELO_NORMAL = "openai/gpt-oss-20b"

MODELO_ADM = (
    "cognitivecomputations/"
    "dolphin-mistral-24b-venice-edition"
)

PROMPT_PADRAO = """
Você é o JoyToy AI, uma inteligência artificial amigável.

Responda em português quando o usuário falar português.
Seja natural, inteligente e direto.
Explique assuntos difíceis de forma simples.
Considere o histórico da conversa.
"""

st.set_page_config(
    page_title="JoyToy AI",
    page_icon="🤖",
    layout="centered",
)

# =====================================
# PUTER.JS - COMPONENTE DE COMUNICAÇÃO
# =====================================

ADM_HTML = '<div id="joytoy-adm-bridge"></div>'

ADM_JS = r"""
export default function(component) {
    const { data, setStateValue } = component;
    const job = data?.job;

    if (!job?.id || !job?.prompt || !job?.model) return;

    // Evita executar o mesmo pedido novamente nos reruns.
    window.__joytoyPuterJobs ??= {};

    if (window.__joytoyPuterJobs[job.id]) return;
    window.__joytoyPuterJobs[job.id] = true;

    async function carregarPuter() {
        if (window.puter?.ai) return window.puter;

        if (!window.__joytoyPuterLoading) {
            window.__joytoyPuterLoading = new Promise(
                (resolve, reject) => {
                    const script = document.createElement("script");
                    script.src = "https://js.puter.com/v2/";

                    script.onload = () => {
                        if (window.puter?.ai) {
                            resolve(window.puter);
                        } else {
                            reject(
                                new Error(
                                    "Puter.js carregou, mas a API não apareceu."
                                )
                            );
                        }
                    };

                    script.onerror = () => reject(
                        new Error("Não foi possível carregar o Puter.js.")
                    );

                    document.head.appendChild(script);
                }
            );
        }

        return await window.__joytoyPuterLoading;
    }

    async function executar() {
        const controller = new AbortController();
        let timer;

        try {
            const puter = await carregarPuter();

            const pedido = puter.ai.chat(job.prompt, {
                model: job.model,
                normalize: true,
                signal: controller.signal
            });

            const limite = new Promise((_, reject) => {
                timer = setTimeout(() => {
                    controller.abort();
                    reject(
                        new Error(
                            "Tempo esgotado após 15 segundos. Tente novamente."
                        )
                    );
                }, 15000);
            });

            const resposta = await Promise.race([pedido, limite]);

            let texto =
                resposta?.message?.content ??
                resposta?.choices?.[0]?.message?.content ??
                resposta?.text ??
                "";

            if (Array.isArray(texto)) {
                texto = texto.map(item =>
                    typeof item === "string"
                        ? item
                        : (item?.text || "")
                ).join("");
            }

            if (typeof texto !== "string" || !texto.trim()) {
                throw new Error("O modelo retornou uma resposta vazia.");
            }

            setStateValue("response", {
                id: job.id,
                answer: texto.trim(),
                error: null
            });

        } catch (erro) {
            setStateValue("response", {
                id: job.id,
                answer: "",
                error: erro?.message || String(erro)
            });

        } finally {
            if (timer) clearTimeout(timer);
        }
    }

    executar();
}
"""

adm_component = st.components.v2.component(
    "joytoy_adm_bridge_v2",
    html=ADM_HTML,
    js=ADM_JS,
)

# =====================================
# ESTADO
# =====================================

if "mensagens" not in st.session_state:
    st.session_state.mensagens = []

if "adm_job" not in st.session_state:
    st.session_state.adm_job = None

# =====================================
# CABEÇALHO E MODOS
# =====================================

st.title("JoyToy AI")
st.caption("Sua inteligência artificial")

modo = st.radio(
    "Modo de conversa",
    ["Normal", "ADM"],
    horizontal=True,
)

if modo == "Normal":
    st.caption(f"Modelo: {MODELO_NORMAL} · Groq")
else:
    st.caption(f"Modelo: {MODELO_ADM} · Puter.js")

# =====================================
# LIMPAR CONVERSA
# =====================================

if st.button(
    "Limpar conversa",
    disabled=st.session_state.adm_job is not None,
):
    st.session_state.mensagens = []
    st.session_state.adm_job = None
    st.rerun()

# =====================================
# COMPONENTE ADM
# =====================================

resultado_componente = None

if modo == "ADM":
    resultado_componente = adm_component(
        data={"job": st.session_state.adm_job},
        key="joytoy_adm_bridge_instance",
        on_response_change=lambda: None,
    )

    job = st.session_state.adm_job
    resultado = getattr(
        resultado_componente,
        "response",
        None,
    )

    if (
        job is not None
        and isinstance(resultado, dict)
        and resultado.get("id") == job.get("id")
    ):
        erro = resultado.get("error")
        texto = (resultado.get("answer") or "").strip()

        if erro:
            conteudo = f"Erro no modo ADM: {erro}"
        elif texto:
            conteudo = texto
        else:
            conteudo = "O modelo retornou uma resposta vazia."

        st.session_state.mensagens.append({
            "role": "assistant",
            "content": conteudo,
        })

        st.session_state.adm_job = None
        st.rerun()

# =====================================
# HISTÓRICO NATIVO DO STREAMLIT
# =====================================

for mensagem in st.session_state.mensagens:
    with st.chat_message(mensagem["role"]):
        st.markdown(mensagem["content"])

if modo == "ADM" and st.session_state.adm_job is not None:
    st.info("O ADM está processando sua mensagem...")

# =====================================
# ENTRADA DE MENSAGENS
# =====================================

pergunta = st.chat_input(
    "Converse com o JoyToy...",
    disabled=st.session_state.adm_job is not None,
)

if pergunta:
    st.session_state.mensagens.append({
        "role": "user",
        "content": pergunta,
    })

    if modo == "ADM":
        historico = []

        for mensagem in st.session_state.mensagens:
            papel = (
                "Usuário"
                if mensagem["role"] == "user"
                else "JoyToy"
            )
            historico.append(
                f"{papel}: {mensagem['content']}"
            )

        prompt = (
            PROMPT_PADRAO
            + "\n\nHistórico da conversa:\n"
            + "\n".join(historico)
            + "\n\nJoyToy:"
        )

        st.session_state.adm_job = {
            "id": uuid.uuid4().hex,
            "prompt": prompt,
            "model": MODELO_ADM,
        }

        st.rerun()

    else:
        with st.chat_message("user"):
            st.markdown(pergunta)

        try:
            api_key = st.secrets.get("GROQ_API_KEY", "")

            if not api_key:
                raise ValueError(
                    "Configure GROQ_API_KEY nos Secrets do Streamlit."
                )

            cliente = Groq(
                api_key=api_key,
                timeout=30.0,
            )

            with st.chat_message("assistant"):
                with st.spinner("JoyToy está pensando..."):
                    resposta = cliente.chat.completions.create(
                        model=MODELO_NORMAL,
                        messages=[
                            {
                                "role": "system",
                                "content": PROMPT_PADRAO,
                            },
                            *st.session_state.mensagens,
                        ],
                        temperature=0.7,
                        max_completion_tokens=2048,
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
            mensagem_erro = f"Erro no modo Normal: {erro}"

            st.session_state.mensagens.append({
                "role": "assistant",
                "content": mensagem_erro,
            })

            st.error(mensagem_erro)
