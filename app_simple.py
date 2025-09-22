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
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if "messages" not in st.session_state:
        st.session_state.messages = []


def reset_session():
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.messages = []


def stream_agent_response(user_text: str):
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


def format_response(raw_text: str) -> str:
    """Formata retorno da emissão de DAE: mostra apenas campos preenchidos, um por linha."""
    if not raw_text:
        return ""
    parts = raw_text.split()
    buffer, linhas = [], []
    for part in parts:
        if ":" in part:
            if buffer:
                linha = " ".join(buffer).strip()
                if not linha.endswith(":"):
                    linhas.append(linha)
                buffer = []
        buffer.append(part)
    if buffer:
        linha = " ".join(buffer).strip()
        if not linha.endswith(":"):
            linhas.append(linha)
    return "\n".join(linhas)

# =========================
# UI – Sidebar
# =========================
def format_dae_response(text: str) -> str:
    """Formata o retorno da emissão da DAE para 'um campo por linha', exibindo apenas campos com valor."""
    if not text:
        return text
    anchor = "Dados da emissão:"
    if anchor in text:
        text = text.split(anchor, 1)[1]
    # Normaliza: troca quebras de linha por espaço e colapsa espaços múltiplos
    t = " ".join(text.replace("\n", " ").split())
    pattern = re.compile(r"([A-Za-z_]+):")
    matches = list(pattern.finditer(t))
    lines = []
    for i, m in enumerate(matches):
        key = m.group(1)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(t)
        value = t[start:end].strip()
        if value:
            lines.append(f"{key}: {value}")
    return "\n".join(lines)

with st.sidebar:
    st.header("Sobre o sistema")
    st.write("Lorem ipsum dolor sit amet, consectetur adipiscing elit...")
    st.header("Como usar")
    st.write("Lorem ipsum dolor sit amet, consectetur adipiscing elit...")
    st.header("Atalhos rápidos")
    st.write("• Lorem ipsum dolor sit amet.\n• Consectetur adipiscing elit.\n• Integer quis nisl a erat.")

# =========================
# UI – Área principal (chat estilo ChatGPT)
# =========================
ensure_session()

st.title("💬 Chat com Bedrock Agent")

col_left, col_right = st.columns([1, 0.2])
with col_right:
    if st.button("🧹 Resetar sessão", key="reset_session_btn_top", help="Apaga o histórico e cria uma nova sessão de chat"):
        reset_session()
        st.toast("Sessão reiniciada.")
        try:
            st.rerun()
        except Exception:
            st.experimental_rerun()

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"]) 

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
        else:
            if streamed_text.strip().startswith("Sua guia DAE foi gerada"):
                formatted = format_dae_response(streamed_text)
                placeholder.markdown(f"```
{formatted}
```")

    if streamed_text:
        # Se a resposta for de emissão de DAE, formata automaticamente
        if streamed_text.strip().startswith("Sua guia DAE foi gerada"):
            formatted = format_response(streamed_text)
            st.session_state.messages.append({"role": "assistant", "content": formatted})
            with st.chat_message("assistant"):
                st.markdown(f"```
{formatted}
```")
        else:
            st.session_state.messages.append({"role": "assistant", "content": streamed_text})

st.caption("Esta interface APENAS conversa com o Bedrock Agent configurado.")
