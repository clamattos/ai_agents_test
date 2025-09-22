import os
import uuid
import boto3
import streamlit as st

# =========================
# Configuração básica
# =========================
st.set_page_config(page_title="Chat – Bedrock Agent", page_icon="💬", layout="wide")

# Lê configurações de ambiente/Secrets (recomendado no Streamlit Cloud)
AWS_REGION = st.secrets.get("AWS_REGION") or os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION", "us-east-1")
AGENT_ID = st.secrets.get("BEDROCK_AGENT_ID") or os.getenv("BEDROCK_AGENT_ID", "")
AGENT_ALIAS_ID = st.secrets.get("BEDROCK_AGENT_ALIAS_ID") or os.getenv("BEDROCK_AGENT_ALIAS_ID", "")

# =========================
# Cliente Bedrock Agent Runtime
# =========================
@st.cache_resource(show_spinner=False)
def get_bedrock_agent_runtime():
    try:
        client = boto3.client("bedrock-agent-runtime", region_name=AWS_REGION)
        return client
    except Exception as e:
        st.error(f"Falha ao inicializar o cliente Bedrock Agent Runtime: {e}")
        st.stop()

client = get_bedrock_agent_runtime()

# =========================
# Funções utilitárias
# =========================

def ensure_session():
    """Garante um session_id estável por sessão de navegador e histórico de chat."""
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if "messages" not in st.session_state:
        st.session_state.messages = []  # [{"role": "user|assistant", "content": str}]


def reset_session():
    """Apaga a sessão atual e inicia uma nova (até o usuário recarregar a página)."""
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.messages = []


def stream_agent_response(user_text: str):
    """Invoca o Agent e faz streaming do texto de resposta.
    A interface APENAS conversa com o Agent (sem chamar outras APIs diretamente).
    """
    if not AGENT_ID or not AGENT_ALIAS_ID:
        st.error("Defina BEDROCK_AGENT_ID e BEDROCK_AGENT_ALIAS_ID em st.secrets ou variáveis de ambiente.")
        return ""

    try:
        response = client.invoke_agent(
            agentId=AGENT_ID,
            agentAliasId=AGENT_ALIAS_ID,
            sessionId=st.session_state.session_id,
            inputText=user_text,
        )

        full_text = ""
        for event in response.get("completion", []):
            if "chunk" in event:
                part = event["chunk"].get("bytes", b"").decode("utf-8", errors="ignore")
                full_text += part
                yield part
        return full_text

    except client.exceptions.ThrottlingException:
        msg = "O serviço está ocupado (Throttling). Tente novamente em alguns segundos."
        st.warning(msg)
        yield "\n" + msg
    except Exception as e:
        err = f"Erro ao invocar o Agent: {e}"
        st.error(err)
        yield "\n" + err

# =========================
# UI – Sidebar (informativo)
# =========================
with st.sidebar:
    st.header("Sobre o sistema")
    st.write("""
        Lorem ipsum dolor sit amet, consectetur adipiscing elit. Praesent commodo
        suscipit lorem, sit amet egestas purus vulputate eget. Integer quis nisl
        a erat facilisis tempus.
        """)

    st.header("Como usar")
    st.write("""
        Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam vitae
        feugiat turpis. Sed posuere, dolor et faucibus pharetra, diam nisl
        rhoncus odio, eu lacinia lorem odio non odio.
        """)

    st.header("Atalhos rápidos")
    st.write("""
        • Lorem ipsum dolor sit amet.\n
        • Consectetur adipiscing elit.\n
        • Integer quis nisl a erat.\n
        • Sed posuere dolor et faucibus.
        """)

# =========================
# UI – Área principal (chat estilo ChatGPT)
# =========================
ensure_session()
st.title("💬 Chat com Bedrock Agent")

# Renderiza histórico
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"]) 

# Controles rápidos (fica logo acima da barra de pergunta)
cc1, cc2 = st.columns([0.8, 0.2])
with cc2:
    if st.button("🧹 Resetar sessão", help="Apaga o histórico e cria uma nova sessão de chat"):
        reset_session()
        st.toast("Sessão reiniciada.")
        try:
            st.rerun()
        except Exception:
            st.experimental_rerun()

# Entrada do usuário
prompt = st.chat_input("Escreva sua mensagem…")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        streamed_text = ""
        for chunk in stream_agent_response(prompt):
            streamed_text += chunk
            placeholder.markdown(streamed_text)
        if not streamed_text:
            placeholder.markdown("(sem conteúdo)")

    if streamed_text:
        st.session_state.messages.append({"role": "assistant", "content": streamed_text})

# Rodapé simples
st.caption("Esta interface APENAS conversa com o Bedrock Agent configurado.")
