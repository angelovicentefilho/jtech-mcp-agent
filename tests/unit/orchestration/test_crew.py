import pytest
import asyncio # Para testes com async close
from unittest.mock import MagicMock, AsyncMock, patch

# Importações das classes a serem testadas e mockadas
from jtech_mcp_executor.orchestration.crew import JtechMCPCrew
from jtech_mcp_executor.orchestration.task import JtechMCPTask # Não usado diretamente, mas bom para contexto
from jtech_mcp_executor.orchestration.memory import AgentMemory
# Suponha que JtechMCPAgent e Workflows sejam mockados
# from jtech_mcp_executor.agents.mcpagent import JtechMCPAgent (para type hint, mas será mock)
# from jtech_mcp_executor.orchestration.workflow import JtechMCPWorkflow (para type hint, mas será mock)

# Mock para JtechMCPAgent - Usaremos instâncias de MagicMock/AsyncMock nas fixtures
# para maior controle por teste.

@pytest.fixture
def mock_agent_instance() -> MagicMock:
    """Retorna uma instância mock de JtechMCPAgent com papel."""
    agent = MagicMock(name="MockedAgentInstance")
    # Precisa configurar get_role para retornar uma tupla (role, description)
    agent.get_role.return_value = ("test_role_1", "Description for role 1")
    agent.close = AsyncMock() # Método close assíncrono
    # Adicionar o atributo 'role' que é acessado em JtechMCPCrew.close logs
    agent.role = "test_role_1" 
    return agent

@pytest.fixture
def another_mock_agent_instance() -> MagicMock:
    """Retorna outra instância mock de JtechMCPAgent com um papel diferente."""
    agent = MagicMock(name="AnotherMockedAgentInstance")
    agent.get_role.return_value = ("test_role_2", "Description for role 2")
    agent.close = AsyncMock()
    agent.role = "test_role_2"
    return agent

@pytest.fixture
def mock_agent_instance_no_role() -> MagicMock:
    """Retorna uma instância mock de JtechMCPAgent sem papel."""
    agent = MagicMock(name="MockedAgentNoRole")
    agent.get_role.return_value = (None, None)
    agent.role = None # Atributo role também None
    return agent
    
@pytest.fixture
def mock_workflow_instance() -> AsyncMock:
    """Retorna uma instância mock de JtechMCPWorkflow."""
    workflow = AsyncMock(name="MockedWorkflowInstance") # Usar AsyncMock para o método execute
    workflow.execute.return_value = {"result": "workflow executed successfully"}
    return workflow


class TestJtechMCPCrewInitialization:
    def test_crew_creation_basic(self):
        crew = JtechMCPCrew(name="TestCrew", description="A test crew")
        assert crew.name == "TestCrew"
        assert crew.description == "A test crew"
        assert crew.verbose is False
        assert crew.agents == {}
        assert isinstance(crew.shared_memory, AgentMemory)
        # Verifica se uma nova memória foi criada e está vazia
        assert crew.shared_memory.get_all_memory() == {}

    def test_crew_creation_with_agents(self, mock_agent_instance, another_mock_agent_instance):
        # Configurar roles diferentes para os agentes da fixture, se necessário
        mock_agent_instance.get_role.return_value = ("role_init_1", "Init Agent 1")
        another_mock_agent_instance.get_role.return_value = ("role_init_2", "Init Agent 2")
        
        crew = JtechMCPCrew(name="InitCrew", description="Crew with agents", agents=[mock_agent_instance, another_mock_agent_instance])
        assert "role_init_1" in crew.agents
        assert crew.get_agent("role_init_1") == mock_agent_instance
        assert "role_init_2" in crew.agents
        assert crew.get_agent("role_init_2") == another_mock_agent_instance
        assert len(crew.agents) == 2

    def test_crew_creation_with_shared_memory(self):
        custom_memory = AgentMemory()
        custom_memory.add_memory("init_key", "init_val")
        crew = JtechMCPCrew(name="MemCrew", description="Crew with custom memory", shared_memory=custom_memory)
        assert crew.shared_memory == custom_memory
        assert crew.shared_memory.get_memory("init_key") == "init_val"

    def test_crew_verbose_mode(self):
        crew_verbose = JtechMCPCrew(name="VerboseCrew", description="Test verbose", verbose=True)
        assert crew_verbose.verbose is True
        crew_non_verbose = JtechMCPCrew(name="NonVerboseCrew", description="Test non-verbose", verbose=False)
        assert crew_non_verbose.verbose is False


