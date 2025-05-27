import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, call, patch # call para verificar chamadas múltiplas

# Classes a serem testadas
from jtech_mcp_executor.orchestration.workflow import (
    SequentialWorkflow, ParallelWorkflow, HierarchicalWorkflow, JtechMCPWorkflow
)
# Classes a serem mockadas
from jtech_mcp_executor.orchestration.task import JtechMCPTask
from jtech_mcp_executor.orchestration.memory import AgentMemory
from jtech_mcp_executor.orchestration.aggregator import ResultAggregator
# from jtech_mcp_executor.agents.mcpagent import JtechMCPAgent (para type hint, mas será mock)
# from jtech_mcp_executor.orchestration.crew import JtechMCPCrew (para type hint, mas será mock)

# --- Mocks Globais e Fixtures ---
@pytest.fixture
def mock_crew():
    crew = MagicMock(name="MockCrew")
    crew.verbose = False 
    crew.name = "TestCrewName" # Adicionado para mensagens de erro
    crew.get_agent = MagicMock()
    # A memória compartilhada do crew é passada para workflow.execute
    crew.shared_memory = AgentMemory() 
    # Limpar a memória do crew antes de cada teste que a usa
    crew.shared_memory.clear_memory()
    return crew

@pytest.fixture
def mock_agent(name="MockAgent"):
    agent = AsyncMock(name=name) 
    agent.run = AsyncMock()
    # Adicionar o atributo 'role' para logs no workflow hierárquico
    agent.role = name 
    return agent

@pytest.fixture
def mock_llm_client(): # Para ResultAggregator.summarize
    client = MagicMock(name="MockLLMClient")
    client.summarize = MagicMock(return_value="Summary from LLM")
    return client

