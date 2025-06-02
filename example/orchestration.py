#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Exemplo avançado de orquestração de agentes JtechMCP para operações em banco de dados.

Este script implementa um fluxo de trabalho com 4 agentes especializados que:
1. Obtém metadados da tabela revenue_forecast
2. Gera uma consulta SQL baseada nos metadados
3. Executa a consulta no banco de dados PostgreSQL
4. Transforma os resultados em um relatório e salva na pasta output
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

# Importações diretas dos módulos necessários
from jtech_mcp_executor import (
    JtechMCPAgent,
    JtechMCPClient,
    JtechMCPCrew,
    JtechMCPTask,
    SequentialWorkflow,
    AgentMemory
)

# Uso do modelo Gemini da Google, mas poderia ser trocado por outro
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

# Garantir que a pasta de saída existe
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Papéis específicos para cada agente no fluxo de trabalho
AGENT_ROLES = {
    "metadata_agent": "Agente de Metadados",
    "query_builder": "Construtor de Consultas SQL",
    "query_executor": "Executor de Consultas",
    "report_generator": "Gerador de Relatórios"
}

# Descrições dos papéis de cada agente
ROLE_DESCRIPTIONS = {
    "metadata_agent": "Especialista em coletar e interpretar metadados de tabelas do banco de dados.",
    "query_builder": "Especialista em construir consultas SQL precisas e eficientes baseadas em metadados.",
    "query_executor": "Especialista em executar consultas SQL e interpretar seus resultados.",
    "report_generator": "Especialista em transformar dados em relatórios estruturados e informativos."
}

# System prompts específicos para cada agente
SYSTEM_PROMPTS = {
    "metadata_agent": """Você é um especialista em banco de dados PostgreSQL e sua função é obter metadados detalhados sobre tabelas.
Sua tarefa específica é obter informações sobre a estrutura da tabela revenue_forecast, incluindo:
- Nomes e tipos das colunas
- Descrições de cada coluna (quando disponíveis)
- Restrições e chaves primárias/estrangeiras
- Índices e qualquer outra informação relevante sobre a estrutura

Organize suas descobertas em um formato estruturado e claro que possa ser utilizado por outros agentes para gerar e executar consultas SQL.
""",
    "query_builder": """Você é um especialista em construção de consultas SQL para PostgreSQL.
Sua função é analisar os metadados de tabelas fornecidos e criar consultas SQL bem estruturadas e eficientes.
Gere consultas que sigam as melhores práticas de SQL, incluindo:
- Seleção adequada de colunas relevantes
- Uso correto de cláusulas WHERE e JOIN
- Agregações e ordenações quando apropriado
- Otimização para performance

A consulta deve seguir exatamente as especificações solicitadas, sem adicionar ou remover elementos.
""",
    "query_executor": """Você é um especialista em execução de consultas SQL em bancos de dados PostgreSQL.
Sua função é:
- Executar a consulta SQL fornecida
- Capturar e interpretar os resultados
- Validar se a consulta foi executada com sucesso
- Formatar os resultados de maneira estruturada
- Detectar e relatar quaisquer erros ou problemas na execução

Apresente os resultados de forma clara e organizada para que possam ser facilmente transformados em relatórios.
""",
    "report_generator": f"""Você é um especialista em geração de relatórios analíticos.
Sua função é transformar resultados de consultas SQL em relatórios informativos e bem estruturados.
Seus relatórios devem:
- Conter título e data de geração
- Apresentar uma introdução explicando o contexto da análise
- Exibir os dados de forma organizada (tabelas, listas, etc.)
- Destacar insights importantes derivados dos dados
- Incluir uma conclusão resumindo as descobertas principais
- Ser formatado em markdown profissional e fácil de ler

IMPORTANTE: Você DEVE salvar o relatório como um arquivo markdown na pasta 'output'.

Para salvar seu relatório, faça o seguinte:

1. Crie o conteúdo do relatório como texto markdown
2. Use o código Python abaixo para salvar o relatório (copie EXATAMENTE este código):

```python
import os
from datetime import datetime

# Obter as informações do contexto
output_dir = context.get('output_dir')
nome_arquivo = context.get('output_filename')

# Criar o conteúdo completo do relatório (substitua este texto pelo seu relatório)
data_atual = datetime.now().strftime('%d/%m/%Y %H:%M')
conteudo = # Relatório de Faturamento - Plásticos (Jan-Mar)

**Data de geração:** 

## Introdução
Este relatório apresenta a análise de faturamento para plásticos nos meses de janeiro a março.

## Dados Analisados
[Seus dados aqui]

## Conclusão
[Sua conclusão aqui]


# Salvar o relatório
os.makedirs(output_dir, exist_ok=True)
caminho_arquivo = os.path.join(output_dir, nome_arquivo)
with open(caminho_arquivo, 'w', encoding='utf-8') as arquivo:
    arquivo.write(conteudo)

# Retornar o caminho do arquivo salvo
caminho_arquivo
```

Insira seu relatório no código acima no lugar de [Seus dados aqui] e [Sua conclusão aqui]. 
Retorne o caminho completo do arquivo salvo para confirmar que o relatório foi gerado com sucesso.
"""
}


