import asyncio
from unittest.mock import MagicMock, AsyncMock

# Supondo que as classes reais estão acessíveis via jtech_mcp_executor
# Se este script for executado de fora do pacote, pode precisar ajustar os imports
# ou garantir que jtech_mcp_executor esteja no PYTHONPATH.
# Para um exemplo dentro do pacote, imports relativos ou absolutos do pacote funcionariam
# ao executar como módulo. Assumindo que está no PYTHONPATH:
from jtech_mcp_executor import (
    JtechMCPAgent,
    # JtechMCPClient, # Mocked, não precisa importar o real para este exemplo
    JtechMCPCrew,
    SequentialWorkflow,
    JtechMCPTask,
    AgentMemory
)
from jtech_mcp_executor.connectors.base import BaseConnector # Para type hint do LLM mock

# Mock para um BaseLanguageModel (LangChain)
# Não precisamos de uma implementação real de LLM para este exemplo focado na orquestração.
# O importante é que o JtechMCPAgent possa ser instanciado.
# A classe MockableAgent abaixo vai sobrescrever o método `run` que usa o LLM.
llm_mock_instance = MagicMock(spec=BaseConnector) # Usar BaseConnector ou um mock mais específico de LLM
# Se o construtor do JtechMCPAgent ou seu initialize() depender de atributos/métodos específicos do LLM,
# eles precisariam ser mockados aqui. Por ex: llm_mock_instance.some_attribute = "value"

# Mock para JtechMCPClient
# Similar ao LLM, o MockableAgent.run não usará o client ativamente.
mcp_client_mock = AsyncMock() # Usar AsyncMock se métodos async são chamados
# Simular métodos do client que o JtechMCPAgent pode chamar durante o __init__ ou initialize()
mcp_client_mock.get_all_active_sessions = MagicMock(return_value={})
mcp_client_mock.create_all_sessions = AsyncMock(return_value={"mock_session_id": MagicMock()})
# JtechMCPAgent.initialize() chama adapter.create_tools(self.client), 
# que pode chamar client.get_tools_from_session() ou similar.
# Para o MockableAgent, a inicialização completa pode não ser crítica se o `run` é sobrescrito.
# No entanto, para instanciar JtechMCPAgent, o construtor espera `client` ou `connectors`.
# Se `client` é fornecido, ele será usado.


class MockableAgent(JtechMCPAgent):
    """
    Uma subclasse de JtechMCPAgent que sobrescreve o método `run`
    para simular a execução de tarefas sem depender de um LLM real ou
    de uma infraestrutura de ferramentas MCP complexa.
    Foco na demonstração da lógica de orquestração.
    """
    async def run(self, query: str, max_steps: int | None = None, manage_connector: bool = True, external_history=None, context: dict | None = None) -> str:
        role_name, _ = self.get_role()
        # context pode ser None, então usamos .get() com um default
        current_task_context_str = f"{context}" if context else "{}"
        
        print(f"  [Agente Mock '{role_name}'] Tarefa: '{query[:60]}...'")
        if context:
            print(f"  [Agente Mock '{role_name}'] Contexto recebido: {str(context)[:100]}...")


        # Simular um pequeno atraso para representar o trabalho
        await asyncio.sleep(0.1)

        # Simular output baseado no papel ou na query
        if role_name == "pesquisador":
            return f"Dados pesquisados sobre '{query}': Muitos resultados e artigos encontrados sobre o tema."
        elif role_name == "analista":
            last_output = context.get("last_task_output", "dados não fornecidos") if context else "dados não fornecidos"
            return f"Análise das tendências para '{query}' (baseado em '{last_output[:30]}...'): Tendências mostram crescimento e necessidade de adaptação."
        elif role_name == "redator":
            last_output = context.get("last_task_output", "análise não fornecida") if context else "análise não fornecida"
            return f"Relatório sobre '{query}' (baseado em '{last_output[:30]}...'): O estudo conclui que o impacto é significativo e recomenda ações estratégicas."
        
        return f"Agente '{role_name}' concluiu a tarefa: '{query}' com output genérico."

