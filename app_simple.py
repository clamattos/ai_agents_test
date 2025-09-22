import streamlit as st
import os
from datetime import datetime
import boto3
from typing import Dict, Any, Optional
import logging
from dotenv import load_dotenv

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Configuração do Bedrock
BEDROCK_AGENT_ID = os.getenv('BEDROCK_AGENT_ID')
AWS_REGION = os.getenv('AWS_REGION', 'sa-east-1')

# Configuração da página
st.set_page_config(
    page_title="CET-MG - Assistente CNH",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado estilo ChatGPT
st.markdown("""
<style>
    /* Reset e configurações gerais */
    .stApp {
        background-color: #f7f7f8;
    }
    
    /* Mensagens do usuário */
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 18px 18px 4px 18px;
        margin: 1rem 0 1rem 3rem;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
        position: relative;
    }
    
    .user-message::before {
        content: "👤";
        position: absolute;
        left: -2.5rem;
        top: 50%;
        transform: translateY(-50%);
        background: #667eea;
        border-radius: 50%;
        width: 2rem;
        height: 2rem;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.8rem;
    }
    
    /* Mensagens do assistente */
    .assistant-message {
        background: #f1f3f4;
        color: #333;
        padding: 1rem 1.5rem;
        border-radius: 18px 18px 18px 4px;
        margin: 1rem 3rem 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        position: relative;
        border: 1px solid #e0e0e0;
    }
    
    .assistant-message::before {
        content: "🤖";
        position: absolute;
        right: -2.5rem;
        top: 50%;
        transform: translateY(-50%);
        background: #f1f3f4;
        border-radius: 50%;
        width: 2rem;
        height: 2rem;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.8rem;
        border: 1px solid #e0e0e0;
    }
    
    /* Mensagens de sucesso */
    .success-message {
        background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
        color: white;
        border-radius: 18px 18px 18px 4px;
        margin: 1rem 3rem 1rem 0;
    }
    
    /* Mensagens de erro */
    .error-message {
        background: linear-gradient(135deg, #f44336 0%, #d32f2f 100%);
        color: white;
        border-radius: 18px 18px 18px 4px;
        margin: 1rem 3rem 1rem 0;
    }
    
    /* Botões */
    .chat-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
    }
    
    .chat-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    /* Sidebar */
    .sidebar-info {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        border: 1px solid #e0e0e0;
    }
    
    /* Animações */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .user-message, .assistant-message, .success-message, .error-message {
        animation: fadeIn 0.3s ease-out;
    }
    
    /* Scrollbar personalizada */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #c1c1c1;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #a8a8a8;
    }
</style>
""", unsafe_allow_html=True)

# Inicializar session state
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'quick_actions' not in st.session_state:
    st.session_state.quick_actions = [
        "Quero emitir a segunda via da minha CNH",
        "Qual o status da minha solicitação?",
        "Preciso de ajuda com PPD",
        "Como consultar minha CNH?"
    ]

# Classe para chamadas reais do Bedrock Agent
class BedrockAgent:
    def __init__(self):
        self.bedrock_client = self._init_bedrock_client()
    
    def _init_bedrock_client(self):
        """Inicializa o cliente Bedrock"""
        try:
            return boto3.client(
                'bedrock-agent-runtime',
                region_name=AWS_REGION
            )
        except Exception as e:
            logger.error(f"Erro ao inicializar cliente Bedrock: {e}")
            return None
    
    def process_message(self, user_message: str) -> str:
        """Processa a mensagem do usuário usando Bedrock Agent real"""
        if not self.bedrock_client:
            return "❌ Erro: Cliente Bedrock não inicializado. Verifique as configurações."
        
        if not BEDROCK_AGENT_ID:
            return "❌ Erro: ID do Bedrock Agent não configurado. Verifique o arquivo .env."
        
        try:
            # Chamada real para o Bedrock Agent
            response = self.bedrock_client.invoke_agent(
                agentId=BEDROCK_AGENT_ID,
                sessionId=st.session_state.get('session_id', 'default-session'),
                inputText=user_message
            )
            
            # Processar resposta do Bedrock
            return self._process_bedrock_response(response)
            
        except Exception as e:
            logger.error(f"Erro ao chamar Bedrock Agent: {e}")
            return f"❌ Erro ao processar mensagem: {str(e)}"
    
    def _process_bedrock_response(self, response) -> str:
        """Processa a resposta do Bedrock Agent"""
        try:
            # Ler a resposta do Bedrock
            for event in response['completion']:
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        # Decodificar bytes para texto
                        text = chunk['bytes'].decode('utf-8')
                        return text
                elif 'trace' in event:
                    # Processar traces se necessário
                    trace = event['trace']
                    if 'trace' in trace and 'trace' in trace['trace']:
                        # Processar trace específico
                        pass
            
            return "❌ Não foi possível processar a resposta do Bedrock Agent."
            
        except Exception as e:
            logger.error(f"Erro ao processar resposta do Bedrock: {e}")
            return f"❌ Erro ao processar resposta: {str(e)}"
    
    def get_welcome_message(self) -> str:
        """Retorna a mensagem de boas-vindas inicial"""
        return """Olá! Sou o assistente do CET-MG. Posso ajudá-lo com:

🚗 **Solicitar segunda via** de CNH, PPD ou ACC
📋 **Consultar status** da sua solicitação em andamento

Como posso ajudá-lo hoje?"""

# Interface principal
def main():
    # Título principal
    st.title("🚗 CET-MG - Assistente Virtual")
    st.markdown("---")
    
    # Inicializar o agente
    if 'agent' not in st.session_state:
        st.session_state.agent = BedrockAgent()
    
    # Inicializar session_id se não existir
    if 'session_id' not in st.session_state:
        st.session_state.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Adicionar mensagem de boas-vindas se não houver mensagens
    if not st.session_state.messages:
        st.session_state.messages.append({
            "role": "assistant", 
            "content": st.session_state.agent.get_welcome_message()
        })
    
    # Layout principal
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Exibir histórico de mensagens
        for message in st.session_state.messages:
            if message["role"] == "user":
                st.markdown(f"""
                <div class="user-message">
                    {message["content"]}
                </div>
                """, unsafe_allow_html=True)
            else:
                # Detectar tipo de mensagem para aplicar estilo
                message_class = "assistant-message"
                if "✅" in message["content"]:
                    message_class = "success-message"
                elif "❌" in message["content"]:
                    message_class = "error-message"
                
                st.markdown(f"""
                <div class="{message_class}">
                    {message["content"]}
                </div>
                """, unsafe_allow_html=True)
        
        # Input area
        col_input, col_clear = st.columns([5, 1])
        
        with col_input:
            user_input = st.text_input(
                "Digite sua mensagem:", 
                key="user_input", 
                placeholder="Ex: Preciso emitir a segunda via da minha CNH",
                label_visibility="collapsed"
            )
        
        with col_clear:
            clear_clicked = st.button("🗑️", help="Limpar chat", key="clear_btn")
        
        if clear_clicked:
            st.session_state.messages = []
            st.rerun()
        
        # Processar mensagem quando usuário digita e pressiona Enter
        if user_input:
            # Adicionar mensagem do usuário
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # Mostrar indicador de digitação
            with st.spinner("Assistente está digitando..."):
                # Processar com o agente
                response = st.session_state.agent.process_message(user_input)
            
            # Adicionar resposta do assistente
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            # Limpar input e recarregar
            st.rerun()
    
    with col2:
        # Informações sobre o sistema
        st.markdown("""
        <div class="sidebar-info">
            <h4>🚗 Sobre o Sistema</h4>
            <p>Assistente virtual para emissão e consulta de segunda via de CNH, PPD e ACC do CET-MG.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Como usar
        st.markdown("""
        <div class="sidebar-info">
            <h4>📋 Como Usar</h4>
            <p><strong>Solicitar 2ª via:</strong> Digite "quero emitir a segunda via da minha CNH"</p>
            <p><strong>Consultar status:</strong> Digite "qual o status da minha solicitação"</p>
            <p><strong>Fornecer dados:</strong> Informe nome, CPF, data de nascimento e nome da mãe</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Atalhos rápidos
        st.markdown("""
        <div class="sidebar-info">
            <h4>⚡ Atalhos Rápidos</h4>
        </div>
        """, unsafe_allow_html=True)
        
        for i, action in enumerate(st.session_state.quick_actions):
            if st.button(f"💬 {action}", key=f"quick_{i}", help="Clique para enviar esta mensagem"):
                # Adicionar mensagem do usuário
                st.session_state.messages.append({"role": "user", "content": action})
                
                # Processar com o agente
                response = st.session_state.agent.process_message(action)
                
                # Adicionar resposta do assistente
                st.session_state.messages.append({"role": "assistant", "content": response})
                
                # Recarregar
                st.rerun()

if __name__ == "__main__":
    main()
