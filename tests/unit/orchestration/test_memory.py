import pytest
from jtech_mcp_executor.orchestration.memory import AgentMemory

@pytest.fixture
def empty_memory() -> AgentMemory:
    """Fixture que retorna uma instância vazia de AgentMemory."""
    return AgentMemory()

@pytest.fixture
def populated_memory() -> AgentMemory:
    """Fixture que retorna uma AgentMemory com alguns dados."""
    memory = AgentMemory()
    memory.add_memory("key1", "value1")
    memory.add_memory("key2", 123)
    memory.add_memory("key3", {"nested_key": "nested_value"})
    return memory

def test_initialization(empty_memory: AgentMemory):
    """Testa se AgentMemory é inicializado vazio."""
    assert empty_memory.get_all_memory() == {}
    # Também podemos verificar o atributo interno se a API não for suficiente,
    # mas get_all_memory() é a forma preferencial de verificar o estado.
    assert empty_memory._memory == {}

def test_add_memory_new_item(empty_memory: AgentMemory):
    """Testa adicionar um novo item à memória."""
    empty_memory.add_memory("test_key", "test_value")
    assert empty_memory.get_memory("test_key") == "test_value"
    assert len(empty_memory.get_all_memory()) == 1
    assert empty_memory.get_all_memory() == {"test_key": "test_value"}

def test_add_memory_overwrite_item(populated_memory: AgentMemory):
    """Testa sobrescrever um item existente na memória."""
    # Verifica o valor original para garantir que a fixture está como esperado
    assert populated_memory.get_memory("key1") == "value1"
    
    populated_memory.add_memory("key1", "new_value1")
    assert populated_memory.get_memory("key1") == "new_value1"
    # O número de chaves não deve mudar
    assert len(populated_memory.get_all_memory()) == 3 

def test_get_memory_existing_item(populated_memory: AgentMemory):
    """Testa obter um item existente."""
    assert populated_memory.get_memory("key1") == "value1"
    assert populated_memory.get_memory("key2") == 123
    assert populated_memory.get_memory("key3") == {"nested_key": "nested_value"}

def test_get_memory_non_existing_item(populated_memory: AgentMemory):
    """Testa obter um item que não existe (deve retornar None)."""
    assert populated_memory.get_memory("non_existent_key") is None

def test_get_all_memory_content(populated_memory: AgentMemory):
    """Testa se get_all_memory retorna todos os itens corretamente."""
    all_mem = populated_memory.get_all_memory()
    expected_mem = {
        "key1": "value1",
        "key2": 123,
        "key3": {"nested_key": "nested_value"}
    }
    assert all_mem == expected_mem
    assert len(all_mem) == 3

def test_get_all_memory_is_copy(populated_memory: AgentMemory):
    """Testa se get_all_memory retorna uma cópia e não a referência interna."""
    all_mem_copy = populated_memory.get_all_memory()
    
    # Verifica se são instâncias diferentes de dicionário
    # Acessar _memory é para fins de teste para confirmar a cópia.
    # Em um cenário ideal, não acessaríamos atributos privados, mas para
    # garantir a não-mutabilidade externa, é um teste válido.
    assert id(all_mem_copy) != id(populated_memory._memory)
    
    # Modificar a cópia não deve afetar o original
    all_mem_copy["new_key_in_copy"] = "data_in_copy"
    
    # Verifica se a memória original não foi alterada
    original_memory_after_modification = populated_memory.get_all_memory()
    assert "new_key_in_copy" not in original_memory_after_modification
    assert len(original_memory_after_modification) == 3 # O tamanho original deve ser mantido

    # Também verifica diretamente o atributo interno (para robustez do teste)
    assert "new_key_in_copy" not in populated_memory._memory


def test_clear_memory(populated_memory: AgentMemory):
    """Testa limpar todos os itens da memória."""
    # Garante que não está vazia antes de limpar
    assert len(populated_memory.get_all_memory()) == 3 
    
    populated_memory.clear_memory()
    
    assert populated_memory.get_all_memory() == {}
    assert len(populated_memory.get_all_memory()) == 0
    assert populated_memory._memory == {} # Verifica também o atributo interno

def test_remove_memory_existing_item(populated_memory: AgentMemory):
    """Testa remover um item existente."""
    # Garante que o item existe
    assert populated_memory.get_memory("key1") == "value1"
    initial_size = len(populated_memory.get_all_memory()) # Should be 3
    
    populated_memory.remove_memory("key1")
    
    assert populated_memory.get_memory("key1") is None
    assert "key1" not in populated_memory.get_all_memory()
    assert len(populated_memory.get_all_memory()) == initial_size - 1 # Tamanho deve diminuir
    assert "key1" not in populated_memory._memory # Verifica o atributo interno

def test_remove_memory_non_existing_item(populated_memory: AgentMemory):
    """Testa remover um item que não existe (não deve dar erro)."""
    initial_size = len(populated_memory.get_all_memory()) # Should be 3
    key_to_remove = "non_existent_key"

    # Garante que a chave realmente não existe
    assert populated_memory.get_memory(key_to_remove) is None
    
    try:
        populated_memory.remove_memory(key_to_remove)
    except KeyError: # Ou qualquer outra exceção que não deveria ser levantada
        pytest.fail(f"Remover chave '{key_to_remove}' inexistente não deve levantar exceção.")
    
    # Garante que nada mudou se a chave não existia
    assert len(populated_memory.get_all_memory()) == initial_size
    # Verifica se o estado do dicionário original permaneceu o mesmo
    expected_mem = {
        "key1": "value1",
        "key2": 123,
        "key3": {"nested_key": "nested_value"}
    }
    assert populated_memory.get_all_memory() == expected_mem

def test_remove_memory_on_empty_memory(empty_memory: AgentMemory):
    """Testa remover um item de uma memória vazia (não deve dar erro)."""
    initial_size = len(empty_memory.get_all_memory()) # Should be 0
    key_to_remove = "any_key"
    
    try:
        empty_memory.remove_memory(key_to_remove)
    except KeyError:
        pytest.fail(f"Remover chave '{key_to_remove}' de memória vazia não deve levantar exceção.")
        
    assert len(empty_memory.get_all_memory()) == initial_size # Deve continuar 0
    assert empty_memory.get_all_memory() == {}

# Testes adicionais podem incluir diferentes tipos de chaves/valores,
# mas os testes atuais cobrem bem a funcionalidade principal.
# Por exemplo, testar com chaves numéricas ou valores complexos já é
# parcialmente coberto pela fixture populated_memory.
```