class TestJtechMCPCrewAgentManagement:
    def test_add_agent_success(self, mock_agent_instance):
        crew = JtechMCPCrew(name="AgentAddCrew", description="Test adding agents")
        # mock_agent_instance já tem role "test_role_1" pela fixture
        crew.add_agent(mock_agent_instance)
        assert "test_role_1" in crew.agents
        assert crew.get_agent("test_role_1") == mock_agent_instance

    def test_add_agent_no_role_raises_value_error(self, mock_agent_instance_no_role):
        crew = JtechMCPCrew(name="NoRoleCrew", description="Test no role agent")
        with pytest.raises(ValueError, match="Agente deve ter um papel definido para ser adicionado ao crew."):
            crew.add_agent(mock_agent_instance_no_role)

    def test_add_agent_duplicate_role_raises_value_error(self, mock_agent_instance):
        crew = JtechMCPCrew(name="DuplicateRoleCrew", description="Test duplicate roles")
        # mock_agent_instance já tem role "test_role_1" pela fixture
        crew.add_agent(mock_agent_instance) 
        
        another_agent_same_role = MagicMock(name="AnotherAgentSameRole")
        # Configurar o mesmo role que mock_agent_instance
        another_agent_same_role.get_role.return_value = ("test_role_1", "Another agent, same role desc")
        
        with pytest.raises(ValueError, match="Um agente com o papel 'test_role_1' já existe neste crew."):
            crew.add_agent(another_agent_same_role)

    def test_get_agent_existing(self, mock_agent_instance):
        # mock_agent_instance já tem role "test_role_1" pela fixture
        crew = JtechMCPCrew(name="GetAgentCrew", description="Testing get_agent", agents=[mock_agent_instance])
        retrieved_agent = crew.get_agent("test_role_1")
        assert retrieved_agent == mock_agent_instance

    def test_get_agent_non_existing(self):
        crew = JtechMCPCrew(name="GetNonExistAgentCrew", description="Testing get non-existing agent")
        assert crew.get_agent("non_existent_role") is None