async def main():
    print("🚀 Iniciando exemplo de orquestração de agentes JTech MCP Executor...")

    # 1. Configuração (LLM e Client Mocks já definidos globalmente)
    # llm_mock_instance e mcp_client_mock

    # 2. Criar agentes especializados usando MockableAgent
    print("\n--- 🧑‍🔧 Criando Agentes Especializados (Mocks) ---")
    pesquisador = MockableAgent(
        llm=llm_mock_instance, 
        client=mcp_client_mock,
        # system_prompt é usado na inicialização real, mas menos crítico para MockableAgent.run
        system_prompt="Você é um especialista em pesquisa de dados.",
        # auto_initialize=False para evitar chamadas a _create_agent se não for necessário.
        # Para MockableAgent, como run é sobrescrito, a inicialização completa do agent original
        # pode não ser estritamente necessária, simplificando o mock.
        # No entanto, JtechMCPCrew.add_agent espera que agent.get_role() funcione.
        auto_initialize=False # Para este exemplo, a inicialização completa do agente não é o foco.
    )
    pesquisador.set_role("pesquisador", "Responsável por pesquisar e coletar dados relevantes.")
    
    analista = MockableAgent(
        llm=llm_mock_instance,
        client=mcp_client_mock,
        system_prompt="Você é um analista de dados sênior.",
        auto_initialize=False
    )
    analista.set_role("analista", "Responsável por analisar os dados coletados e identificar insights.")
    
    redator = MockableAgent(
        llm=llm_mock_instance,
        client=mcp_client_mock,
        system_prompt="Você é um redator técnico especializado.",
        auto_initialize=False
    )
    redator.set_role("redator", "Responsável por compilar análises e dados em relatórios claros.")
    
    print(f"  - Agente '{pesquisador.get_role()[0]}' criado. Desc: {pesquisador.get_role()[1]}")
    print(f"  - Agente '{analista.get_role()[0]}' criado. Desc: {analista.get_role()[1]}")
    print(f"  - Agente '{redator.get_role()[0]}' criado. Desc: {redator.get_role()[1]}")

    # 3. Criar um crew com estes agentes
    print("\n--- 🤝 Criando o Crew de Agentes ---")
    crew_memory = AgentMemory() 
    crew = JtechMCPCrew(
        name="Equipe de Análise de Impacto de IA",
        description="Uma equipe multidisciplinar para analisar e relatar o impacto da IA.",
        agents=[pesquisador, analista, redator],
        shared_memory=crew_memory,
        verbose=True # Habilitar logs do crew/workflow para ver o processo
    )
    print(f"  - Crew '{crew.name}' criado com {len(crew.agents)} agentes.")
    print(f"  - Memória compartilhada inicial do crew: {crew.shared_memory.get_all_memory()}")


    # 4. Definir tarefas para cada agente
    print("\n--- 📝 Definindo Tarefas para o Workflow ---")
    tarefas = [
        JtechMCPTask(
            description="Pesquisar dados atualizados sobre o impacto da Inteligência Artificial na produtividade de desenvolvedores de software.",
            agent_name="pesquisador", # Deve corresponder ao role definido para o agente
            name="PesquisaImpactoIA",
            expected_output="Um resumo dos dados coletados, incluindo fontes e principais estatísticas."
        ),
        JtechMCPTask(
            description="Analisar os dados coletados sobre IA e produtividade, identificando tendências chave, desafios e oportunidades.",
            agent_name="analista",
            name="AnaliseDadosIA",
            context={"foco_da_analise": "ferramentas de IA generativa e seu impacto em TDD"}, # Exemplo de contexto específico
            expected_output="Uma análise detalhada das tendências, com gráficos e pontos chave."
        ),
        JtechMCPTask(
            description="Criar um relatório executivo (1-2 parágrafos) sobre as descobertas da análise de impacto da IA.",
            agent_name="redator",
            name="RedacaoRelatorioIA",
            expected_output="Um relatório conciso e bem escrito, formatado para executivos."
        )
    ]
    for i, t in enumerate(tarefas):
        print(f"  - Tarefa {i+1}: '{t.name}' (Agente: {t.agent_name}) - Desc: '{t.description[:50]}...'")

    # 5. Criar um workflow sequencial
    print("\n--- 🔄 Configurando o Workflow Sequencial ---")
    workflow = SequentialWorkflow(tasks=tarefas)
    print(f"  - Workflow do tipo '{workflow.__class__.__name__}' criado com {len(workflow.tasks)} tarefas.")

    # 6. Executar o workflow
    print("\n--- ▶️ Executando o Workflow ---")
    tarefa_geral_crew = "Elaborar um estudo compreensivo sobre o impacto da IA na produtividade de desenvolvedores."
    
    # Adicionar algo à memória compartilhada do crew antes de começar, para demonstração
    crew.shared_memory.add_memory("meta_estudo_global", "Identificar top 3 ferramentas de IA para devs.")
    print(f"  - Memória do crew antes da execução: {crew.shared_memory.get_all_memory()}")

    resultado_workflow = await crew.run(
        task_description=tarefa_geral_crew,
        workflow=workflow,
        initial_context={"cliente_final": "Diretoria JTech", "prazo": "3 dias"}
    )
    
    print("\n--- ✅ Resultado Final do Workflow ---")
    print(f"  Status Geral: {resultado_workflow.get('status')}")
    if resultado_workflow.get('final_output'):
        print(f"  Output Final Consolidado: {resultado_workflow['final_output']}")
    
    print("\n--- 📋 Detalhes das Tarefas Executadas no Workflow ---")
    for i, task_out in enumerate(resultado_workflow.get("task_outputs", [])):
        print(f"  Resultado Tarefa {i+1}:")
        print(f"    Nome da Tarefa: {task_out.get('task_name')}")
        print(f"    Agente Designado: {task_out.get('agent_name')}")
        print(f"    Status: {task_out.get('status')}")
        if task_out.get('status') == 'CONCLUÍDA':
            print(f"    Output Gerado: {task_out.get('output')[:150]}...") # Limitar output longo
        elif task_out.get('error'):
            print(f"    Erro Ocorrido: {task_out.get('error')}")

    print("\n--- 🧠 Memória Compartilhada Pós-Execução ---")
    # Mostrar como a memória compartilhada foi populada pelo workflow/agentes
    all_shared_mem = crew.shared_memory.get_all_memory()
    print("  Conteúdo da Memória Compartilhada:")
    for key, value in all_shared_mem.items():
        print(f"    - {key}: {str(value)[:100]}...") # Limitar output longo

    # 7. Liberar recursos (simulado, pois os agentes são mocks)
    print("\n--- 🚪 Encerrando o Crew e Agentes ---")
    await crew.close() # Chama o close dos agentes (que são AsyncMock no MockableAgent)
    print("  - Crew e agentes encerrados.")
    
    print("\n🏁 Exemplo de orquestração de agentes concluído! 🏁")

if __name__ == "__main__":
    # Adicionar um handler básico de logging para ver os logs do crew (verbose=True)
    import logging
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(name)s: %(message)s')
    
    asyncio.run(main())

```
