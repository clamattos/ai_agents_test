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

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1f4e79, #2d5a87);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 4px solid #1f4e79;
    }
    .user-message {
        background-color: #e3f2fd;
        margin-left: 2rem;
    }
    .assistant-message {
        background-color: #f5f5f5;
        margin-right: 2rem;
    }
    .success-message {
        background-color: #e8f5e8;
        border-left-color: #4caf50;
    }
    .error-message {
        background-color: #ffebee;
        border-left-color: #f44336;
    }
    .info-box {
        background-color: #f0f8ff;
        border: 1px solid #1f4e79;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
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
        """Processa a mensagem do usuário e retorna a resposta do assistente"""
        user_message_lower = user_message.lower()
        
        # Verificar se já temos dados confirmados
        if st.session_state.get('current_step') == 'data_confirmed':
            if any(word in user_message_lower for word in ['sim', 'gerar', 'dae', 'guia', 'pagamento']):
                return self._generate_dae_guide()
            elif any(word in user_message_lower for word in ['não', 'alterar', 'mudar']):
                return "Entendi. Para alterar os dados, use o formulário ao lado ou me informe os novos dados."
            else:
                return "Deseja gerar a guia DAE para pagamento ou alterar algum dado?"
        
        # Verificar se a mensagem contém dados do usuário primeiro
        if self._extract_user_data(user_message):
            return self._process_user_data(user_message)
        
        # Detectar intenção apenas se não contém dados
        if any(word in user_message_lower for word in ['segunda via', 'emitir', 'cnh', 'ppd', 'acc']):
            return self._handle_second_copy_request(user_message)
        elif any(word in user_message_lower for word in ['status', 'consulta', 'situação', 'andamento']):
            return self._handle_status_request(user_message)
        else:
            return self._handle_general_request(user_message)
    
    def _handle_second_copy_request(self, message: str) -> str:
        # Se não contém dados, pedir as informações
        return """Claro! Para emissão do documento, preciso de algumas informações:
        
**Por favor, me informe:**
- Nome completo
- CPF (11 dígitos, apenas números)
- Data de nascimento (formato DD/MM/AAAA)
- Nome da mãe

Pode me informar esses dados?"""
    
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
        """Gera a guia DAE para pagamento"""
        if not st.session_state.get('user_data'):
            return "❌ Erro: Dados do usuário não encontrados. Por favor, forneça os dados novamente."
        
        # Usar dados já confirmados
        user_data = st.session_state.user_data['retornoNSDGXS02']
        
        # Preparar payload para gerar guia
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
            return f"""✅ Guia DAE gerada com sucesso!

**Dados da Guia:**
- **Valor:** R$ {data['valor_taxa']}
- **Vencimento:** {data['data_vencimento']}
- **Linha Digitável:** {data['linha_digitavel']}
- **Código de Barras:** {data['codigo_barras']}
- **Nosso Número:** {data['nosso_numero']}

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
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("💬 Chat com o Assistente")
        
        # Exibir histórico de mensagens
        for message in st.session_state.messages:
            with st.container():
                if message["role"] == "user":
                    st.markdown(f"""
                    <div class="chat-message user-message">
                        <strong>Você:</strong> {message["content"]}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="chat-message assistant-message">
                        <strong>Assistente:</strong> {message["content"]}
                    </div>
                    """, unsafe_allow_html=True)
        
        # Input para nova mensagem
        col_input, col_clear = st.columns([3, 1])
        
        with col_input:
            user_input = st.text_input("Digite sua mensagem:", key="user_input", placeholder="Ex: Preciso emitir a segunda via da minha CNH")
        
        with col_clear:
            if st.button("🗑️ Limpar Chat"):
                st.session_state.messages = []
                st.session_state.user_data = {}
                st.session_state.current_step = 'welcome'
                st.rerun()
        
        if st.button("Enviar") and user_input:
            # Adicionar mensagem do usuário
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # Processar com o agente imediatamente
            response = st.session_state.agent.process_message(user_input)
            
            # Adicionar resposta do assistente
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            # Limpar input e recarregar
            st.rerun()
    
    with col2:
        st.subheader("📋 Formulários")
        
        # Formulário para segunda via
        with st.expander("🚗 Solicitar Segunda Via", expanded=True):
            with st.form("segunda_via_form"):
                nome = st.text_input("Nome completo")
                cpf = st.text_input("CPF (11 dígitos)", max_chars=11)
                data_nascimento = st.text_input("Data de nascimento (DD/MM/AAAA)")
                nome_mae = st.text_input("Nome da mãe")
                
                if st.form_submit_button("Confirmar Dados"):
                    if nome and cpf and data_nascimento and nome_mae:
                        payload = {
                            "cpf": cpf,
                            "nome_condutor": nome,
                            "data_nascimento": data_nascimento,
                            "nome_mae": nome_mae
                        }
                        
                        result = st.session_state.agent.backend.confirmar_dados(payload)
                        
                        if result.get("status") == 200:
                            st.session_state.user_data = result["data"]
                            st.success("✅ Dados confirmados com sucesso!")
                            
                            # Exibir dados retornados
                            st.json(result["data"])
                            
                            # Botão para gerar guia
                            if st.button("Gerar Guia DAE"):
                                guia_payload = {
                                    **payload,
                                    "flow_id": result["data"]["flow_id"],
                                    "codigo_municipio_condutor": result["data"]["retornoNSDGXS02"]["codigo_municipio_condutor"],
                                    "ddd_celular": result["data"]["retornoNSDGXS02"]["ddd_celular"],
                                    "numero_celular": result["data"]["retornoNSDGXS02"]["numero_celular"],
                                    "email": result["data"]["retornoNSDGXS02"]["email"],
                                    "codigo_taxa": result["data"]["retornoNSDGXS02"]["codigo_taxa"],
                                    "codigo_servico": result["data"]["retornoNSDGXS02"]["codigo_servico"],
                                    "numero_cnh": result["data"]["retornoNSDGXS02"]["numero_cnh"],
                                    "numero_ip_micro": "192.168.1.1"
                                }
                                
                                guia_result = st.session_state.agent.backend.exibir_opcoes_pagamento(guia_payload)
                                
                                if guia_result.get("status") == 200:
                                    st.success("✅ Guia DAE gerada com sucesso!")
                                    st.json(guia_result["data"])
                                    
                                    # Exibir código de barras se disponível
                                    if guia_result["data"].get("codigoBarras"):
                                        try:
                                            # Decodificar base64 e exibir como imagem
                                            barcode_data = base64.b64decode(guia_result["data"]["codigoBarras"])
                                            st.image(barcode_data, caption="Código de Barras DAE")
                                        except:
                                            st.info("Código de barras disponível (formato base64)")
                        else:
                            st.error(f"❌ Erro: {result.get('error', 'Erro desconhecido')}")
                    else:
                        st.warning("⚠️ Preencha todos os campos obrigatórios")
        
        # Formulário para consulta de status
        with st.expander("📊 Consultar Status"):
            with st.form("status_form"):
                cpf_status = st.text_input("CPF (11 dígitos)", key="cpf_status", max_chars=11)
                data_nascimento_status = st.text_input("Data de nascimento (DD/MM/AAAA)", key="data_nascimento_status")
                
                if st.form_submit_button("Consultar Status"):
                    if cpf_status and data_nascimento_status:
                        payload = {
                            "cpf": cpf_status,
                            "data_nascimento": data_nascimento_status
                        }
                        
                        result = st.session_state.agent.backend.exibir_dados(payload)
                        
                        if result.get("status") == 200:
                            st.success("✅ Status consultado com sucesso!")
                            st.json(result["data"])
                        else:
                            st.error(f"❌ Erro: {result.get('error', 'Erro desconhecido')}")
                    else:
                        st.warning("⚠️ Preencha todos os campos obrigatórios")
        
        # Informações adicionais
        st.markdown("""
        <div class="info-box">
            <h4>ℹ️ Informações Importantes</h4>
            <ul>
                <li>Este é um sistema de demonstração</li>
                <li>Os dados são fictícios para fins de teste</li>
                <li>Em produção, conectaria com APIs reais do CET-MG</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