@pytest.mark.asyncio
class TestJtechMCPCrewExecution:
    async def test_run_workflow_calls_workflow_execute(self, mock_workflow_instance, mock_agent_instance):
        # Adicionar um agente ao crew para que o workflow possa (hipoteticamente) usá-lo
        crew = JtechMCPCrew(name="RunCrew", description="Testing run workflow", agents=[mock_agent_instance], verbose=True)
        
        task_desc = "Perform a complex analysis"
        initial_ctx = {"input_data": "some_data"}
        expected_run_result = {"status": "completed", "data": "analysis_done"}
        
        # Configurar o mock do workflow para retornar o resultado esperado
        mock_workflow_instance.execute.return_value = expected_run_result
        
        result = await crew.run(
            task_description=task_desc,
            workflow=mock_workflow_instance,
            initial_context=initial_ctx
        )
        
        # Verificar se workflow.execute foi chamado corretamente
        mock_workflow_instance.execute.assert_awaited_once() # Para métodos async
        
        # Acessar os argumentos da chamada
        # call_args é uma tupla (args, kwargs) ou um objeto CallArgs
        # Para assert_awaited_once_with, os args/kwargs são passados diretamente.
        # Aqui, vamos inspecionar call_args manualmente.
        
        called_args_list = mock_workflow_instance.execute.call_args_list
        assert len(called_args_list) == 1
        call_args = called_args_list[0]
        
        # Os argumentos posicionais (args) e nomeados (kwargs)
        # O método execute do workflow espera (self, crew, task_description, context, shared_memory)
        # Como é um método de instância mockado, o 'self' não é capturado em call_args.kwargs
        # Os argumentos passados para o método mockado começam a partir do segundo parâmetro da definição original.
        
        # No JtechMCPCrew.run:
        # result = await workflow.execute(
        #     crew=self,
        #     task_description=task_description,
        #     context=current_context, # current_context é initial_context + {'task_description': task_description}
        #     shared_memory=self.shared_memory 
        # )
        # Então, os kwargs da chamada ao mock devem ser:
        # {'crew': self, 'task_description': task_description, 'context': current_context, 'shared_memory': self.shared_memory}

        assert call_args.kwargs['crew'] == crew
        assert call_args.kwargs['task_description'] == task_desc
        
        expected_context_for_workflow = initial_ctx.copy()
        if 'task_description' not in expected_context_for_workflow: # Lógica em crew.run
            expected_context_for_workflow['task_description'] = task_desc
        
        assert call_args.kwargs['context'] == expected_context_for_workflow
        assert call_args.kwargs['shared_memory'] == crew.shared_memory # Deve ser a memória do crew
        assert isinstance(call_args.kwargs['shared_memory'], AgentMemory)
        
        # Verificar se o resultado retornado é o esperado
        assert result == expected_run_result

    async def test_crew_close_calls_agents_close(self, mock_agent_instance, another_mock_agent_instance):
        # mock_agent_instance e another_mock_agent_instance são configurados com AsyncMock para 'close'
        # e têm 'role' definido nas fixtures.

        # Agente sem método close (para testar robustez)
        agent3_no_close = MagicMock(name="Agent3NoClose")
        agent3_no_close.get_role.return_value = ("role3_no_close", "d3")
        agent3_no_close.role = "role3_no_close"
        # Remover o atributo 'close' se MagicMock o cria por padrão
        if hasattr(agent3_no_close, 'close'):
            del agent3_no_close.close
            
        # Agente com método close, mas não é corrotina (para testar aviso)
        agent4_sync_close = MagicMock(name="Agent4SyncClose")
        agent4_sync_close.get_role.return_value = ("role4_sync_close", "d4")
        agent4_sync_close.role = "role4_sync_close"
        agent4_sync_close.close = MagicMock() # Método síncrono


        crew = JtechMCPCrew(name="CloseCrew", description="Testing close", agents=[mock_agent_instance, another_mock_agent_instance, agent3_no_close, agent4_sync_close], verbose=True)
        
        # Usar patch para capturar logs
        with patch('jtech_mcp_executor.orchestration.crew.logger') as mock_logger:
            await crew.close()
        
        mock_agent_instance.close.assert_awaited_once()
        another_mock_agent_instance.close.assert_awaited_once()
        
        # Verificar que close síncrono foi chamado
        agent4_sync_close.close.assert_called_once()

        # Verificar se o aviso foi logado para o agente com close síncrono
        warning_found = False
        for call in mock_logger.warning.call_args_list:
            if f"Agente {agent4_sync_close.role or agent4_sync_close.__class__.__name__} possui um método 'close' que não é uma corrotina." in call[0][0]:
                warning_found = True
                break
        assert warning_found, "Aviso para método close síncrono não foi logado."

    async def test_run_workflow_with_empty_initial_context(self, mock_workflow_instance, mock_agent_instance):
        crew = JtechMCPCrew(name="RunEmptyCtxCrew", description="Testing run with empty context", agents=[mock_agent_instance])
        task_desc = "Task with no initial context"
        
        await crew.run(task_description=task_desc, workflow=mock_workflow_instance, initial_context=None)
        
        mock_workflow_instance.execute.assert_awaited_once()
        call_args = mock_workflow_instance.execute.call_args
        
        expected_context = {'task_description': task_desc} # crew.run adiciona task_description
        assert call_args.kwargs['context'] == expected_context

```
