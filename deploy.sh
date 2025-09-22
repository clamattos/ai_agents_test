#!/bin/bash

# Script para deploy da aplicação CET-MG no Streamlit Cloud
# Execute este script para preparar e fazer deploy da aplicação

echo "🚗 CET-MG - Deploy para Streamlit Cloud"
echo "======================================"

# Verificar se estamos em um repositório Git
if [ ! -d ".git" ]; then
    echo "❌ Erro: Este diretório não é um repositório Git"
    echo "Execute: git init"
    exit 1
fi

# Verificar se os arquivos necessários existem
echo "📋 Verificando arquivos necessários..."

required_files=("app.py" "requirements.txt" "README.md")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Arquivo necessário não encontrado: $file"
        exit 1
    fi
done

echo "✅ Todos os arquivos necessários encontrados"

# Verificar se o remote origin está configurado
if ! git remote get-url origin > /dev/null 2>&1; then
    echo "⚠️  Remote origin não configurado"
    echo "Configure com: git remote add origin https://github.com/USUARIO/REPOSITORIO.git"
    echo "Substitua USUARIO e REPOSITORIO pelos seus dados"
    exit 1
fi

# Adicionar todos os arquivos
echo "📦 Adicionando arquivos ao Git..."
git add .

# Fazer commit
echo "💾 Fazendo commit..."
git commit -m "Deploy: CET-MG Assistente CNH para Streamlit Cloud

- Aplicação Streamlit completa
- Interface de chat interativa
- Formulários para segunda via e consulta
- Simulação do backend CET-MG
- Configurações otimizadas para Streamlit Cloud"

# Push para o repositório
echo "🚀 Enviando para o repositório..."
git push origin main

echo ""
echo "✅ Deploy concluído!"
echo ""
echo "📋 Próximos passos:"
echo "1. Acesse https://share.streamlit.io"
echo "2. Faça login com sua conta GitHub"
echo "3. Clique em 'New app'"
echo "4. Selecione seu repositório"
echo "5. Configure:"
echo "   - Repository: $(git remote get-url origin | sed 's/.*github.com\///' | sed 's/\.git$//')"
echo "   - Branch: main"
echo "   - Main file path: app.py"
echo "6. Clique em 'Deploy!'"
echo ""
echo "🔗 Sua aplicação estará disponível em:"
echo "https://share.streamlit.io/[seu-usuario]/[seu-repositorio]"
echo ""
echo "📚 Para mais informações, consulte o README.md"