async def setup_agents(config_path: str) -> Dict[str, JtechMCPAgent]:
    """
    Configura e retorna os agentes necessários para o fluxo de trabalho.
    
    Args:
        config_path: Caminho para o arquivo de configuração postgres-mcp.json
        
    Returns:
        Dicionário com os agentes configurados
    """
    # Carregar variáveis de ambiente (para chave de API do Google)
    load_dotenv()
    
    # Inicializar cliente MCP com configuração PostgreSQL
    client = JtechMCPClient.from_config_file(config_path)
    
    # Configurar modelo LLM (usando Google Gemini, mas poderia ser outro)
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",  # Usar modelo Gemini Flash para melhor performance
        temperature=0,            # Temperatura 0 para respostas mais determinísticas
        max_tokens=None,          # Sem limite de tokens para respostas
        timeout=None,             # Sem timeout
        max_retries=2,            # Tentar até 2 vezes em caso de falha
    )
    
    # Criar os agentes com papéis específicos
    agents = {}
    
    for role, name in AGENT_ROLES.items():
        # Criar um agente para cada papel com seu system prompt específico
        agent = JtechMCPAgent(
            llm=llm,
            client=client,  # Todos compartilham o mesmo cliente
            system_prompt=SYSTEM_PROMPTS[role],
            max_steps=30,   # Permitir até 30 passos para tarefas complexas
            auto_initialize=False,  # Inicializar apenas quando necessário
            memory_enabled=True,    # Habilitar memória para contexto
            verbose=True  # Ativar logs detalhados para depuração
        )
        
        # Definir o papel e descrição do agente
        agent.set_role(role, ROLE_DESCRIPTIONS[role])
        agents[role] = agent
        
    return agents


async def create_workflow() -> SequentialWorkflow:
    """
    Cria e retorna o fluxo de trabalho sequencial com as tarefas definidas.
    
    Returns:
        SequentialWorkflow com as tarefas configuradas
    """
    # Definir as tarefas para cada agente
    tarefas = [
        JtechMCPTask(
            description="Obtenha os metadados completos da tabela revenue_forecast, incluindo nomes das colunas, tipos de dados e descrições. Formate os resultados de maneira estruturada.",
            agent_name="metadata_agent",
            name="ObterMetadados",
            expected_output="Metadados estruturados da tabela revenue_forecast."
        ),
        JtechMCPTask(
            description="Com base nos metadados fornecidos, gere uma consulta SQL que obtenha os valores de faturamento para plásticos nos meses de janeiro a março. A consulta deve ser válida para PostgreSQL e usar apenas as colunas disponíveis.",
            agent_name="query_builder",
            name="GerarConsultaSQL",
            expected_output="Uma consulta SQL válida e otimizada."
        ),
        JtechMCPTask(
            description="Execute a consulta SQL fornecida no banco de dados PostgreSQL e capture os resultados. Verifique se a execução foi bem-sucedida e formate os resultados de maneira estruturada.",
            agent_name="query_executor",
            name="ExecutarConsulta",
            expected_output="Resultados da consulta em formato estruturado."
        ),
        JtechMCPTask(
            description="Transforme os resultados da consulta em um relatório completo. O relatório deve incluir título, data, introdução, os dados em formato tabular, análises e conclusão. Salve o relatório como um arquivo markdown na pasta 'output' com nome 'relatorio_faturamento_plasticos.md'. Certifique-se de que o arquivo seja criado corretamente e retorne o caminho completo do arquivo salvo.",
            agent_name="report_generator",
            name="GerarRelatorio",
            expected_output="Caminho para o arquivo de relatório salvo.",
            context={"output_filename": "relatorio_faturamento_plasticos.md"}
        )
    ]
    
    # Criar o workflow sequencial com as tarefas
    workflow = SequentialWorkflow(tasks=tarefas)
    return workflow


