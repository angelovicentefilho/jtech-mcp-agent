from typing import Any, Dict

class AgentMemory:
    """Armazena e gerencia a memória compartilhada entre agentes."""

    def __init__(self) -> None:
        """Inicializa um novo AgentMemory."""
        self._memory: Dict[str, Any] = {}

    def add_memory(self, key: str, value: Any) -> None:
        """Adiciona um item à memória.

        Args:
            key: A chave para o item da memória.
            value: O valor do item da memória.
        """
        self._memory[key] = value

    def get_memory(self, key: str) -> Any:
        """Recupera um item da memória.

        Args:
            key: A chave do item da memória a ser recuperado.

        Returns:
            O valor do item da memória, ou None se a chave não existir.
        """
        return self._memory.get(key)

    def get_all_memory(self) -> Dict[str, Any]:
        """Recupera uma cópia de toda a memória.

        Returns:
            Um dicionário contendo todos os itens da memória.
        """
        return self._memory.copy()

    def clear_memory(self) -> None:
        """Limpa todos os itens da memória."""
        self._memory.clear()

    def remove_memory(self, key: str) -> None:
        """Remove um item específico da memória.

        Args:
            key: A chave do item da memória a ser removido.
        """
        if key in self._memory:
            del self._memory[key]
