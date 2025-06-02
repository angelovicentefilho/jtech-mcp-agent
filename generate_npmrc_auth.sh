#!/bin/bash

# Script para gerar credenciais de usuário para .npmrc
# Autor: GitHub Copilot
# Data: 02 de junho de 2025

# Cores para saída no terminal
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}Gerador de Credenciais para .npmrc${NC}"
echo -e "${BLUE}=====================================${NC}"

NPMRC_FILE=".npmrc"
REGISTRY_URL="https://nexus.jtech.com.br/repository/npm-jtech/"
PUBLIC_REGISTRY="https://registry.npmjs.org/"
SCOPE="@modelcontextprotocol"

# Verifica se o arquivo .npmrc já existe
if [ -f "$NPMRC_FILE" ]; then
    echo -e "${YELLOW}Arquivo .npmrc já existe. Deseja sobrescrever? (s/n)${NC}"
    read -r resposta
    if [[ "$resposta" != "s" && "$resposta" != "S" ]]; then
        echo -e "${RED}Operação cancelada pelo usuário.${NC}"
        exit 0
    fi
fi

# Solicita credenciais de usuário
echo -e "${YELLOW}Digite seu nome de usuário para o registro NPM do JTech:${NC}"
read -r username

echo -e "${YELLOW}Digite sua senha:${NC}"
read -r -s password

# Gera a string de autenticação em base64
auth=$(echo -n "$username:$password" | base64)

# Cria ou atualiza o arquivo .npmrc
cat > "$NPMRC_FILE" <<EOL
registry=${PUBLIC_REGISTRY}
${SCOPE}:registry=${REGISTRY_URL}
//nexus.jtech.com.br/repository/npm-jtech/:_auth=${auth}
//nexus.jtech.com.br/repository/npm-jtech/:always-auth=true
EOL

echo -e "\n${GREEN}Arquivo .npmrc criado com sucesso!${NC}"
echo -e "${BLUE}Configurações aplicadas:${NC}"
echo -e "  - Registro público: ${PUBLIC_REGISTRY}"
echo -e "  - Registro JTech para escopo ${SCOPE}: ${REGISTRY_URL}"
echo -e "  - Autenticação configurada para: ${username}\n"

# Tornar o script executável
chmod +x "$0"

echo -e "${YELLOW}Nota:${NC} Suas credenciais estão armazenadas em formato base64 no arquivo .npmrc."
echo -e "${YELLOW}      Este não é um método de criptografia seguro, apenas um encoding.${NC}"