async def run_database_workflow(config_path: str) -> None:
    """
    Executa o fluxo de trabalho completo do banco de dados.
    
    Args:
        config_path: Caminho para o arquivo de configuração postgres-mcp.json
    """
    print("🚀 Iniciando o fluxo de trabalho de banco de dados...")
    
    # Configurar os agentes
    agents = await setup_agents(config_path)
    
    # Criar o crew com os agentes
    crew_memory = AgentMemory()
    crew = JtechMCPCrew(
        name="Equipe de Análise de Dados",
        description="Equipe especializada em análise de dados de banco PostgreSQL",
        agents=list(agents.values()),
        shared_memory=crew_memory,
        verbose=True  # Ativar logs detalhados
    )
    
    # Criar o workflow
    workflow = await create_workflow()
    
    try:
        print("\n📊 Executando workflow de análise de dados...")
        
        # Descrição geral da tarefa
        task_description = "Analisar os dados de faturamento para plásticos nos meses de janeiro a março da tabela revenue_forecast e gerar um relatório."
        
        # Contexto inicial
        initial_context = {
            "database": "waste_dev",
            "target_table": "revenue_forecast",
            "material_filter": "plásticos",
            "date_range": "janeiro a março",
            "output_format": "markdown",
            "output_dir": OUTPUT_DIR
        }
        
        # Executar o workflow
        resultado = await crew.run(
            task_description=task_description,
            workflow=workflow,
            initial_context=initial_context
        )
        
        # Exibir resultados
        print("\n✅ Workflow concluído!")
        print(f"Status: {resultado.get('status', 'Desconhecido')}")
        
        if resultado.get('status') == "CONCLUÍDO":
            report_path = resultado.get('final_output')
            print(f"\nRelatório gerado e salvo em: {report_path}")
            
            # Verificar se o arquivo realmente existe
            expected_file = os.path.join(OUTPUT_DIR, "relatorio_faturamento_plasticos.md")
            
            if os.path.exists(expected_file):
                print(f"✅ Arquivo confirmado: {expected_file}")
                print("\nConteúdo do relatório:")
                with open(expected_file, 'r', encoding='utf-8') as f:
                    conteudo = f.read()
                    print("-"*50)
                    print(conteudo[:500] + "..." if len(conteudo) > 500 else conteudo)
                    print("-"*50)
            else:
                # Se o arquivo não existir, mas temos uma resposta, vamos criá-lo
                if report_path and isinstance(report_path, str) and len(report_path) > 10:
                    print(f"⚠️ Arquivo não encontrado, mas recebemos uma resposta. Criando arquivo em: {expected_file}")
                    
                    # Criar um relatório simples com os dados coletados
                    from datetime import datetime
                    
                    # Extrair informações do contexto final
                    metadados = resultado.get('final_context', {}).get('task_ObterMetadados_output', 'Metadados não disponíveis')
                    consulta_sql = resultado.get('final_context', {}).get('task_GerarConsultaSQL_output', 'Consulta SQL não disponível')
                    resultados_consulta = resultado.get('final_context', {}).get('task_ExecutarConsulta_output', 'Resultados da consulta não disponíveis')
                    
                    relatorio = f"""# Relatório de Faturamento - Plásticos (Jan-Mar)

**Data de geração:** {datetime.now().strftime('%d/%m/%Y %H:%M')}

## Introdução
Este relatório apresenta a análise de faturamento para plásticos nos meses de janeiro a março da tabela revenue_forecast.

## Metadados da Tabela
{metadados}

## Consulta SQL Gerada
```sql
{consulta_sql}
```

## Resultados da Consulta
{resultados_consulta}

## Conclusão
Relatório gerado automaticamente pelo framework de orquestração de agentes JTech MCP.
"""
                    
                    with open(expected_file, 'w', encoding='utf-8') as f:
                        f.write(relatorio)
                    print(f"✅ Arquivo criado manualmente: {expected_file}")
                else:
                    print("❌ Relatório não foi salvo no disco!")
        else:
            print("\n❌ Workflow não foi concluído com sucesso.")
            print(f"Erro: {resultado.get('error', 'Erro desconhecido')}")
        
    except Exception as e:
        print(f"\n❌ Erro durante a execução do workflow: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Fechar todos os agentes e recursos
        print("\n🧹 Limpando recursos...")
        try:
            await crew.close()
            print("✅ Recursos limpos com sucesso.")
        except Exception as e:
            print(f"⚠️ Aviso: Houve erros durante a limpeza de recursos: {e}")
            print("  Isso não afeta os resultados do workflow, apenas o encerramento dos recursos.")
        
    print("\n🏁 Processo finalizado!")


if __name__ == "__main__":
    # Configurar logging básico
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='[%(levelname)s] %(name)s: %(message)s'
    )
    
    # Caminho para o arquivo de configuração
    config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "postgres-mcp.json")
    
    # Executar o workflow
    asyncio.run(run_database_workflow(config_file))