# --- Testes para SequentialWorkflow ---
@pytest.mark.asyncio
class TestSequentialWorkflow:
    async def test_sequential_empty_tasks(self, mock_crew):
        workflow = SequentialWorkflow(tasks=[])
        # A implementação atual do SequentialWorkflow não define 'final_output' se não houver tarefas.
        # O resultado esperado deve ser ajustado para corresponder à lógica real.
        results = await workflow.execute(mock_crew, "Test empty sequential", {}, mock_crew.shared_memory)
        
        assert results["status"] == "CONCLUÍDO"
        assert not results["task_outputs"]
        # De acordo com a implementação de SequentialWorkflow:
        # elif not final_results["task_outputs"]:
        #      final_results['final_output'] = "Nenhuma tarefa foi executada."
        assert results.get("final_output") == "Nenhuma tarefa foi executada."


    async def test_sequential_successful_execution(self, mock_crew):
        task1_desc = "Do step 1"
        task2_desc = "Do step 2 based on step 1"
        
        # Usar AsyncMock para o agent.run
        agent_A = AsyncMock(name="AgentA_Sequential")
        agent_A.run = AsyncMock(side_effect=["Output from task 1", "Output from task 2"])

        mock_task1 = MagicMock(spec=JtechMCPTask)
        mock_task1.description = task1_desc
        mock_task1.agent_name = "agent_A"
        mock_task1.context = None
        mock_task1.name = "Task1"
        mock_task1.task_id = "seq_task_001" # Adicionado para teste de shared_memory

        mock_task2 = MagicMock(spec=JtechMCPTask)
        mock_task2.description = task2_desc
        mock_task2.agent_name = "agent_A" 
        mock_task2.context = {"extra_param_for_task2": "value"} # Testar contexto específico da tarefa
        mock_task2.name = "Task2"
        mock_task2.task_id = "seq_task_002" # Adicionado

        mock_crew.get_agent.return_value = agent_A
        
        workflow = SequentialWorkflow(tasks=[mock_task1, mock_task2])
        initial_workflow_context = {"global_param": "global_value"}
        results = await workflow.execute(mock_crew, "Test successful sequence", initial_workflow_context, mock_crew.shared_memory)
        
        assert results["status"] == "CONCLUÍDO"
        assert len(results["task_outputs"]) == 2
        assert results["task_outputs"][0]["output"] == "Output from task 1"
        assert results["task_outputs"][1]["output"] == "Output from task 2"
        assert results["final_output"] == "Output from task 2"
        
        assert agent_A.run.call_count == 2
        first_call_args = agent_A.run.call_args_list[0]
        second_call_args = agent_A.run.call_args_list[1]
        
        assert first_call_args.kwargs["query"] == task1_desc
        assert first_call_args.kwargs["context"]["global_param"] == "global_value" # Contexto inicial do workflow
        assert "extra_param_for_task2" not in first_call_args.kwargs["context"] # Contexto da Task2 não deve estar na Task1

        assert second_call_args.kwargs["query"] == task2_desc
        assert second_call_args.kwargs["context"]["last_task_output"] == "Output from task 1"
        assert second_call_args.kwargs["context"]["global_param"] == "global_value" # Contexto inicial propagado
        assert second_call_args.kwargs["context"]["extra_param_for_task2"] == "value" # Contexto específico da Task2

        # Verificar shared_memory
        assert mock_crew.shared_memory.get_memory("task_seq_task_001_output") == "Output from task 1"
        assert mock_crew.shared_memory.get_memory("task_seq_task_002_output") == "Output from task 2"
        assert mock_crew.shared_memory.get_memory("agent_agent_A_last_output") == "Output from task 2" # Sobrescreve

    async def test_sequential_agent_not_found(self, mock_crew):
        mock_task1 = MagicMock(spec=JtechMCPTask, description="Task with missing agent", agent_name="missing_agent", context=None, name="T1_missing", task_id="t1m")
        mock_crew.get_agent.return_value = None 

        workflow = SequentialWorkflow(tasks=[mock_task1])
        results = await workflow.execute(mock_crew, "Test missing agent", {}, mock_crew.shared_memory)

        assert results["status"] == "FALHOU"
        assert "Agente 'missing_agent' não encontrado" in results["error"]
        # A implementação atual adiciona a tarefa à lista de outputs mesmo se o setup falhar
        assert len(results["task_outputs"]) == 1 
        assert results["task_outputs"][0]["status"] == "FALHOU_SETUP"

    async def test_sequential_task_failure(self, mock_crew):
        agent_A = AsyncMock(name="AgentA_Sequential_Fail")
        agent_A.run = AsyncMock(side_effect=["Success output", Exception("Task failed miserably")])

        mock_task1 = MagicMock(spec=JtechMCPTask, description="Successful task", agent_name="agent_A", context=None, name="T1_ok", task_id="t1ok")
        mock_task_fails = MagicMock(spec=JtechMCPTask, description="Failing task", agent_name="agent_A", context=None, name="T2_fail", task_id="t2fail")

        mock_crew.get_agent.return_value = agent_A

        workflow = SequentialWorkflow(tasks=[mock_task1, mock_task_fails])
        results = await workflow.execute(mock_crew, "Test task failure", {}, mock_crew.shared_memory)

        assert results["status"] == "FALHOU"
        assert "Erro ao executar a tarefa 'Failing task'" in results["error"] # Ou o nome da tarefa, 'T2_fail'
        assert len(results["task_outputs"]) == 2 
        assert results["task_outputs"][0]["status"] == "CONCLUÍDA"
        assert results["task_outputs"][0]["output"] == "Success output"
        assert results["task_outputs"][1]["status"] == "FALHOU"
        assert "Task failed miserably" in results["task_outputs"][1]["error"]
        
        # Verificar shared_memory para a tarefa bem-sucedida
        assert mock_crew.shared_memory.get_memory("task_t1ok_output") == "Success output"
        # Verificar que não há output para a tarefa que falhou na shared_memory
        assert mock_crew.shared_memory.get_memory("task_t2fail_output") is None


