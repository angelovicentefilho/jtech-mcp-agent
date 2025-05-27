import pytest
from jtech_mcp_executor.orchestration.task import JtechMCPTask

def test_create_task_all_parameters():
    """Testa a criação de JtechMCPTask com todos os parâmetros fornecidos."""
    desc = "Test description"
    agent = "TestAgent"
    expected_out = "Expected output"
    ctx = {"key": "value", "another_key": 123}
    task_name = "MyTask"
    tid = "task_001"
    
    task = JtechMCPTask(
        description=desc,
        agent_name=agent,
        expected_output=expected_out,
        context=ctx,
        name=task_name,
        task_id=tid
    )
    
    assert task.description == desc
    assert task.agent_name == agent
    assert task.expected_output == expected_out
    assert task.context == ctx
    assert task.name == task_name
    assert task.task_id == tid

def test_create_task_defaults():
    """Testa a criação de JtechMCPTask com parâmetros opcionais ausentes."""
    desc = "Another task description for default checks"
    agent = "AgentSmith"
    
    task = JtechMCPTask(description=desc, agent_name=agent)
    
    assert task.description == desc
    assert task.agent_name == agent
    assert task.expected_output is None
    assert task.context == {} # Deve ser um dict vazio por padrão
    assert task.name is None
    assert task.task_id is None

def test_task_context_initialization_and_isolation():
    """
    Testa se o contexto é um novo dicionário quando não fornecido
    e se os contextos de diferentes tarefas são isolados.
    """
    task1 = JtechMCPTask(description="d1", agent_name="a1")
    task2 = JtechMCPTask(description="d2", agent_name="a2")
    
    # Verifica se os contextos são dicionários vazios
    assert task1.context == {}
    assert task2.context == {}
    
    # Garante que são instâncias diferentes de dicionário
    assert id(task1.context) != id(task2.context), "Contexts should be different dictionary instances"

    # Modificando o contexto de uma tarefa não deve afetar a outra
    task1.context["data"] = 123
    task1.context["shared_info"] = "task1_specific"
    
    assert task1.context == {"data": 123, "shared_info": "task1_specific"}
    assert task2.context == {}, "Context of task2 should remain empty"

def test_task_context_provided_is_used():
    """Testa se o contexto fornecido no construtor é usado e não uma cópia inicial."""
    initial_context = {"initial_key": "initial_value"}
    task = JtechMCPTask(description="d", agent_name="a", context=initial_context)
    
    assert task.context == initial_context
    # Verifica se é a mesma instância (o comportamento padrão é usar a referência)
    assert id(task.context) == id(initial_context) 

    # Modificar o dicionário original DEPOIS de passar para o construtor
    # deve refletir na tarefa, pois é uma referência.
    initial_context["new_key"] = "new_value"
    assert task.context["new_key"] == "new_value"

def test_task_optional_parameters_can_be_none_explicitly():
    """Testa se parâmetros opcionais podem ser explicitamente None."""
    task = JtechMCPTask(
        description="Test None explicitly",
        agent_name="AgentNull",
        expected_output=None,
        context=None, # Se context é None, deve ser inicializado como {}
        name=None,
        task_id=None
    )
    assert task.expected_output is None
    assert task.context == {} # Comportamento esperado: context=None -> self.context = {}
    assert task.name is None
    assert task.task_id is None

# Adicionar mais testes pode ser útil, como verificar os tipos dos atributos,
# mas o foco principal é a instanciação e valores padrão.
# Exemplo:
# def test_task_attribute_types():
#     task = JtechMCPTask(description="Type check", agent_name="TypeAgent")
#     assert isinstance(task.description, str)
#     assert isinstance(task.agent_name, str)
#     assert isinstance(task.context, dict)
#     # etc. para outros atributos
# Este tipo de teste é mais útil em linguagens sem tipagem estática forte
# ou quando há conversões complexas, mas pode ser bom para robustez.
# Para este caso, os testes de instanciação já cobrem implicitamente os tipos básicos.
