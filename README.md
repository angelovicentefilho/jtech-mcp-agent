<picture>
  <img alt="" src="./static/logo-jtech.png"  width="full">
</picture>

<h1 align="center">Biblioteca Unificada de Cliente MCP</h1>

🌐 Jtech-MCP-Executor é a solução proprietária da J-Tech para conectar **qualquer LLM a qualquer servidor MCP** e construir agentes personalizados que têm acesso a ferramentas.

💡 Permite que desenvolvedores da J-Tech conectem facilmente qualquer LLM a ferramentas como navegação web, operações de arquivos, e muito mais.

# Recursos

## ✨ Recursos Principais

| Recurso | Descrição |
|---------|-------------|
| 🔄 [**Facilidade de uso**](#início-rápido) | Crie seu primeiro agente MCP com apenas 6 linhas de código |
| 🤖 [**Flexibilidade de LLM**](#instalando-provedores-langchain) | Funciona com qualquer LLM suportado pelo LangChain que tenha suporte a chamada de ferramentas (OpenAI, Anthropic, Groq, LLama etc.) |
| 🔗 [**Suporte HTTP**](#exemplo-de-conexão-http) | Conexão direta com servidores MCP rodando em portas HTTP específicas |
| ⚙️ [**Seleção Dinâmica de Servidor**](#seleção-dinâmica-de-servidor-gerenciador-de-servidor) | Os agentes podem escolher dinamicamente o servidor MCP mais apropriado para uma determinada tarefa dentre os disponíveis |
| 🧩 [**Suporte Multi-Servidor**](#suporte-multi-servidor) | Use múltiplos servidores MCP simultaneamente em um único agente |
| 🛡️ [**Restrições de Ferramentas**](#controle-de-acesso-a-ferramentas) | Restrinja ferramentas potencialmente perigosas como acesso ao sistema de arquivos ou à rede |
| 🔧 [**Agentes Personalizados**](#construa-um-agente-personalizado) | Construa seus próprios agentes com qualquer framework usando o adaptador LangChain ou crie novos adaptadores |


# Início Rápido

Para instalação a partir do repositório interno da J-Tech:

```bash
pip install jtech-mcp-executor --index-url=https://pypi.jtech.interno/simple/
```

Ou instale a partir do código fonte:

```bash
git clone https://gitlab.com/veolia.com/brasil/jtech/jtech-generative-ai/poc/jtech-mcp-executor.git
cd jtech-mcp-executor
pip install -e .
```

### Instalando Provedores LangChain

jtech_mcp_executor trabalha com vários provedores de LLM através do LangChain. Você precisará instalar o pacote provedor LangChain apropriado para o LLM escolhido. Por exemplo:

```bash
# Para OpenAI
pip install langchain-openai

# Para Anthropic
pip install langchain-anthropic

# Para outros provedores, consulte a [documentação de modelos de chat LangChain](https://python.langchain.com/docs/integrations/chat/)
```

e adicione suas chaves API para o provedor que deseja usar ao seu arquivo `.env`.

```bash
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
```

> **Importante**: Apenas modelos com recursos de chamadas de ferramentas podem ser usados com jtech_mcp_executor. Certifique-se de que seu modelo escolhido suporte chamadas de função ou uso de ferramentas.

### Inicie seu agente:

```python
import asyncio
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from jtech_mcp_executor import JtechMCPAgent, JtechMCPClient

async def main():
    # Carregar variáveis de ambiente
    load_dotenv()

    # Criar dicionário de configuração
    config = {
      "mcpServers": {
        "playwright": {
          "command": "npx",
          "args": ["@playwright/mcp@latest"],
          "env": {
            "DISPLAY": ":1"
          }
        }
      }
    }

    # Criar JtechMCPClient a partir do dicionário de configuração
    client = JtechMCPClient.from_dict(config)

    # Criar LLM
    llm = ChatOpenAI(model="gpt-4o")

    # Criar agente com o cliente
    agent = JtechMCPAgent(llm=llm, client=client, max_steps=30)

    # Executar a consulta
    result = await agent.run(
        "Encontre o melhor restaurante em São Paulo",
    )
    print(f"\nResultado: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```

Você também pode adicionar a configuração de servidores a partir de um arquivo de configuração assim:

```python
client = JtechMCPClient.from_config_file(
        os.path.join("browser_mcp.json")
    )
```

Exemplo de arquivo de configuração (`browser_mcp.json`):

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"],
      "env": {
        "DISPLAY": ":1"
      }
    }
  }
}
```

Para outras configurações, modelos e mais, consulte a documentação.

## Saída de Agente em Streaming

JtechMCPExecutor suporta streaming assíncrono de saída do agente usando o método `astream` no `JtechMCPAgent`. Isso permite que você receba resultados incrementais, ações de ferramentas e etapas intermediárias conforme são geradas pelo agente, permitindo feedback em tempo real e relatórios de progresso.

### Como usar

Chame `agent.astream(query)` e itere sobre os resultados de forma assíncrona:

```python
async for chunk in agent.astream("Encontre o melhor restaurante em São Paulo"):
    print(chunk["messages"], end="", flush=True)
```

Cada fragmento é um dicionário contendo chaves como `actions`, `steps`, `messages` e (no último fragmento) `output`. Isso permite construir interfaces de usuário responsivas ou registrar o progresso do agente em tempo real.

#### Exemplo: Streaming na Prática

```python
import asyncio
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from jtech_mcp_executor import JtechMCPAgent, JtechMCPClient

async def main():
    load_dotenv()
    client = JtechMCPClient.from_config_file("browser_mcp.json")
    llm = ChatOpenAI(model="gpt-4o")
    agent = JtechMCPAgent(llm=llm, client=client, max_steps=30)
    async for chunk in agent.astream("Procure trabalho na NVIDIA para engenheiro de aprendizado de máquina."):
        print(chunk["messages"], end="", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
```

Esta interface de streaming é ideal para aplicações que requerem atualizações em tempo real, como chatbots, painéis ou notebooks interativos.

# Exemplos de Casos de Uso

## Navegação Web com Playwright

```python
import asyncio
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from jtech_mcp_executor import JtechMCPAgent, JtechMCPClient

async def main():
    # Carregar variáveis de ambiente
    load_dotenv()

    # Criar JtechMCPClient a partir do arquivo de configuração
    client = JtechMCPClient.from_config_file(
        os.path.join(os.path.dirname(__file__), "browser_mcp.json")
    )

    # Criar LLM
    llm = ChatOpenAI(model="gpt-4o")
    # Modelos alternativos:
    # llm = ChatAnthropic(model="claude-3-5-sonnet-20240620")
    # llm = ChatGroq(model="llama3-8b-8192")

    # Criar agente com o cliente
    agent = JtechMCPAgent(llm=llm, client=client, max_steps=30)

    # Executar a consulta
    result = await agent.run(
        "Encontre o melhor restaurante em São Paulo USANDO PESQUISA DO GOOGLE",
        max_steps=30,
    )
    print(f"\nResultado: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Pesquisa no Airbnb

```python
import asyncio
import os
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from jtech_mcp_executor import JtechMCPAgent, JtechMCPClient

async def run_airbnb_example():
    # Carregar variáveis de ambiente
    load_dotenv()

    # Criar JtechMCPClient com configuração do Airbnb
    client = JtechMCPClient.from_config_file(
        os.path.join(os.path.dirname(__file__), "airbnb_mcp.json")
    )

    # Criar LLM - você pode escolher entre diferentes modelos
    llm = ChatAnthropic(model="claude-3-5-sonnet-20240620")

    # Criar agente com o cliente
    agent = JtechMCPAgent(llm=llm, client=client, max_steps=30)

    try:
        # Executar uma consulta para buscar acomodações
        result = await agent.run(
            "Encontre um bom lugar para ficar em Florianópolis para 2 adultos "
            "por uma semana em agosto. Prefiro lugares com piscina e "
            "boas avaliações. Mostre-me as 3 melhores opções.",
            max_steps=30,
        )
        print(f"\nResultado: {result}")
    finally:
        # Garantir que os recursos sejam limpos adequadamente
        if client.sessions:
            await client.close_all_sessions()

if __name__ == "__main__":
    asyncio.run(run_airbnb_example())
```

Exemplo de arquivo de configuração (`airbnb_mcp.json`):

```json
{
  "mcpServers": {
    "airbnb": {
      "command": "npx",
      "args": ["-y", "@openbnb/mcp-server-airbnb"]
    }
  }
}
```

## Criação 3D com Blender

```python
import asyncio
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from jtech_mcp_executor import JtechMCPAgent, JtechMCPClient

async def run_blender_example():
    # Carregar variáveis de ambiente
    load_dotenv()

    # Criar JtechMCPClient com configuração MCP do Blender
    config = {"mcpServers": {"blender": {"command": "uvx", "args": ["blender-mcp"]}}}
    client = JtechMCPClient.from_dict(config)

    # Criar LLM
    llm = ChatAnthropic(model="claude-3-5-sonnet-20240620")

    # Criar agente com o cliente
    agent = JtechMCPAgent(llm=llm, client=client, max_steps=30)

    try:
        # Executar a consulta
        result = await agent.run(
            "Crie um cubo inflável com material macio e um plano como chão.",
            max_steps=30,
        )
        print(f"\nResultado: {result}")
    finally:
        # Garantir que os recursos sejam limpos adequadamente
        if client.sessions:
            await client.close_all_sessions()

if __name__ == "__main__":
    asyncio.run(run_blender_example())
```

# Suporte a Arquivo de Configuração

JtechMCPExecutor suporta inicialização a partir de arquivos de configuração, facilitando o gerenciamento e a alternância entre diferentes configurações de servidores MCP:

```python
import asyncio
from jtech_mcp_executor import create_session_from_config

async def main():
    # Criar uma sessão MCP a partir de um arquivo de configuração
    session = create_session_from_config("mcp-config.json")

    # Inicializar a sessão
    await session.initialize()

    # Usar a sessão...

    # Desconectar quando terminar
    await session.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
```

## Exemplo de Conexão HTTP

JtechMCPExecutor suporta conexões HTTP, permitindo que você se conecte a servidores MCP rodando em portas HTTP específicas. Este recurso é particularmente útil para integração com servidores MCP baseados na web.

Aqui está um exemplo de como usar o recurso de conexão HTTP:

```python
import asyncio
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from jtech_mcp_executor import JtechMCPAgent, JtechMCPClient

async def main():
    """Execute o exemplo usando um arquivo de configuração."""
    # Carregar variáveis de ambiente
    load_dotenv()

    config = {
        "mcpServers": {
            "http": {
                "url": "http://localhost:8931/sse"
            }
        }
    }

    # Criar JtechMCPClient a partir do arquivo de configuração
    client = JtechMCPClient.from_dict(config)

    # Criar LLM
    llm = ChatOpenAI(model="gpt-4o")

    # Criar agente com o cliente
    agent = JtechMCPAgent(llm=llm, client=client, max_steps=30)

    # Executar a consulta
    result = await agent.run(
        "Encontre o melhor restaurante em São Paulo USANDO PESQUISA DO GOOGLE",
        max_steps=30,
    )
    print(f"\nResultado: {result}")

if __name__ == "__main__":
    # Executar o exemplo apropriado
    asyncio.run(main())
```

Este exemplo demonstra como se conectar a um servidor MCP rodando em uma porta HTTP específica. Certifique-se de iniciar seu servidor MCP antes de executar este exemplo.

# Suporte Multi-Servidor

JtechMCPExecutor permite configurar e conectar-se a múltiplos servidores MCP simultaneamente usando o `JtechMCPClient`. Isso possibilita fluxos de trabalho complexos que requerem ferramentas de diferentes servidores, como navegação web combinada com operações de arquivos ou modelagem 3D.

## Configuração

Você pode configurar múltiplos servidores em seu arquivo de configuração:

```json
{
  "mcpServers": {
    "airbnb": {
      "command": "npx",
      "args": ["-y", "@openbnb/mcp-server-airbnb", "--ignore-robots-txt"]
    },
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"],
      "env": {
        "DISPLAY": ":1"
      }
    }
  }
}
```

## Uso

A classe `JtechMCPClient` fornece métodos para gerenciar conexões a múltiplos servidores. Ao criar um `JtechMCPAgent`, você pode fornecer um `JtechMCPClient` configurado com múltiplos servidores.

Por padrão, o agente terá acesso a ferramentas de todos os servidores configurados. Se você precisar direcionar um servidor específico para uma tarefa particular, pode especificar o `server_name` ao chamar o método `agent.run()`.

```python
# Exemplo: Seleção manual de um servidor para uma tarefa específica
result = await agent.run(
    "Procure por listagens do Airbnb em Florianópolis",
    server_name="airbnb" # Use explicitamente o servidor airbnb
)

result_google = await agent.run(
    "Encontre restaurantes perto do primeiro resultado usando a Pesquisa do Google",
    server_name="playwright" # Use explicitamente o servidor playwright
)
```

## Seleção Dinâmica de Servidor (Gerenciador de Servidor)

Para maior eficiência e para reduzir a potencial confusão do agente ao lidar com muitas ferramentas de diferentes servidores, você pode habilitar o Gerenciador de Servidor definindo `use_server_manager=True` durante a inicialização do `JtechMCPAgent`.

Quando habilitado, o agente seleciona inteligentemente o servidor MCP correto com base na ferramenta escolhida pelo LLM para uma etapa específica. Isso minimiza conexões desnecessárias e garante que o agente use as ferramentas apropriadas para a tarefa.

```python
import asyncio
from jtech_mcp_executor import JtechMCPClient, JtechMCPAgent
from langchain_anthropic import ChatAnthropic

async def main():
    # Criar cliente com múltiplos servidores
    client = JtechMCPClient.from_config_file("multi_server_config.json")

    # Criar agente com o cliente
    agent = JtechMCPAgent(
        llm=ChatAnthropic(model="claude-3-5-sonnet-20240620"),
        client=client,
        use_server_manager=True  # Habilitar o Gerenciador de Servidor
    )

    try:
        # Executar uma consulta que usa ferramentas de múltiplos servidores
        result = await agent.run(
            "Procure por um bom lugar para ficar em Florianópolis no Airbnb, "
            "depois use o Google para encontrar restaurantes e atrações próximas."
        )
        print(result)
    finally:
        # Limpar todas as sessões
        await client.close_all_sessions()

if __name__ == "__main__":
    asyncio.run(main())
```

# Controle de Acesso a Ferramentas

JtechMCPExecutor permite que você restrinja quais ferramentas estão disponíveis para o agente, proporcionando melhor segurança e controle sobre as capacidades do agente:

```python
import asyncio
from jtech_mcp_executor import JtechMCPAgent, JtechMCPClient
from langchain_openai import ChatOpenAI

async def main():
    # Criar cliente
    client = JtechMCPClient.from_config_file("config.json")

    # Criar agente com ferramentas restritas
    agent = JtechMCPAgent(
        llm=ChatOpenAI(model="gpt-4"),
        client=client,
        disallowed_tools=["file_system", "network"]  # Restringir ferramentas potencialmente perigosas
    )

    # Executar uma consulta com acesso a ferramentas restrito
    result = await agent.run(
        "Encontre o melhor restaurante em São Paulo"
    )
    print(result)

    # Limpar
    await client.close_all_sessions()

if __name__ == "__main__":
    asyncio.run(main())
```

# Construa um Agente Personalizado:

Você também pode construir seu próprio agente personalizado usando o adaptador LangChain:

```python
import asyncio
from langchain_openai import ChatOpenAI
from jtech_mcp_executor.client import JtechMCPClient
from jtech_mcp_executor.adapters.langchain_adapter import LangChainAdapter
from dotenv import load_dotenv

load_dotenv()


async def main():
    # Inicializar cliente MCP
    client = JtechMCPClient.from_config_file("examples/browser_mcp.json")
    llm = ChatOpenAI(model="gpt-4o")

    # Criar instância do adaptador
    adapter = LangChainAdapter()
    # Obter ferramentas LangChain com uma única linha
    tools = await adapter.create_tools(client)

    # Criar um agente LangChain personalizado
    llm_with_tools = llm.bind_tools(tools)
    result = await llm_with_tools.ainvoke("Quais ferramentas você tem disponíveis?")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
```

# Depuração

JtechMCPExecutor fornece um modo de depuração integrado que aumenta a verbosidade dos logs e ajuda a diagnosticar problemas na implementação do seu agente.

## Habilitando o Modo de Depuração

Existem duas maneiras principais de habilitar o modo de depuração:

### 1. Variável de Ambiente (Recomendado para Execuções Pontuais)

Execute seu script com a variável de ambiente `DEBUG` definida para o nível desejado:

```bash
# Nível 1: Mostrar mensagens de nível INFO
DEBUG=1 python3.11 examples/browser_use.py

# Nível 2: Mostrar mensagens de nível DEBUG (saída verbosa completa)
DEBUG=2 python3.11 examples/browser_use.py
```

Isso define o nível de depuração apenas para a duração desse processo Python específico.

Alternativamente, você pode definir a seguinte variável de ambiente para o nível de log desejado:

```bash
export MCP_USE_DEBUG=1 # ou 2
```

### 2. Definindo a Flag de Depuração Programaticamente

Você pode definir a flag de depuração global diretamente em seu código:

```python
import jtech_mcp_executor

jtech_mcp_executor.set_debug(1)  # Nível INFO
# ou
jtech_mcp_executor.set_debug(2)  # Nível DEBUG (saída verbosa completa)
```

### 3. Verbosidade Específica do Agente

Se você quiser ver apenas informações de depuração do agente sem habilitar o log de depuração completo, pode definir o parâmetro `verbose` ao criar um JtechMCPAgent:

```python
# Criar agente com verbosidade aumentada
agent = JtechMCPAgent(
    llm=seu_llm,
    client=seu_cliente,
    verbose=True  # Mostra apenas mensagens de depuração do agente
)
```

Isso é útil quando você só precisa ver as etapas e o processo de tomada de decisão do agente sem todas as informações de depuração de baixo nível de outros componentes.

# Desenvolvimento com Makefile

O projeto JTech MCP Executor inclui um Makefile para simplificar tarefas comuns de desenvolvimento. Isso facilita a configuração do ambiente, execução de testes e criação de distribuições do pacote.

## 🛠️ Comandos do Makefile

| Comando | Descrição |
|---------|-----------|
| `make help` | Exibe informações sobre todos os comandos disponíveis |
| `make venv` | Cria um ambiente virtual Python. Se já existir, pergunta se deseja recriar |
| `make install` | Instala o pacote sem dependências de desenvolvimento |
| `make install-dev` | Instala o pacote em modo editável com todas as dependências |
| `make test` | Executa os testes unitários do projeto |
| `make lint` | Executa verificações de linting com Ruff |
| `make clean` | Remove arquivos temporários e diretórios de build |
| `make build` | Constrói o pacote para distribuição, permitindo selecionar a versão |
| `make publish` | Publica o pacote no PyPI |
| `make publish-test` | Publica o pacote no TestPyPI para testes |

## 🚀 Exemplos de Uso

### Configuração do Ambiente de Desenvolvimento

```bash
# Criar ambiente virtual e instalar em modo desenvolvimento
make install-dev

# Após a instalação, ative o ambiente virtual
source .venv/bin/activate
```

### Testes e Linting

```bash
# Executar os testes
make test

# Verificar código com o linter
make lint
```

### Construir e Publicar

```bash
# Limpar arquivos temporários e construir o pacote
make build
```

Ao executar `make build`, você verá um menu interativo que permite:
1. Incrementar número de patch (para correções)
2. Incrementar número minor (para novos recursos compatíveis)
3. Incrementar número major (para mudanças incompatíveis)
4. Inserir uma versão personalizada
5. Manter a versão atual

A versão escolhida será atualizada no arquivo `pyproject.toml` e o pacote será construído com esta versão.

```bash
# Publicar no PyPI (requer autenticação)
make publish
```

## 📋 Fluxo de Trabalho Recomendado

Para desenvolvimento:
1. `make install-dev` - Configure o ambiente
2. Faça suas alterações no código
3. `make test` - Certifique-se de que os testes passam
4. `make lint` - Verifique se o código está em conformidade com os padrões

Para lançamento:
1. `make build` - Construa o pacote e selecione a versão adequada
2. `make publish-test` - Teste a publicação no TestPyPI
3. `make publish` - Publique oficialmente no PyPI

> **Nota**: Para publicar no PyPI ou TestPyPI, você deve configurar seus tokens de autenticação com o Poetry antes de executar `make publish` ou `make publish-test`. Use `poetry config pypi-token.pypi <seu-token>` para configurar o token do PyPI.

# Configuração para Pacotes npm da J-Tech

Para utilizar servidores MCP como PostgreSQL, Airbnb e outros que dependem de pacotes do repositório npm interno da J-Tech, é necessário configurar corretamente a autenticação no npm. Sem essa configuração, você poderá encontrar erros como:

```
HttpErrorAuthUnknown: Unable to authenticate, need: BASIC realm="Sonatype Nexus Repository Manager"
```

## 🔐 Configurando o arquivo .npmrc

1. Crie ou edite um arquivo `.npmrc` na raiz do seu projeto:

```bash
# Crie o arquivo .npmrc se ele não existir
touch .npmrc
```

2. Adicione as seguintes configurações ao arquivo:

```properties
registry=https://registry.npmjs.org/
@modelcontextprotocol:registry=https://nexus.jtech.com.br/repository/npm-jtech/
//nexus.jtech.com.br/repository/npm-jtech/:_auth=${JTECH_NPM_AUTH}
//nexus.jtech.com.br/repository/npm-jtech/:always-auth=true
```

3. Configure a variável de ambiente `JTECH_NPM_AUTH` com suas credenciais em formato Base64:

```bash
# Gerar a string Base64 a partir de suas credenciais
echo -n "seu_usuario:sua_senha" | base64

# Exemplo do resultado: c2V1X3VzdWFyaW86c3VhX3Nlbmhh
```

4. Adicione a variável de ambiente ao seu ambiente:

```bash
# Temporariamente (para uma única sessão)
export JTECH_NPM_AUTH=sua_string_base64

# OU permanentemente (adicionando ao seu .bashrc ou .zshrc)
echo 'export JTECH_NPM_AUTH=sua_string_base64' >> ~/.bashrc
source ~/.bashrc
```

## 🔄 Configuração Alternativa (sem variável de ambiente)

Se preferir não usar variáveis de ambiente, você pode adicionar suas credenciais diretamente no arquivo `.npmrc`:

```properties
registry=https://registry.npmjs.org/
@modelcontextprotocol:registry=https://nexus.jtech.com.br/repository/npm-jtech/
//nexus.jtech.com.br/repository/npm-jtech/:_auth=c2V1X3VzdWFyaW86c3VhX3Nlbmhh
//nexus.jtech.com.br/repository/npm-jtech/:always-auth=true
```

## 🚀 Testando a Configuração

Após configurar o `.npmrc`, teste a autenticação:

```bash
# Exemplo para testar o acesso ao servidor PostgreSQL
npx --yes @modelcontextprotocol/server-postgres --help
```

Se a configuração estiver correta, o comando será executado sem erros de autenticação.

## 📋 Exemplo de Configuração para PostgreSQL

Para usar o servidor MCP PostgreSQL, crie um arquivo de configuração como `postgres-mcp.json`:

```json
{
  "mcpServers": {
    "postgres": {
      "command": "npx",
      "args": [
        "--yes",
        "@modelcontextprotocol/server-postgres",
        "postgresql://usuario:senha@host:porta/base_de_dados"
      ]
    }
  }
}
```

> **Dica**: Para projetos de produção, considere usar variáveis de ambiente ou um gerenciador de segredos para as credenciais do banco de dados.

# Exemplo Completo: Consultas SQL com PostgreSQL e Catálogo de Metadados

O exemplo a seguir demonstra como usar o JTech MCP Executor com um banco de dados PostgreSQL, passando um contexto rico de metadados sobre as tabelas para melhorar a precisão das consultas SQL geradas.

## Arquivo de Configuração

Primeiro, crie um arquivo de configuração `postgres-mcp.json` para o servidor PostgreSQL:

```json
{
  "mcpServers": {
    "postgres": {
      "command": "npx",
      "args": [
        "--yes",
        "@modelcontextprotocol/server-postgres",
        "postgresql://usuario:senha@host:porta/base_de_dados"
      ]
    }
  }
}
```

## Código Exemplo

Aqui está um exemplo completo (`database.py`) que mostra como:
1. Configurar metadados de tabelas para fornecer contexto ao modelo
2. Conectar ao servidor MCP PostgreSQL
3. Executar uma consulta em linguagem natural com o contexto das tabelas

```python
import asyncio
import os
from typing import Dict, Any
from dotenv import load_dotenv
from jtech_mcp_executor import JtechMCPAgent, JtechMCPClient
from langchain_google_genai import ChatGoogleGenerativeAI

# Catálogo de metadados das tabelas
TABLE_CATALOG: Dict[str, Dict[str, Any]] = {
    "revenue_forecast": {
        "description": "Projeções e dados históricos de faturamento por cliente e período",
        "keywords": ["faturamento", "receita", "projeção", "previsão", "cliente", "resíduo"],
        "campos": [
            {"nome": "client_id", "tipo": "INT", "descricao": "Identificador único do cliente"},
            {"nome": "year", "tipo": "INT", "descricao": "Ano da projeção ou dado histórico"},
            {"nome": "month", "tipo": "INT", "descricao": "Mês da projeção ou dado histórico (1-12)"},
            {"nome": "material_type", "tipo": "VARCHAR", "descricao": "Tipo de material (metais, plásticos, etc)"},
            {"nome": "revenue", "tipo": "DECIMAL", "descricao": "Valor do faturamento em reais"}
        ]
    },
    "customer": {
        "description": "Dados cadastrais de clientes",
        "keywords": ["cliente", "contato", "cadastro", "empresa"],
        "campos": [
            {"nome": "client_id", "tipo": "INT", "descricao": "Identificador único do cliente"},
            {"nome": "name", "tipo": "VARCHAR", "descricao": "Nome da empresa cliente"},
            {"nome": "segment", "tipo": "VARCHAR", "descricao": "Segmento de atuação do cliente"}
        ]
    }
    # Adicione outras tabelas conforme necessário
}

async def postgres():
    # Carregar variáveis de ambiente
    load_dotenv()

    # Inicializar cliente com configuração
    client = JtechMCPClient.from_config_file("./postgres-mcp.json")

    # Configurar modelo LLM
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
    )

    # Criar agente com o cliente
    agent = JtechMCPAgent(llm=llm, client=client, max_steps=30)

    try:
        # Consulta em linguagem natural
        query = "Preciso saber qual o faturamento para os meses de janeiro até março da tabela revenue_forecast somente para plásticos, apresente o valor em Reais (R$)"
        
        result = await agent.run(query,max_steps=30)
        print(f"\nResultado: {result}")
    finally:
        # Garantir que os recursos sejam limpos adequadamente
        if client.sessions:
            await client.close_all_sessions()

if __name__ == "__main__":
    asyncio.run(postgres())
```

## Como Executar o Exemplo

1. Certifique-se de que você já configurou o `.npmrc` conforme explicado acima
2. Instale as dependências necessárias:
   ```bash
   pip install langchain-google-genai python-dotenv
   ```
3. Configure sua chave API do Google em um arquivo `.env`:
   ```
   GOOGLE_API_KEY=sua_chave_api_aqui
   ```
4. Ajuste as informações de conexão do PostgreSQL no arquivo `postgres-mcp.json`
5. Execute o script:
   ```bash
   python database.py
   ```

## Como Funciona

1. **Catálogo de Metadados**: Define estrutura, descrições e palavras-chave para as tabelas
2. **Formatação do Contexto**: Converte o catálogo em um texto estruturado para o LLM
3. **Execução da Consulta**: O agente usa o contexto para entender o esquema do banco e gerar SQL mais preciso

Este padrão é especialmente útil quando:
- O esquema do banco de dados é complexo
- Você deseja fornecer detalhes semânticos sobre o significado dos dados
- Precisa de consultas precisas que respeitem relações e tipos de dados específicos

Você pode expandir o catálogo de metadados com informações adicionais como restrições, relacionamentos entre tabelas, intervalos válidos para campos, etc.