# --- Testes para ParallelWorkflow ---
@pytest.mark.asyncio
class TestParallelWorkflow:
    async def test_parallel_empty_tasks(self, mock_crew):
        workflow = ParallelWorkflow(tasks=[])
        results = await workflow.execute(mock_crew, "Test empty parallel", {}, mock_crew.shared_memory)
        assert results["status"] == "CONCLUÍDO_SEM_TAREFAS" # Status específico da implementação
        assert not results["task_outputs"]
        assert results["aggregated_output"] == "Nenhuma tarefa para executar."

    async def test_parallel_successful_execution_no_aggregator(self, mock_crew):
        agent_A = AsyncMock(name="AgentA_Parallel")
        agent_A.run = AsyncMock(return_value="Output A")
        agent_B = AsyncMock(name="AgentB_Parallel")
        agent_B.run = AsyncMock(return_value="Output B")

        mock_task_A = MagicMock(spec=JtechMCPTask, description="Parallel Task A", agent_name="agent_A", context=None, name="PTA", task_id="ptA")
        mock_task_B = MagicMock(spec=JtechMCPTask, description="Parallel Task B", agent_name="agent_B", context=None, name="PTB", task_id="ptB")

        def side_effect_get_agent(agent_name_or_role):
            if agent_name_or_role == "agent_A": return agent_A
            if agent_name_or_role == "agent_B": return agent_B
            return None
        mock_crew.get_agent.side_effect = side_effect_get_agent
        
        workflow = ParallelWorkflow(tasks=[mock_task_A, mock_task_B], result_aggregator=None)
        results = await workflow.execute(mock_crew, "Test parallel success no aggregation", {"global_ctx": "parallel_val"}, mock_crew.shared_memory)
        
        assert results["status"] == "CONCLUÍDO"
        assert len(results["task_outputs"]) == 2
        
        # Os outputs individuais estarão em results["task_outputs"]
        # A ordem em asyncio.gather pode variar se as tarefas tiverem durações diferentes.
        # Mas aqui, como são mocks rápidos, a ordem tende a ser a de adição.
        # Para robustez, vamos buscar pelos nomes.
        output_dict = {r["task_name"]: r["output"] for r in results["task_outputs"] if r["status"] == "CONCLUÍDA"}
        assert output_dict.get("PTA") == "Output A"
        assert output_dict.get("PTB") == "Output B"
        
        # aggregated_output será uma lista dos outputs na ordem de conclusão (ou adição para mocks rápidos)
        assert isinstance(results["aggregated_output"], list)
        assert "Output A" in results["aggregated_output"]
        assert "Output B" in results["aggregated_output"]
        assert len(results["aggregated_output"]) == 2

        # Verificar shared_memory
        assert mock_crew.shared_memory.get_memory("parallel_task_ptA_output") == "Output A"
        assert mock_crew.shared_memory.get_memory("parallel_task_ptB_output") == "Output B"

        # Verificar que o contexto do workflow foi passado para as tarefas
        agent_A.run.assert_called_once()
        agent_B.run.assert_called_once()
        assert agent_A.run.call_args.kwargs["context"]["global_ctx"] == "parallel_val"
        assert agent_B.run.call_args.kwargs["context"]["global_ctx"] == "parallel_val"


    async def test_parallel_with_concatenation_aggregator(self, mock_crew):
        agent_A = AsyncMock(name="AgentA_Concat")
        agent_A.run = AsyncMock(return_value="First line.")
        agent_B = AsyncMock(name="AgentB_Concat")
        agent_B.run = AsyncMock(return_value="Second line.")

        mock_task_A = MagicMock(spec=JtechMCPTask, description="Concat Task A", agent_name="agent_A", context=None, name="CTA", task_id="cta")
        mock_task_B = MagicMock(spec=JtechMCPTask, description="Concat Task B", agent_name="agent_B", context=None, name="CTB", task_id="ctb")
        
        def side_effect_get_agent(agent_name_or_role):
            if agent_name_or_role == "agent_A": return agent_A
            if agent_name_or_role == "agent_B": return agent_B
            return None
        mock_crew.get_agent.side_effect = side_effect_get_agent

        workflow = ParallelWorkflow(tasks=[mock_task_A, mock_task_B], result_aggregator=ResultAggregator.concatenate)
        results = await workflow.execute(mock_crew, "Test parallel concat", {}, mock_crew.shared_memory)

        assert results["status"] == "CONCLUÍDO"
        # O ResultAggregator.concatenate simplesmente junta as strings na ordem que recebe.
        # A ordem dos resultados de asyncio.gather corresponde à ordem das coroutines na lista de entrada.
        expected_aggregated_output = "First line.\nSecond line."
        assert results["aggregated_output"] == expected_aggregated_output

    async def test_parallel_with_summarize_aggregator(self, mock_crew, mock_llm_client):
        agent_A = AsyncMock(name="AgentA_Summ")
        agent_A.run = AsyncMock(return_value="Detail one about topic X.")
        agent_B = AsyncMock(name="AgentB_Summ")
        agent_B.run = AsyncMock(return_value="Detail two about topic X.")

        mock_task_A = MagicMock(spec=JtechMCPTask, description="Summary Task A", agent_name="agent_A", context=None, name="STA", task_id="sta")
        mock_task_B = MagicMock(spec=JtechMCPTask, description="Summary Task B", agent_name="agent_B", context=None, name="STB", task_id="stb")
        
        def side_effect_get_agent(agent_name_or_role):
            if agent_name_or_role == "agent_A": return agent_A
            if agent_name_or_role == "agent_B": return agent_B
            return None
        mock_crew.get_agent.side_effect = side_effect_get_agent
        
        # Patch ResultAggregator.summarize para não fazer chamada LLM real, ou usar mock_llm_client se o summarize o usa
        # A implementação atual do ResultAggregator.summarize é um placeholder que não usa o llm_client
        # e concatena. Vamos testar esse comportamento.
        
        workflow_task_desc = "Summarize Topic X"
        workflow = ParallelWorkflow(
            tasks=[mock_task_A, mock_task_B], 
            result_aggregator=ResultAggregator.summarize,
            task_description_for_aggregator=workflow_task_desc # Passando para o summarize
        )
        results = await workflow.execute(mock_crew, workflow_task_desc, {}, mock_crew.shared_memory)

        assert results["status"] == "CONCLUÍDO"
        expected_summary = f"Resumo para a tarefa '{workflow_task_desc}':\nDetail one about topic X.\nDetail two about topic X."
        assert results["aggregated_output"] == expected_summary


    async def test_parallel_task_failure(self, mock_crew):
        agent_A = AsyncMock(name="AgentA_FailParallel")
        agent_A.run = AsyncMock(return_value="Success A")
        agent_B_fails = AsyncMock(name="AgentB_FailParallel")
        agent_B_fails.run = AsyncMock(side_effect=Exception("B failed"))

        mock_task_A = MagicMock(spec=JtechMCPTask, description="Parallel OK", agent_name="agent_A", context=None, name="PF_A", task_id="pfa")
        mock_task_B_fails = MagicMock(spec=JtechMCPTask, description="Parallel Fail", agent_name="agent_B_fails", context=None, name="PF_B", task_id="pfb")

        def side_effect_get_agent(agent_name_or_role):
            if agent_name_or_role == "agent_A": return agent_A
            if agent_name_or_role == "agent_B_fails": return agent_B_fails
            return None
        mock_crew.get_agent.side_effect = side_effect_get_agent

        workflow = ParallelWorkflow(tasks=[mock_task_A, mock_task_B_fails])
        results = await workflow.execute(mock_crew, "Test parallel one fails", {}, mock_crew.shared_memory)

        assert results["status"] == "CONCLUÍDO_COM_FALHAS"
        assert "1 tarefa(s) falharam" in results["error"]
        assert len(results["task_outputs"]) == 2
        
        output_A = next(r for r in results["task_outputs"] if r["task_name"] == "PF_A")
        output_B = next(r for r in results["task_outputs"] if r["task_name"] == "PF_B")

        assert output_A["status"] == "CONCLUÍDA"
        assert output_A["output"] == "Success A"
        assert output_B["status"] == "FALHOU"
        assert "B failed" in output_B["error"]
        
        assert results["aggregated_output"] == ["Success A"] # Só o resultado da tarefa bem-sucedida

    async def test_parallel_agent_not_found(self, mock_crew):
        mock_task_A = MagicMock(spec=JtechMCPTask, description="Task with found agent", agent_name="agent_A", context=None, name="PT_Found", task_id="ptf")
        mock_task_B_missing = MagicMock(spec=JtechMCPTask, description="Task with missing agent", agent_name="missing_agent", context=None, name="PT_Missing", task_id="ptm")
        
        agent_A = AsyncMock(name="AgentA_Parallel_Found")
        agent_A.run = AsyncMock(return_value="Output A")

        def side_effect_get_agent(agent_name_or_role):
            if agent_name_or_role == "agent_A": return agent_A
            if agent_name_or_role == "missing_agent": return None
            return None # Default
        mock_crew.get_agent.side_effect = side_effect_get_agent

        workflow = ParallelWorkflow(tasks=[mock_task_A, mock_task_B_missing])
        results = await workflow.execute(mock_crew, "Test parallel agent not found", {}, mock_crew.shared_memory)

        assert results["status"] == "CONCLUÍDO_COM_FALHAS"
        assert "1 tarefa(s) falharam" in results["error"] # FALHOU_SETUP é uma falha
        assert len(results["task_outputs"]) == 2
        
        output_A = next(r for r in results["task_outputs"] if r["task_name"] == "PT_Found")
        output_B_missing = next(r for r in results["task_outputs"] if r["task_name"] == "PT_Missing")

        assert output_A["status"] == "CONCLUÍDA"
        assert output_A["output"] == "Output A"
        assert output_B_missing["status"] == "FALHOU_SETUP"
        assert "Agente 'missing_agent' não encontrado" in output_B_missing["error"]
        
        assert results["aggregated_output"] == ["Output A"]


