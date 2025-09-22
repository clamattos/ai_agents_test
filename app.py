import streamlit as st
import json
import re
import base64
import io
from datetime import datetime
import boto3
from typing import Dict, Any, Optional
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    
    /* Header principal */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    /* Container do chat */
    .chat-container {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
        min-height: 500px;
        max-height: 70vh;
        overflow-y: auto;
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
    
    /* Input area */
    .chat-input {
        background: white;
        border-radius: 15px;
        padding: 1rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        border: 1px solid #e0e0e0;
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
    
    /* Scrollbar personalizada */
    .chat-container::-webkit-scrollbar {
        width: 6px;
    }
    
    .chat-container::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 3px;
    }
    
    .chat-container::-webkit-scrollbar-thumb {
        background: #c1c1c1;
        border-radius: 3px;
    }
    
    .chat-container::-webkit-scrollbar-thumb:hover {
        background: #a8a8a8;
    }
    
    /* Animações */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .chat-message {
        animation: fadeIn 0.3s ease-out;
    }
    
    /* Typing indicator */
    .typing-indicator {
        display: flex;
        align-items: center;
        padding: 1rem 1.5rem;
        background: #f1f3f4;
        border-radius: 18px 18px 18px 4px;
        margin: 1rem 3rem 1rem 0;
        border: 1px solid #e0e0e0;
    }
    
    .typing-dots {
        display: flex;
        gap: 4px;
    }
    
    .typing-dot {
        width: 8px;
        height: 8px;
        background: #999;
        border-radius: 50%;
        animation: typing 1.4s infinite ease-in-out;
    }
    
    .typing-dot:nth-child(1) { animation-delay: -0.32s; }
    .typing-dot:nth-child(2) { animation-delay: -0.16s; }
    
    @keyframes typing {
        0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
        40% { transform: scale(1); opacity: 1; }
    }
</style>
""", unsafe_allow_html=True)

# Inicialização do estado da sessão
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'user_data' not in st.session_state:
    st.session_state.user_data = {}
if 'current_step' not in st.session_state:
    st.session_state.current_step = 'welcome'
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'quick_actions' not in st.session_state:
    st.session_state.quick_actions = [
        "Quero emitir a segunda via da minha CNH",
        "Qual o status da minha solicitação?",
        "Preciso de ajuda com PPD",
        "Como consultar minha CNH?"
    ]

# Classe para gerenciar o backend (adaptada do lambda)
class CETBackend:
    def __init__(self):
        self.cpf_re = re.compile(r"^\d{11}$")
        self.date_re = re.compile(r"^\d{2}/\d{2}/\d{4}$")
    
    def _require(self, payload, field, pattern: re.Pattern = None, fmt_desc: str = ""):
        v = payload.get(field)
        if v is None or (isinstance(v, str) and not v.strip()):
            raise ValueError(f'O campo "{field}" é obrigatório')
        if pattern and isinstance(v, str) and not pattern.match(v):
            raise ValueError(f'Campo "{field}" inválido. {fmt_desc}'.strip())
        return v
    
    def _validate_confirmar(self, payload):
        self._require(payload, "cpf", self.cpf_re, "Use 11 dígitos numéricos")
        self._require(payload, "nome_condutor")
        self._require(payload, "data_nascimento", self.date_re, "Formato DD/MM/AAAA")
        self._require(payload, "nome_mae")
    
    def _validate_emitir_guia(self, payload):
        if not payload.get("flow_id"):
            self._require(payload, "cpf", self.cpf_re, "Use 11 dígitos numéricos")
            self._require(payload, "nome_condutor")
            self._require(payload, "data_nascimento", self.date_re, "Formato DD/MM/AAAA")
            self._require(payload, "nome_mae")
            self._require(payload, "codigo_taxa")
            self._require(payload, "codigo_servico")
            self._require(payload, "numero_cnh")
        self._require(payload, "codigo_municipio_condutor")
        self._require(payload, "ddd_celular")
        self._require(payload, "numero_celular")
        self._require(payload, "email")
        self._require(payload, "numero_ip_micro")
    
    def _validate_exibir_dados(self, payload):
        self._require(payload, "cpf", self.cpf_re, "Use 11 dígitos numéricos")
        self._require(payload, "data_nascimento", self.date_re, "Formato DD/MM/AAAA")
    
    def confirmar_dados(self, payload: dict):
        try:
            self._validate_confirmar(payload)
        except ValueError as e:
            return {"error": str(e), "status": 422}
        
        cpf = payload.get("cpf")
        return {
            "status": 200,
            "data": {
                "flow_id": "0a84e30c-3c9c-4f1c-9a5c-5d9a3b2d7f1a",
                "retornoNSDGXS02": {
                    "codigo_retorno": 0,
                    "mensagem_retorno": "OK",
                    "cpf": cpf,
                    "numero_cnh": "12345678900",
                    "numero_pgu": "99887766",
                    "numero_identidade": "MG1234567",
                    "orgao_expedidor_identidade": "SSP",
                    "uf_identidade": "MG",
                    "endereco_condutor": "Av. Afonso Pena",
                    "numero_endereco_condutor": "1000",
                    "complemento_endereco_condutor": "Sala 101",
                    "bairro_endereco_condutor": "Centro",
                    "codigo_municipio_condutor": 4123,
                    "nome_municipio_condutor": "BELO HORIZONTE",
                    "sigla_uf_municipio_condutor": "MG",
                    "numero_cep_endereco_condutor": "30130008",
                    "data_primeira_habilitacao": "2010-06-15",
                    "data_validade_exame": "2027-05-23",
                    "codigo_servico": 123,
                    "codigo_taxa": 25,
                    "flag_escolhe_entrega": 1,
                    "flag_tipo_autorizacao": "CNH",
                    "ddd_celular": 31,
                    "numero_celular": 999999999,
                    "email": "condutor@example.com"
                }
            }
        }
    
    def exibir_opcoes_pagamento(self, payload: dict):
        try:
            self._validate_emitir_guia(payload)
        except ValueError as e:
            return {"error": str(e), "status": 422}
        
        cpf = payload.get("cpf", "00000000000")
        return {
            "status": 200,
            "data": {
                "retornoNsdgxS2A": {"codigo_retorno": 0, "mensagem_retorno": "OK"},
                "retornoNsdgx414": {
                    "codigo_erro": 0,
                    "mensagem_erro": "",
                    "codigo_tipo_contribuinte": "04",
                    "codigo_municipio_ibge": "062",
                    "descricao_municipio": "BELO HORIZONTE",
                    "mes_ano_dae": "12/2024",
                    "data_vencimento": "31/12/2024",
                    "linha_digitavel": "85610000001 2 26710213241 7 23112252400 3 02194270789 0",
                    "codigo_barras": "856100000012267102132417231122524003021942707890",
                    "nosso_numero": "2524000219427",
                    "nome_contribuinte": "CONDUTOR TESTE",
                    "valor_taxa": "126,71",
                    "quantidade_taxa": 1,
                    "data_emissao": "20/12/2024",
                    "cpf_contribuinte": cpf,
                    "numero_identificao_contribuinte": "12345678900",
                    "sigla_uf_origem_contribuinte": "MG",
                    "campo_mensagem_1": "EXPEDICAO DA 2a VIA DA HABILITACAO",
                    "campo_mensagem_2": "NUM. CNH: 12345678900",
                    "campo_mensagem_3": "Solicitação Segunda Via de CNH / PPD",
                    "campo_mensagem_4": "",
                    "campo_mensagem_5": "- A segunda via da CNH sera emitida apos a confirmacao de pagamento",
                    "campo_mensagem_6": "do DAE e enviada para o endereco do condutor atraves do correio.",
                    "campo_mensagem_7": "Acompanhe a sua solicitacao atraves do site www.detran.mg.gov.br",
                    "campo_mensagem_8": "",
                    "campo_mensagem_9": "",
                    "campo_mensagem_10": "",
                    "campo_mensagem_11": "",
                    "campo_mensagem_12": "",
                    "campo_mensagem_13": "Sr. Caixa,",
                    "campo_mensagem_14": "Este documento deve ser recebido exclusivamente pela",
                    "campo_mensagem_15": "leitura do codigo de barra ou linha digitavel",
                    "campo_mensagem_16": "",
                    "campo_mensagem_17": "Data Emissao: 20/12/2024",
                    "campo_mensagem_18": "",
                    "codigo_taxa": 25,
                    "codigo_municipio": "4123"
                },
                "codigoBarras": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAAB..."
            }
        }
    
    def exibir_dados(self, payload: dict):
        try:
            self._validate_exibir_dados(payload)
        except ValueError as e:
            return {"error": str(e), "status": 422}
        
        cpf = payload.get("cpf")
        return {
            "status": 200,
            "data": {
                "cpf": cpf,
                "numero_renach": "MG-123456789",
                "nome_condutor": "CONDUTOR TESTE",
                "numero_formulario_renach": "FORM-0001",
                "codigo_etapa": 4,
                "descricao_etapa": "Emissão concluída",
                "prazo": 0,
                "titulo_entrega": "Postado nos Correios",
                "data_entrega_lote": "2025-09-18",
                "titulo_hora_entrega": "Até 18h",
                "hora_entrega_lote": "18:00:00",
                "data_hora_status": "2025-09-18T12:10:00Z",
                "texto_ar_correio": "AR: 123456789BR",
                "numero_ar_correio": "123456789BR",
                "data_ar_correio": "2025-09-18",
                "situacao_cnh": "Emitida",
                "descricao_situacao_entrega": "Em trânsito",
                "codigo_retorno_binco": 0,
                "descricao_retorno_binco": "Sem restrições",
                "data_retorno_binco": "2024-12-19",
                "descricao_situacao_cnh": "Regular",
                "texto_livre_rejeicao": "",
                "titulo_motivo_devolucao": "",
                "titulo_motivo_baixa": "",
                "titulo_motivo_rejeicao": "",
                "quantidade_motivo_rejeicao": 0,
                "codigo_rejeicao": [],
                "motivo_rejeicao": [],
                "descricao_acao": "Acompanhar entrega pelo AR"
            }
        }

# Classe para simular o Bedrock Agent
class BedrockAgent:
    def __init__(self):
        self.backend = CETBackend()
        self.system_prompt = self._load_system_prompt()
    
    def _load_system_prompt(self):
        try:
            with open('system_prompt_agent.txt', 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return """
            Você é um assistente de emissão e consulta de segunda via de CNH do CET - Minas Gerais.
            Responda sempre em português do Brasil com tom claro e profissional.
            """
    
    def process_message(self, user_message: str) -> str:
        """Processa a mensagem do usuário seguindo o system prompt"""
        user_message_lower = user_message.lower()
        
        # Seguir o fluxo do system prompt
        if st.session_state.get('current_step') == 'collecting_data':
            return self._handle_data_collection(user_message)
        elif st.session_state.get('current_step') == 'confirming_data':
            return self._handle_data_confirmation(user_message)
        elif st.session_state.get('current_step') == 'generating_dae':
            return self._handle_dae_generation(user_message)
        else:
            return self._handle_initial_request(user_message)
    
    def _handle_initial_request(self, message: str) -> str:
        """Handle initial user request following system prompt"""
        user_message_lower = message.lower()
        
        # Detectar intenção conforme system prompt
        if any(word in user_message_lower for word in ['segunda via', 'emitir', 'cnh', 'ppd', 'acc']):
            st.session_state.current_step = 'collecting_data'
            return """Claro! Para emissão do documento, preciso de algumas informações:

**Por favor, me informe:**
- Nome completo
- CPF (11 dígitos, apenas números)
- Data de nascimento (formato DD/MM/AAAA)
- Nome da mãe

Pode me informar esses dados?"""
        elif any(word in user_message_lower for word in ['status', 'consulta', 'situação', 'andamento']):
            return """Para consultar o status da sua solicitação, preciso de:
            
- CPF (11 dígitos)
- Data de nascimento (formato DD/MM/AAAA)

Use o formulário de consulta ao lado para verificar o status."""
        else:
            return self._handle_general_request(message)
    
    def _handle_data_collection(self, message: str) -> str:
        """Handle data collection phase following system prompt"""
        # Verificar se a mensagem contém dados do usuário
        if self._extract_user_data(message):
            # Extrair dados conforme system prompt
            user_data = self._extract_user_data_from_message(message)
            if user_data:
                # Confirmar dados conforme system prompt
                st.session_state.current_step = 'confirming_data'
                st.session_state.temp_user_data = user_data
                return f"""Vou seguir com a solicitação de 2ª via para: 
CPF {user_data['cpf']}, Nome {user_data['nome_condutor']}, Nascimento {user_data['data_nascimento']}, Mãe {user_data['nome_mae']}. 

Confirmar?"""
            else:
                return "❌ Não consegui identificar todos os dados necessários. Pode me informar novamente?"
        else:
            return "Por favor, me informe os dados necessários: nome completo, CPF (11 dígitos), data de nascimento (DD/MM/AAAA) e nome da mãe."
    
    def _handle_data_confirmation(self, message: str) -> str:
        """Handle data confirmation phase following system prompt"""
        user_message_lower = message.lower()
        
        if any(word in user_message_lower for word in ['sim', 'confirmar', 'ok', 'certo']):
            # Chamar confirmar-dados conforme system prompt
            user_data = st.session_state.temp_user_data
            result = self.backend.confirmar_dados(user_data)
            
            if result.get("status") == 200:
                st.session_state.user_data = result["data"]
                st.session_state.current_step = 'data_confirmed'
                
                # Apresentar todos os dados conforme system prompt
                data = result["data"]["retornoNSDGXS02"]
                return f"""✅ Dados confirmados com sucesso!

**Seus dados cadastrados:**
- CPF: {data['cpf']}
- Nome: {data.get('nome_condutor', 'N/A')}
- CNH: {data['numero_cnh']}
- Endereço: {data['endereco_condutor']}, {data['numero_endereco_condutor']}
- Município: {data['nome_municipio_condutor']}/{data['sigla_uf_municipio_condutor']}
- Telefone: ({data['ddd_celular']}) {data['numero_celular']}
- Email: {data['email']}

Deseja alterar algum dado? Se sim: "Vou te repassar para nosso agente de alteração de dados." Se não: "Vou gerar a guia (DAE) para pagamento." """
            else:
                return f"❌ Erro na validação: {result.get('error', 'Erro desconhecido')}"
        else:
            return "Dados não confirmados. Deseja alterar algum dado ou confirmar novamente?"
    
    def _handle_dae_generation(self, message: str) -> str:
        """Handle DAE generation phase following system prompt"""
        user_message_lower = message.lower()
        
        if any(word in user_message_lower for word in ['sim', 'gerar', 'dae', 'guia', 'pagamento']):
            # Chamar exibir-opcoes-pagamento conforme system prompt
            return self._generate_dae_guide()
        else:
            return "Deseja gerar a guia DAE para pagamento?"
    
    def _extract_user_data(self, message: str) -> bool:
        """Verifica se a mensagem contém dados do usuário"""
        # Procurar por padrões que indicam dados do usuário
        import re
        
        # Verificar se tem CPF (11 dígitos)
        cpf_pattern = r'\b\d{11}\b'
        if re.search(cpf_pattern, message):
            return True
        
        # Verificar se tem data (DD/MM/AAAA)
        date_pattern = r'\b\d{2}/\d{2}/\d{4}\b'
        if re.search(date_pattern, message):
            return True
            
        return False
    
    def _extract_user_data_from_message(self, message: str) -> dict:
        """Extrai dados do usuário da mensagem"""
        import re
        
        # Extrair dados da mensagem
        cpf_match = re.search(r'\b(\d{11})\b', message)
        date_match = re.search(r'\b(\d{2}/\d{2}/\d{4})\b', message)
        
        if cpf_match and date_match:
            cpf = cpf_match.group(1)
            data_nascimento = date_match.group(1)
            
            # Tentar extrair nome e nome da mãe
            words = message.split()
            # Remover CPF e data da lista de palavras
            words = [w for w in words if not re.match(r'\d{11}', w) and not re.match(r'\d{2}/\d{2}/\d{4}', w)]
            
            if len(words) >= 2:
                nome = words[0]
                nome_mae = words[-1]
                
                return {
                    "cpf": cpf,
                    "nome_condutor": nome,
                    "data_nascimento": data_nascimento,
                    "nome_mae": nome_mae
                }
        
        return None
    
    def _process_user_data(self, message: str) -> str:
        """Processa os dados fornecidos pelo usuário"""
        import re
        
        # Extrair dados da mensagem
        cpf_match = re.search(r'\b(\d{11})\b', message)
        date_match = re.search(r'\b(\d{2}/\d{2}/\d{4})\b', message)
        
        if cpf_match and date_match:
            cpf = cpf_match.group(1)
            data_nascimento = date_match.group(1)
            
            # Tentar extrair nome e nome da mãe (assumindo que são as primeiras e últimas palavras)
            words = message.split()
            # Remover CPF e data da lista de palavras
            words = [w for w in words if not re.match(r'\d{11}', w) and not re.match(r'\d{2}/\d{2}/\d{4}', w)]
            
            if len(words) >= 2:
                nome = words[0]
                nome_mae = words[-1]
                
                # Processar com o backend
                payload = {
                    "cpf": cpf,
                    "nome_condutor": nome,
                    "data_nascimento": data_nascimento,
                    "nome_mae": nome_mae
                }
                
                result = self.backend.confirmar_dados(payload)
                
                if result.get("status") == 200:
                    st.session_state.user_data = result["data"]
                    st.session_state.current_step = 'data_confirmed'
                    return f"""✅ Dados confirmados com sucesso!

**Seus dados cadastrados:**
- CPF: {cpf}
- Nome: {nome}
- Data de nascimento: {data_nascimento}
- Nome da mãe: {nome_mae}

**Dados do sistema:**
- CNH: {result['data']['retornoNSDGXS02']['numero_cnh']}
- Endereço: {result['data']['retornoNSDGXS02']['endereco_condutor']}, {result['data']['retornoNSDGXS02']['numero_endereco_condutor']}
- Município: {result['data']['retornoNSDGXS02']['nome_municipio_condutor']}/{result['data']['retornoNSDGXS02']['sigla_uf_municipio_condutor']}
- Telefone: ({result['data']['retornoNSDGXS02']['ddd_celular']}) {result['data']['retornoNSDGXS02']['numero_celular']}
- Email: {result['data']['retornoNSDGXS02']['email']}

Deseja alterar algum dado ou posso gerar a guia DAE para pagamento?"""
                else:
                    return f"❌ Erro na validação: {result.get('error', 'Erro desconhecido')}"
            else:
                return "❌ Não consegui identificar o nome e nome da mãe. Pode me informar novamente?"
        else:
            return "❌ Não consegui identificar o CPF e data de nascimento. Pode me informar novamente?"
    
    def _handle_status_request(self, message: str) -> str:
        return """Para consultar o status da sua solicitação, preciso de:
        
- CPF (11 dígitos)
- Data de nascimento (formato DD/MM/AAAA)

Use o formulário de consulta ao lado para verificar o status."""
    
    def _handle_general_request(self, message: str) -> str:
        return """Olá! Sou o assistente do CET-MG. Posso ajudá-lo com:

🚗 **Solicitar segunda via** de CNH, PPD ou ACC
📋 **Consultar status** da sua solicitação em andamento

Como posso ajudá-lo hoje?"""
    
    def get_welcome_message(self) -> str:
        """Retorna a mensagem de boas-vindas inicial"""
        return """Olá! Sou o assistente do CET-MG. Posso ajudá-lo com:

🚗 **Solicitar segunda via** de CNH, PPD ou ACC
📋 **Consultar status** da sua solicitação em andamento

Como posso ajudá-lo hoje?"""
    
    def _generate_dae_guide(self) -> str:
        """Gera a guia DAE para pagamento seguindo o system prompt"""
        if not st.session_state.get('user_data'):
            return "❌ Erro: Dados do usuário não encontrados. Por favor, forneça os dados novamente."
        
        # Usar dados já confirmados
        user_data = st.session_state.user_data['retornoNSDGXS02']
        
        # Preparar payload para gerar guia (reaproveitando dados conforme system prompt)
        payload = {
            "flow_id": st.session_state.user_data.get('flow_id'),
            "cpf": user_data['cpf'],
            "nome_condutor": user_data.get('nome_condutor', 'CONDUTOR TESTE'),
            "data_nascimento": "01/01/2000",  # Data padrão para teste
            "nome_mae": "TESTE",
            "codigo_municipio_condutor": user_data['codigo_municipio_condutor'],
            "ddd_celular": user_data['ddd_celular'],
            "numero_celular": user_data['numero_celular'],
            "email": user_data['email'],
            "codigo_taxa": user_data['codigo_taxa'],
            "codigo_servico": user_data['codigo_servico'],
            "numero_cnh": user_data['numero_cnh'],
            "numero_ip_micro": "192.168.1.1"
        }
        
        result = self.backend.exibir_opcoes_pagamento(payload)
        
        if result.get("status") == 200:
            st.session_state.current_step = 'dae_generated'
            data = result['data']['retornoNsdgx414']
            
            # Exibir todos os dados da guia conforme system prompt
            return f"""✅ Guia DAE gerada com sucesso!

**Dados da Guia:**
- **Código de Retorno:** {result['data']['retornoNsdgxS2A']['codigo_retorno']}
- **Mensagem:** {result['data']['retornoNsdgxS2A']['mensagem_retorno']}
- **Valor:** R$ {data['valor_taxa']}
- **Vencimento:** {data['data_vencimento']}
- **Linha Digitável:** {data['linha_digitavel']}
- **Código de Barras:** {data['codigo_barras']}
- **Nosso Número:** {data['nosso_numero']}
- **Nome Contribuinte:** {data['nome_contribuinte']}
- **CPF Contribuinte:** {data['cpf_contribuinte']}
- **Data Emissão:** {data['data_emissao']}
- **Município:** {data['descricao_municipio']}
- **Código Taxa:** {data['codigo_taxa']}

**Instruções:**
- Pague em qualquer banco ou casa lotérica
- Use o código de barras ou linha digitável
- A CNH será enviada para o endereço cadastrado

Obrigado por usar nossos serviços! 🚗"""
        else:
            return f"❌ Erro ao gerar guia: {result.get('error', 'Erro desconhecido')}"

# Interface principal
def main():
    # Cabeçalho
    st.markdown("""
    <div class="main-header">
        <h1>🚗 CET-MG - Assistente CNH</h1>
        <p>Assistente virtual para emissão e consulta de segunda via de CNH, PPD e ACC</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Inicializar o agente
    if 'agent' not in st.session_state:
        st.session_state.agent = BedrockAgent()
    
    # Adicionar mensagem de boas-vindas se não houver mensagens
    if not st.session_state.messages:
        st.session_state.messages.append({
            "role": "assistant", 
            "content": st.session_state.agent.get_welcome_message()
        })
    
    # Layout principal
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Container do chat
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        
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
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Input area
        st.markdown('<div class="chat-input">', unsafe_allow_html=True)
        
        # Input para nova mensagem
        col_input, col_send, col_clear = st.columns([4, 1, 1])
        
        with col_input:
            user_input = st.text_input(
                "Digite sua mensagem:", 
                key="user_input", 
                placeholder="Ex: Preciso emitir a segunda via da minha CNH",
                label_visibility="collapsed"
            )
        
        with col_send:
            send_clicked = st.button("📤", help="Enviar mensagem", key="send_btn")
        
        with col_clear:
            clear_clicked = st.button("🗑️", help="Limpar chat", key="clear_btn")
        
        if clear_clicked:
            st.session_state.messages = []
            st.session_state.user_data = {}
            st.session_state.current_step = 'welcome'
            st.rerun()
        
        if (send_clicked or st.session_state.get('auto_send', False)) and user_input:
            # Adicionar mensagem do usuário
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # Mostrar indicador de digitação
            with st.spinner("Assistente está digitando..."):
                # Processar com o agente
                response = st.session_state.agent.process_message(user_input)
            
            # Adicionar resposta do assistente
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            # Limpar input e recarregar
            st.session_state.auto_send = False
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        # Status da sessão
        if st.session_state.get('user_data'):
            st.markdown("""
            <div class="sidebar-info">
                <h4>✅ Dados Confirmados</h4>
                <p>Seus dados foram validados e estão prontos para emissão da guia DAE.</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Informações sobre o sistema
        st.markdown("""
        <div class="sidebar-info">
            <h4>🚗 Sobre o Sistema</h4>
            <p>Assistente virtual para emissão e consulta de segunda via de CNH, PPD e ACC do CET-MG.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Instruções de uso
        st.markdown("""
        <div class="sidebar-info">
            <h4>📋 Como Usar</h4>
            <ul>
                <li><strong>Solicitar 2ª via:</strong> Digite "quero emitir a segunda via da minha CNH"</li>
                <li><strong>Consultar status:</strong> Digite "qual o status da minha solicitação"</li>
                <li><strong>Fornecer dados:</strong> Informe nome, CPF, data de nascimento e nome da mãe</li>
            </ul>
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
                st.session_state.auto_send = True
                st.session_state.user_input = action
                st.rerun()
        
        # Histórico de conversas
        if len(st.session_state.messages) > 1:
            st.markdown("""
            <div class="sidebar-info">
                <h4>💬 Histórico</h4>
                <p>Conversa ativa com {} mensagens</p>
            </div>
            """.format(len(st.session_state.messages)), unsafe_allow_html=True)
        
        # Informações técnicas
        st.markdown("""
        <div class="sidebar-info">
            <h4>🔧 Sistema de Demonstração</h4>
            <ul>
                <li>Dados são fictícios para fins de teste</li>
                <li>Em produção, conectaria com APIs reais do CET-MG</li>
                <li>Desenvolvido com Streamlit e AWS Bedrock</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
