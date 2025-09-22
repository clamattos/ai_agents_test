# 🚗 CET-MG - Assistente CNH

Sistema de assistente virtual para emissão e consulta de segunda via de CNH, PPD e ACC do CET - Minas Gerais, desenvolvido com Streamlit e integração com AWS Bedrock.

## 🏗️ Arquitetura

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit     │    │   AWS Bedrock    │    │   Lambda        │
│   Frontend      │◄──►│   Agent          │◄──►│   Backend       │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🚀 Deploy no Streamlit Cloud

### Pré-requisitos

1. **Conta no Streamlit Cloud** (gratuita)
2. **Repositório no GitHub** com o código
3. **AWS Account** (para Bedrock Agent - opcional para demo)

### Passo a Passo

#### 1. Preparar o Repositório

```bash
# Clone ou crie um repositório no GitHub
git clone https://github.com/seu-usuario/cet-mg-assistente.git
cd cet-mg-assistente

# Copie os arquivos do projeto
cp /caminho/para/PRODEMGE/* .
```

#### 2. Estrutura de Arquivos

Certifique-se de que seu repositório tenha a seguinte estrutura:

```
cet-mg-assistente/
├── app.py                    # Aplicação principal Streamlit
├── requirements.txt          # Dependências Python
├── system_prompt_agent.txt  # Prompt do agente (opcional)
├── README.md               # Este arquivo
└── .streamlit/             # Configurações do Streamlit (opcional)
    └── config.toml
```

#### 3. Deploy no Streamlit Cloud

1. **Acesse [share.streamlit.io](https://share.streamlit.io)**
2. **Faça login** com sua conta GitHub
3. **Clique em "New app"**
4. **Preencha os campos:**
   - **Repository**: `seu-usuario/cet-mg-assistente`
   - **Branch**: `main` (ou `master`)
   - **Main file path**: `app.py`
   - **App URL**: `cet-mg-assistente` (ou o nome que preferir)

5. **Clique em "Deploy!"**

#### 4. Configuração de Variáveis de Ambiente (Opcional)

Se você quiser conectar com AWS Bedrock real:

1. **No painel do Streamlit Cloud**, vá para **Settings**
2. **Adicione as seguintes variáveis:**
   ```
   AWS_ACCESS_KEY_ID=sua_access_key
   AWS_SECRET_ACCESS_KEY=sua_secret_key
   AWS_DEFAULT_REGION=us-east-1
   BEDROCK_AGENT_ID=seu_agent_id
   ```

### 🔧 Configurações Avançadas

#### Arquivo .streamlit/config.toml (Opcional)

Crie um arquivo `.streamlit/config.toml` para configurações personalizadas:

```toml
[theme]
primaryColor = "#1f4e79"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"

[server]
headless = true
port = 8501
enableCORS = false
enableXsrfProtection = false
```

#### Integração com AWS Bedrock (Opcional)

Para conectar com um Bedrock Agent real, modifique a classe `BedrockAgent` em `app.py`:

```python
import boto3

class BedrockAgent:
    def __init__(self):
        self.bedrock_runtime = boto3.client(
            'bedrock-runtime',
            region_name='us-east-1'
        )
        self.agent_id = os.getenv('BEDROCK_AGENT_ID')
    
    def invoke_agent(self, session_id: str, user_input: str):
        # Implementar chamada real para Bedrock Agent
        pass
```

## 📱 Funcionalidades

### ✅ Implementadas

- **Interface de Chat** interativa
- **Formulários** para coleta de dados
- **Validação** de dados de entrada
- **Simulação** do backend CET-MG
- **Geração** de guias DAE
- **Consulta** de status de solicitações
- **Interface responsiva** e moderna

### 🔄 Fluxos Disponíveis

1. **Solicitar Segunda Via**
   - Coleta de dados do condutor
   - Validação e confirmação
   - Geração de guia DAE
   - Exibição de código de barras

2. **Consultar Status**
   - Busca por CPF e data de nascimento
   - Exibição de status da solicitação
   - Informações de entrega

## 🛠️ Desenvolvimento Local

### Instalação

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/cet-mg-assistente.git
cd cet-mg-assistente

# Instale as dependências
pip install -r requirements.txt

# Execute localmente
streamlit run app.py
```

### Estrutura do Código

- **`app.py`**: Aplicação principal Streamlit
- **`CETBackend`**: Classe que simula o backend Lambda
- **`BedrockAgent`**: Classe que simula o Bedrock Agent
- **Interface**: Chat + Formulários integrados

## 🔒 Segurança

### Para Produção

1. **Configure HTTPS** no Streamlit Cloud
2. **Use variáveis de ambiente** para credenciais
3. **Implemente autenticação** se necessário
4. **Configure CORS** adequadamente
5. **Valide todas as entradas** do usuário

### Variáveis de Ambiente Recomendadas

```bash
# AWS (se usando Bedrock real)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_DEFAULT_REGION=us-east-1
BEDROCK_AGENT_ID=

# Aplicação
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

## 📊 Monitoramento

### Logs do Streamlit Cloud

- Acesse o painel do Streamlit Cloud
- Vá para **Logs** para ver erros e debug
- Configure alertas se necessário

### Métricas Recomendadas

- Número de usuários ativos
- Taxa de sucesso das validações
- Tempo de resposta das APIs
- Erros de validação mais comuns

## 🚨 Troubleshooting

### Problemas Comuns

1. **App não carrega**
   - Verifique se `app.py` está na raiz
   - Confirme se `requirements.txt` está correto
   - Verifique os logs no Streamlit Cloud

2. **Erro de dependências**
   - Atualize `requirements.txt`
   - Verifique versões compatíveis
   - Teste localmente primeiro

3. **Erro de AWS**
   - Verifique as variáveis de ambiente
   - Confirme as credenciais AWS
   - Teste a conectividade

### Comandos de Debug

```bash
# Teste local
streamlit run app.py --logger.level debug

# Verificar dependências
pip check

# Testar importações
python -c "import streamlit, boto3, httpx"
```

## 📈 Próximos Passos

### Melhorias Sugeridas

1. **Integração Real com Bedrock**
   - Conectar com Bedrock Agent real
   - Implementar autenticação AWS
   - Configurar IAM adequadamente

2. **API Gateway**
   - Adicionar API Gateway na frente
   - Implementar rate limiting
   - Configurar CORS

3. **Melhorias de UX**
   - Adicionar loading states
   - Implementar notificações
   - Melhorar responsividade

4. **Funcionalidades Adicionais**
   - Histórico de solicitações
   - Download de documentos
   - Integração com pagamento

## 📞 Suporte

Para dúvidas ou problemas:

1. **Verifique os logs** no Streamlit Cloud
2. **Teste localmente** primeiro
3. **Consulte a documentação** do Streamlit
4. **Abra uma issue** no repositório

## 📄 Licença

Este projeto é para fins de demonstração e desenvolvimento do CET-MG.

---

**Desenvolvido para CET-MG** 🚗✨