# --- Testes para HierarchicalWorkflow ---
@pytest.mark.asyncio
class TestHierarchicalWorkflow:
    async def test_hierarchical_max_iterations_reached(self, mock_crew):
        supervisor_agent = AsyncMock(name="Supervisor")
        supervisor_agent.run = AsyncMock(return_value="Delegate to worker_A: Do something.")
        
        worker_agent = AsyncMock(name="WorkerA")
        worker_agent.run = AsyncMock(return_value="Worker A did something.")

        mock_crew.get_agent.side_effect = lambda name: supervisor_agent if name == "supervisor" else (worker_agent if name == "worker_A" else None)

        max_iters = 2
        workflow = HierarchicalWorkflow(
            supervisor_agent_name="supervisor",
            worker_agent_names=["worker_A"],
            max_iterations=max_iters
        )
        results = await workflow.execute(mock_crew, "Test max iterations", {}, mock_crew.shared_memory)
        
        assert results["status"] == "MAX_ITERATIONS_REACHED"
        assert len(results["history"]) == max_iters 
        assert supervisor_agent.run.call_count == max_iters
        assert worker_agent.run.call_count == max_iters # Dada delegação simples para worker_A
        assert results["final_output"] == "Delegate to worker_A: Do something." 

        # Verificar shared_memory
        for i in range(1, max_iters + 1):
            assert mock_crew.shared_memory.get_memory(f"hierarchical_supervisor_iter_{i}_output") == "Delegate to worker_A: Do something."
            assert mock_crew.shared_memory.get_memory(f"hierarchical_worker_worker_A_iter_{i}_output") == "Worker A did something."


    async def test_hierarchical_supervisor_completes_task(self, mock_crew):
        supervisor_agent = AsyncMock(name="Supervisor")
        supervisor_agent.run.side_effect = [
            "Delegate to worker_A: Initial task.", 
            "Work from worker_A is good. CONCLUÍDO: Final report."
        ]
        
        worker_agent = AsyncMock(name="WorkerA")
        worker_agent.run = AsyncMock(return_value="Worker A initial result.")

        mock_crew.get_agent.side_effect = lambda name: supervisor_agent if name == "supervisor" else (worker_agent if name == "worker_A" else None)

        workflow = HierarchicalWorkflow(
            supervisor_agent_name="supervisor",
            worker_agent_names=["worker_A"],
            max_iterations=3
        )
        results = await workflow.execute(mock_crew, "Test supervisor completes", {"initial_ctx_hier": "val"}, mock_crew.shared_memory)

        assert results["status"] == "CONCLUÍDO"
        assert results["final_output"] == "Work from worker_A is good. CONCLUÍDO: Final report."
        assert len(results["history"]) == 2 
        assert supervisor_agent.run.call_count == 2
        assert worker_agent.run.call_count == 1 
        
        # Verificar shared_memory
        assert mock_crew.shared_memory.get_memory("hierarchical_supervisor_iter_1_output") == "Delegate to worker_A: Initial task."
        assert mock_crew.shared_memory.get_memory("hierarchical_worker_worker_A_iter_1_output") == "Worker A initial result."
        assert mock_crew.shared_memory.get_memory("hierarchical_supervisor_iter_2_output") == "Work from worker_A is good. CONCLUÍDO: Final report."
        
        # Verificar que o contexto inicial foi passado para o supervisor e worker
        supervisor_first_call_ctx = supervisor_agent.run.call_args_list[0].kwargs['context']
        worker_first_call_ctx = worker_agent.run.call_args_list[0].kwargs['context']
        assert supervisor_first_call_ctx['initial_ctx_hier'] == "val"
        assert worker_first_call_ctx['initial_ctx_hier'] == "val"


    async def test_hierarchical_supervisor_not_found(self, mock_crew):
        mock_crew.get_agent.return_value = None 
        workflow = HierarchicalWorkflow("missing_supervisor", ["worker_A"])
        results = await workflow.execute(mock_crew, "Test missing supervisor", {}, mock_crew.shared_memory)
        assert results["status"] == "FALHOU_SETUP" # Corrigido para o status correto
        assert "Agente supervisor 'missing_supervisor' não encontrado" in results["error"]

    async def test_hierarchical_worker_not_found(self, mock_crew):
        supervisor_agent = AsyncMock(name="Supervisor")
        mock_crew.get_agent.side_effect = lambda name: supervisor_agent if name == "supervisor" else None 
        
        workflow = HierarchicalWorkflow("supervisor", ["missing_worker"])
        results = await workflow.execute(mock_crew, "Test missing worker", {}, mock_crew.shared_memory)
        assert results["status"] == "FALHOU_SETUP" # Corrigido
        assert "Agente trabalhador 'missing_worker' não encontrado" in results["error"]

    async def test_hierarchical_supervisor_fails_during_iteration(self, mock_crew):
        supervisor_agent = AsyncMock(name="Supervisor")
        supervisor_agent.run.side_effect = Exception("Supervisor crashed")
        
        worker_agent = AsyncMock(name="WorkerA") 
        
        mock_crew.get_agent.side_effect = lambda name: supervisor_agent if name == "supervisor" else (worker_agent if name == "worker_A" else None)

        workflow = HierarchicalWorkflow("supervisor", ["worker_A"])
        results = await workflow.execute(mock_crew, "Supervisor fails", {}, mock_crew.shared_memory)

        assert results["status"] == "FALHOU"
        assert "Erro na iteração 1: Supervisor crashed" in results["error"]
        assert len(results["history"]) == 1 
        assert "error" in results["history"][0]
        assert results["final_output"] == "Workflow não produziu um output final do supervisor." # Valor padrão

    async def test_hierarchical_worker_fails_during_delegation(self, mock_crew):
        supervisor_agent = AsyncMock(name="Supervisor")
        supervisor_agent.run.return_value = "Delegate to worker_A: Do this critical task." # Supervisor delega para worker_A
        
        worker_agent = AsyncMock(name="WorkerA")
        worker_agent.run.side_effect = Exception("Worker A exploded")

        mock_crew.get_agent.side_effect = lambda name: supervisor_agent if name == "supervisor" else (worker_agent if name == "worker_A" else None)

        workflow = HierarchicalWorkflow("supervisor", ["worker_A"], max_iterations=2) # Limitar iterações para o teste
        results = await workflow.execute(mock_crew, "Worker fails", {}, mock_crew.shared_memory)
        
        assert results["status"] == "MAX_ITERATIONS_REACHED" 
        assert len(results["history"]) == 2 # Deve rodar 2 iterações
        
        # Iteração 1: Supervisor OK, Worker Falha
        iter1_history = results["history"][0]
        assert iter1_history["supervisor_action"] == "Delegate to worker_A: Do this critical task."
        assert len(iter1_history["worker_results"]) == 1
        assert iter1_history["worker_results"][0]["agent_name"] == "worker_A"
        assert "Worker A exploded" in iter1_history["worker_results"][0]["error"]
        
        # Iteração 2: Supervisor é chamado novamente, recebe o erro do worker
        supervisor_call_iter2 = supervisor_agent.run.call_args_list[1]
        prompt_iter2 = supervisor_call_iter2.kwargs['query'] # query é o nome do param no agent.run
        assert "Trabalhador worker_A FALHOU: Worker A exploded" in prompt_iter2
        assert results["final_output"] == "Delegate to worker_A: Do this critical task." # Última ação bem sucedida do supervisor

    async def test_hierarchical_supervisor_delegates_to_all_workers(self, mock_crew):
        supervisor_agent = AsyncMock(name="Supervisor")
        # Supervisor não menciona nenhum worker específico
        supervisor_agent.run.return_value = "General instruction for all workers."

        worker_A = AsyncMock(name="WorkerA")
        worker_A.run = AsyncMock(return_value="Worker A processed general instruction.")
        worker_B = AsyncMock(name="WorkerB")
        worker_B.run = AsyncMock(return_value="Worker B processed general instruction.")

        def get_agent_side_effect(agent_name):
            if agent_name == "supervisor": return supervisor_agent
            if agent_name == "worker_A": return worker_A
            if agent_name == "worker_B": return worker_B
            return None
        mock_crew.get_agent.side_effect = get_agent_side_effect

        workflow = HierarchicalWorkflow(
            supervisor_agent_name="supervisor",
            worker_agent_names=["worker_A", "worker_B"],
            max_iterations=1 # Apenas uma iteração para simplificar
        )
        results = await workflow.execute(mock_crew, "Test delegation to all", {}, mock_crew.shared_memory)

        assert results["status"] == "MAX_ITERATIONS_REACHED" # Porque max_iterations=1 e não houve "CONCLUÍDO"
        assert len(results["history"]) == 1
        iter1_history = results["history"][0]
        assert iter1_history["supervisor_action"] == "General instruction for all workers."
        assert len(iter1_history["worker_tasks_delegated"]) == 2 # Delegado para ambos
        assert len(iter1_history["worker_results"]) == 2
        
        worker_A.run.assert_called_once_with(query="General instruction for all workers.", context=unittest.mock.ANY)
        worker_B.run.assert_called_once_with(query="General instruction for all workers.", context=unittest.mock.ANY)

        worker_outputs_in_history = sorted([res["output"] for res in iter1_history["worker_results"]])
        assert worker_outputs_in_history == ["Worker A processed general instruction.", "Worker B processed general instruction."]
```

**Note**: Added `unittest.mock.ANY` in the last assertion for context, as it can become complex to match exactly.
