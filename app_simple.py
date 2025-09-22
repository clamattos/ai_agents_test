import os
import uuid
import boto3
import re
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

    except getattr(client, "exceptions", object()).__dict__.get("ThrottlingException", Exception) as _e:  # robust fallback
        msg = "O serviço está ocupado (Throttling). Tente novamente em alguns segundos."
        st.warning(msg)
        yield "\n" + msg
    except Exception as e:
        err = f"Erro ao invocar o Agent: {e}"
        st.error(err)
        yield "\n" + err

def format_dae_response(text: str) -> str:
    """
    Formata o retorno da emissão da DAE para 'um campo por linha',
    exibindo apenas campos com valor.
    - Remove campos vazios
    - Normaliza espaços
    - Trunca campos muito longos de código de barras
    """
    if not text:
        return text

    anchor = "Dados da emissão:"
    if anchor in text:
        text = text.split(anchor, 1)[1]

    # Normaliza: remove quebras e múltiplos espaços sem usar escapes problemáticos
    t = " ".join(text.split())

    pattern = re.compile(r"([A-Za-z_]+):")
    matches = list(pattern.finditer(t))

    lines = []
    for i, m in enumerate(matches):
        key = m.group(1)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(t)
        value = t[start:end].strip()
        if not value:
            continue
        if key in {"codigo_barras", "codigoBarras"} and len(value) > 60:
            value = value[:60] + "…"
        lines.append(f"{key}: {value}")

    return "\n".join(lines)

# =========================
# UI – Sidebar (informativo)
# =========================
with st.sidebar:
    st.header("Sobre o sistema")
    st.write(
        """
        Lorem ipsum dolor sit amet, consectetur adipiscing elit. Praesent commodo
        suscipit lorem, sit amet egestas purus vulputate eget. Integer quis nisl
        a erat facilisis tempus.
        """
    )

    st.header("Como usar")
    st.write(
        """
        Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam vitae
        feugiat turpis. Sed posuere, dolor et faucibus pharetra, diam nisl
        rhoncus odio, eu lacinia lorem odio non odio.
        """
    )

    st.header("Atalhos rápidos")
    st.write(
        """
        • Lorem ipsum dolor sit amet.

        • Consectetur adipiscing elit.

        • Integer quis nisl a erat.

        • Sed posuere dolor et faucibus.
        """
    )

# =========================
# UI – Área principal (chat estilo ChatGPT)
# =========================
ensure_session()

st.title("💬 Chat com Bedrock Agent")

# Barra superior com botão único de reset (direita)
col_left, col_right = st.columns([1, 0.2])
with col_right:
    if st.button("🧹 Resetar sessão", key="reset_session_btn_top", help="Apaga o histórico e cria uma nova sessão de chat"):
        reset_session()
        st.toast("Sessão reiniciada.")
        try:
            st.rerun()
        except Exception:
            st.experimental_rerun()

# Renderiza histórico
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Entrada do usuário
prompt = st.chat_input("Escreva sua mensagem…")

if prompt:
    # Guarda a mensagem do usuário e mostra
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Espaço para a resposta do agente
    with st.chat_message("assistant"):
        placeholder = st.empty()
        streamed_text = ""
        for chunk in stream_agent_response(prompt):
            streamed_text += chunk
            placeholder.markdown(streamed_text)
        if not streamed_text:
            placeholder.markdown("(sem conteúdo)")
        else:
            # Se for a resposta de emissão de DAE, formata para um campo por linha
            if ("Sua guia DAE foi gerada" in streamed_text) or ("mes_ano_dae:" in streamed_text):
                formatted = format_dae_response(streamed_text)
                # Mostra a frase inicial + os campos
                placeholder.markdown("**Sua guia DAE foi gerada com sucesso. A segunda via da CNH sera emitida apos a confirmacao de pagamento do DAE e enviada para o endereco do condutor atraves do correio. Acompanhe a sua solicitacao perguntando o status aqui. Dados da emissão:**")
                placeholder.code(formatted)
                # Salva no histórico com a frase + campos
                streamed_text = "Sua guia DAE foi gerada com sucesso. A segunda via da CNH sera emitida apos a confirmacao de pagamento do DAE e enviada para o endereco do condutor atraves do correio. Acompanhe a sua solicitacao perguntando o status aqui. Dados da emissão:\n" + formatted

    # Salva a resposta completa no histórico (se houver)
    if streamed_text:
        st.session_state.messages.append({"role": "assistant", "content": streamed_text})

# Rodapé simples
st.caption("Esta interface APENAS conversa com o Bedrock Agent configurado.")
