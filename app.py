
import streamlit as st
import streamlit.components.v1 as components
from groq import Groq
import json

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

modo = st.radio(
    "Modo de conversa",
    ["Normal", "ADM"],
    horizontal=True,
    help="Normal usa a Groq. ADM usa o Dolphin-Mistral pelo Puter.js.",
)

# =========================================================
# MODO ADM: Puter.js no navegador, sem API Key no backend
# =========================================================
if modo == "ADM":
    st.info(
        "Modo ADM: Dolphin-Mistral via Puter.js. "
        "A autenticação, se solicitada, acontece no navegador."
    )

    html_chat = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">

      <script src="https://js.puter.com/v2/"></script>

      <style>
        * { box-sizing: border-box; }

        body {
          margin: 0;
          font-family: Arial, sans-serif;
          color: #e8eaf0;
          background: transparent;
        }

        .container {
          border: 1px solid #343844;
          border-radius: 14px;
          padding: 12px;
          background: #17191f;
        }

        .header {
          font-size: 14px;
          color: #aeb6c8;
          margin-bottom: 12px;
        }

        #chat {
          height: 340px;
          overflow-y: auto;
          padding: 4px;
          display: flex;
          flex-direction: column;
          gap: 10px;
        }

        .message {
          padding: 11px 13px;
          border-radius: 12px;
          max-width: 94%;
          white-space: pre-wrap;
          overflow-wrap: anywhere;
          line-height: 1.5;
          font-size: 14px;
        }

        .user {
          background: #2457a6;
          color: white;
          align-self: flex-end;
        }

        .assistant {
          background: #292d36;
          color: #f1f3f7;
          align-self: flex-start;
        }

        .status {
          min-height: 20px;
          font-size: 12px;
          color: #aeb6c8;
          padding: 8px 2px;
        }

        .controls {
          display: flex;
          gap: 8px;
        }

        #prompt {
          flex: 1;
          width: 0;
          min-width: 0;
          border: 1px solid #414654;
          border-radius: 9px;
          background: #20232b;
          color: white;
          padding: 12px;
          outline: none;
          font-size: 14px;
        }

        button {
          border: 0;
          border-radius: 9px;
          padding: 11px 14px;
          cursor: pointer;
          font-weight: bold;
        }

        #send {
          background: #3677e8;
          color: white;
        }

        #clear {
          margin-top: 9px;
          background: #30343e;
          color: #e8eaf0;
          width: 100%;
        }

        button:disabled {
          opacity: 0.5;
          cursor: wait;
        }
      </style>
    </head>

    <body>
      <div class="container">
        <div class="header">
          Modelo: cognitivecomputations/dolphin-mistral-24b-venice-edition
        </div>

        <div id="chat" aria-live="polite"></div>
        <div id="status" class="status">Preparando conexão...</div>

        <div class="controls">
          <input
            id="prompt"
            type="text"
            placeholder="Digite sua mensagem..."
            autocomplete="off"
          >
          <button id="send" type="button">Enviar</button>
        </div>

        <button id="clear" type="button">Limpar conversa</button>
      </div>

      <script>
        const MODEL =
          "cognitivecomputations/dolphin-mistral-24b-venice-edition";

        const SYSTEM_PROMPT = __PROMPT__;

        const chat = document.getElementById("chat");
        const input = document.getElementById("prompt");
        const sendButton = document.getElementById("send");
        const clearButton = document.getElementById("clear");
        const status = document.getElementById("status");

        let history = [];
        let busy = false;

        function addMessage(role, content) {
          const element = document.createElement("div");
          element.className = "message " + role;
          element.textContent = content;
          chat.appendChild(element);
          chat.scrollTop = chat.scrollHeight;
          return element;
        }

        function extractText(result) {
          if (typeof result === "string") return result;

          const content = result?.message?.content
            ?? result?.choices?.[0]?.message?.content
            ?? result?.text;

          if (typeof content === "string") return content;

          if (Array.isArray(content)) {
            return content.map(item =>
              typeof item === "string" ? item : (item.text || "")
            ).join("");
          }

          return content == null
            ? ""
            : JSON.stringify(content, null, 2);
        }

        async function sendMessage() {
          const message = input.value.trim();

          if (!message || busy) return;

          if (!window.puter || !puter.ai) {
            status.textContent =
              "Puter.js não carregou. Atualize a página e tente novamente.";
            return;
          }

          busy = true;
          sendButton.disabled = true;
          input.value = "";

          addMessage("user", message);
          const answerBox = addMessage("assistant", "Pensando...");
          status.textContent = "Consultando o modelo...";

          try {
            // Inclui instruções e histórico no texto enviado ao modelo.
            const context = [
              "INSTRUÇÕES DO SISTEMA:\\n" + SYSTEM_PROMPT,
              ...history.map(item =>
                (item.role === "user" ? "Usuário: " : "JoyToy: ")
                + item.content
              ),
              "Usuário: " + message,
              "JoyToy:"
            ].join("\\n\\n");

            const result = await puter.ai.chat(context, {
              model: MODEL
            });

            const answer = extractText(result).trim();

            if (!answer) {
              throw new Error("O modelo retornou uma resposta vazia.");
            }

            answerBox.textContent = answer;

            history.push(
              { role: "user", content: message },
              { role: "assistant", content: answer }
            );

            status.textContent = "Resposta recebida.";
          } catch (error) {
            answerBox.textContent =
              "Não foi possível obter uma resposta. " +
              (error?.message || String(error));

            status.textContent =
              "Verifique o acesso ao Puter, a autenticação e a disponibilidade do modelo.";
          } finally {
            busy = false;
            sendButton.disabled = false;
            input.focus();
            chat.scrollTop = chat.scrollHeight;
          }
        }

        sendButton.addEventListener("click", sendMessage);

        input.addEventListener("keydown", event => {
          if (event.key === "Enter") {
            event.preventDefault();
            sendMessage();
          }
        });

        clearButton.addEventListener("click", () => {
          if (busy) return;
          history = [];
          chat.replaceChildren();
          status.textContent = "Conversa limpa.";
        });

        status.textContent = "Pronto. Envie uma mensagem para começar.";
      </script>
    </body>
    </html>
    """

    # Insere o prompt padrão de forma segura como string JavaScript.
    html_chat = html_chat.replace(
        "__PROMPT__",
        json.dumps(PROMPT_PADRAO, ensure_ascii=False),
    )

    components.html(
        html_chat,
        height=530,
        scrolling=False,
    )

    st.caption(
        "O histórico do modo ADM fica dentro do componente do navegador "
        "e não é compartilhado com o histórico Python do modo Normal."
    )

# =========================================================
# MODO NORMAL: mantém a integração existente com a Groq
# =========================================================
else:
    try:
        chave_api = st.secrets["GROQ_API_KEY"]
        cliente = Groq(api_key=chave_api)
    except KeyError:
        st.error(
            "Configure GROQ_API_KEY em "
            "Streamlit → Settings → Secrets."
        )
        st.stop()
    except Exception as erro:
        st.error("Não foi possível inicializar a conexão com a Groq.")
        st.code(
            f"{type(erro).__name__}: {str(erro)[:500]}",
            language="text",
        )
        st.stop()

    for mensagem in st.session_state.mensagens:
        with st.chat_message(mensagem["role"]):
            st.markdown(mensagem["content"])

    pergunta = st.chat_input("Digite sua mensagem...")

    if pergunta and pergunta.strip():
        texto_usuario = pergunta.strip()

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
                    model=MODELO_NORMAL,
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

                st.session_state.mensagens.append({
                    "role": "assistant",
                    "content": texto_resposta,
                })

            except Exception as erro:
                status_code = getattr(erro, "status_code", None)

                detalhe = str(erro)
                detalhe = detalhe.replace(
                    str(chave_api), "[CHAVE OCULTA]"
                ) if chave_api else detalhe
                detalhe = detalhe[:700] or "Sem detalhes disponíveis."

                if status_code == 401:
                    orientacao = (
                        "A Groq recusou a autenticação. Confira "
                        "GROQ_API_KEY nos Secrets."
                    )
                elif status_code == 403:
                    orientacao = (
                        "Sua conta não tem permissão para usar este modelo."
                    )
                elif status_code == 404:
                    orientacao = (
                        f"Modelo não encontrado: {MODELO_NORMAL}."
                    )
                elif status_code == 429:
                    orientacao = (
                        "Limite de uso da Groq atingido. Tente mais tarde."
                    )
                elif status_code is not None and status_code >= 500:
                    orientacao = "A Groq apresentou um erro no servidor."
                elif type(erro).__name__ in (
                    "APIConnectionError", "APITimeoutError"
                ):
                    orientacao = "Não foi possível conectar à Groq."
                else:
                    orientacao = "Não foi possível obter uma resposta da Groq."

                area_resposta.error(orientacao)
                st.code(
                    f"Erro: {type(erro).__name__}"
                    + (
                        f" | HTTP {status_code}"
                        if status_code else ""
                    )
                    + f"\n{detalhe}",
                    language="text",
                )

    if st.session_state.mensagens:
        if st.button("Limpar conversa", use_container_width=True):
            st.session_state.mensagens = []
            st.rerun()
