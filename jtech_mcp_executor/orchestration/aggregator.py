from typing import List, Callable, Any, Dict
from collections import Counter

class ResultAggregator:
    """Utilitários para agregação de resultados de múltiplos agentes."""

    @staticmethod
    def summarize(results: List[str], task: str, llm_client: Any = None) -> str:
        """Agrega resultados através de resumo.

        Esta é uma implementação placeholder. Idealmente, usaria um LLM para resumir.
        Args:
            results: Lista de strings de resultados dos agentes.
            task: A descrição da tarefa original para dar contexto ao resumo.
            llm_client: (Opcional) Um cliente LLM para realizar o resumo.
        Returns:
            Uma string resumida dos resultados.
        """
        if not results:
            return "Nenhum resultado para resumir."

        # Placeholder: Concatena os resultados e adiciona uma nota sobre a tarefa.
        # Em uma implementação real, aqui poderia ser feita uma chamada a um LLM.
        # Exemplo: if llm_client: return llm_client.summarize(results, task_context=task)
        combined_results = "\n".join(results)
        return f"Resumo para a tarefa '{task}':\n{combined_results}"

    @staticmethod
    def concatenate(results: List[str]) -> str:
        """Concatena resultados.

        Args:
            results: Lista de strings de resultados dos agentes.
        Returns:
            Uma única string com todos os resultados concatenados.
        """
        return "\n".join(results)

    @staticmethod
    def vote(results: List[Any]) -> Any:
        """Implementa um sistema de votação para resultados conflitantes.

        Retorna o resultado mais comum. Em caso de empate, retorna um dos empatados.
        Args:
            results: Lista de resultados (podem ser strings, números, etc.).
        Returns:
            O resultado mais votado.
        """
        if not results:
            return None

        count = Counter(results)
        most_common = count.most_common(1)
        return most_common[0][0] if most_common else None

    @staticmethod
    def average(results: List[float | int]) -> float | None:
        """Calcula a média de uma lista de números.

        Args:
            results: Lista de números (float ou int).
        Returns:
            A média dos números, ou None se a lista estiver vazia.
        """
        if not results:
            return None
        return sum(results) / len(results)

    @staticmethod
    def sum_values(results: List[float | int]) -> float | int:
        """Soma uma lista de números.

        Args:
            results: Lista de números (float ou int).
        Returns:
            A soma dos números. Retorna 0 se a lista estiver vazia.
        """
        return sum(results)

    @staticmethod
    def pick_first(results: List[Any]) -> Any:
        """Retorna o primeiro resultado não nulo da lista.

        Args:
            results: Lista de resultados.
        Returns:
            O primeiro resultado não nulo, ou None se todos forem nulos ou a lista estiver vazia.
        """
        for result in results:
            if result is not None:
                return result
        return None

    @staticmethod
    def pick_last(results: List[Any]) -> Any:
        """Retorna o último resultado não nulo da lista.

        Args:
            results: Lista de resultados.
        Returns:
            O último resultado não nulo, ou None se todos forem nulos ou a lista estiver vazia.
        """
        for result in reversed(results):
            if result is not None:
                return result
        return None
