import pytest
from jtech_mcp_executor.orchestration.aggregator import ResultAggregator

class TestResultAggregator:

    def test_summarize_with_results(self):
        results = ["First sentence.", "Second sentence."]
        task_desc = "Test Summarization"
        # O placeholder atual concatena com um cabeçalho
        expected = f"Resumo para a tarefa '{task_desc}':\nFirst sentence.\nSecond sentence."
        assert ResultAggregator.summarize(results, task_desc) == expected

    def test_summarize_empty_results(self):
        assert ResultAggregator.summarize([], "Empty Test") == "Nenhum resultado para resumir."

    def test_concatenate_with_results(self):
        results = ["Line 1", "Line 2", "Line 3"]
        expected = "Line 1\nLine 2\nLine 3"
        assert ResultAggregator.concatenate(results) == expected

    def test_concatenate_empty_results(self):
        assert ResultAggregator.concatenate([]) == "" # Concatenação de lista vazia deve ser string vazia

    def test_vote_clear_winner_string(self):
        results = ["apple", "banana", "apple", "orange", "apple"]
        assert ResultAggregator.vote(results) == "apple"

    def test_vote_clear_winner_numbers(self):
        results_num = [1, 2, 1, 3, 1, 2, 1]
        assert ResultAggregator.vote(results_num) == 1
        
    def test_vote_clear_winner_mixed_case_strings(self):
        # Counter é case-sensitive
        results = ["Apple", "apple", "Apple"]
        assert ResultAggregator.vote(results) == "Apple"


    def test_vote_tie(self):
        results_str_tie = ["apple", "banana", "apple", "banana"]
        # Em caso de empate, Counter.most_common(1) retorna um dos empatados.
        # O comportamento exato pode depender da ordem de inserção ou do valor.
        assert ResultAggregator.vote(results_str_tie) in ["apple", "banana"]
        
        results_num_tie = [1, 2, 1, 2, 3]
        assert ResultAggregator.vote(results_num_tie) in [1, 2]

    def test_vote_empty_results(self):
        assert ResultAggregator.vote([]) is None
        
    def test_vote_single_item(self):
        assert ResultAggregator.vote(["single_value"]) == "single_value"
        assert ResultAggregator.vote([100]) == 100

    def test_average_with_results(self):
        results = [10, 20, 30, 40, 50]
        assert ResultAggregator.average(results) == 30.0
        
        results_float = [10.5, 20.5, 30.0] # (10.5 + 20.5 + 30.0) / 3 = 61 / 3 = 20.333...
        assert pytest.approx(ResultAggregator.average(results_float)) == (10.5 + 20.5 + 30.0) / 3


    def test_average_empty_results(self):
        assert ResultAggregator.average([]) is None
        
    def test_average_single_number(self):
        assert ResultAggregator.average([25]) == 25.0
        assert ResultAggregator.average([-10]) == -10.0

    def test_sum_values_with_results(self):
        results_int = [10, 20, 30]
        assert ResultAggregator.sum_values(results_int) == 60
        
        results_float = [10.5, 20.0, 0.5]
        assert ResultAggregator.sum_values(results_float) == 31.0
        
        results_mixed = [1, 2.5, 3]
        assert ResultAggregator.sum_values(results_mixed) == 6.5

    def test_sum_values_empty_results(self):
        # sum([]) é 0 para números
        assert ResultAggregator.sum_values([]) == 0
        
    def test_sum_values_single_number(self):
        assert ResultAggregator.sum_values([15]) == 15
        assert ResultAggregator.sum_values([-5.5]) == -5.5


    def test_pick_first_basic(self):
        results = [None, "hello", "world", None]
        assert ResultAggregator.pick_first(results) == "hello"

    def test_pick_first_first_is_value(self):
        results = ["first_val", None, "world"]
        assert ResultAggregator.pick_first(results) == "first_val"

    def test_pick_first_all_none(self):
        results = [None, None, None, None]
        assert ResultAggregator.pick_first(results) is None

    def test_pick_first_empty_list(self):
        assert ResultAggregator.pick_first([]) is None
        
    def test_pick_first_mixed_types_valid_first(self):
        results = [None, 0, "world", False] # 0 é um valor válido
        assert ResultAggregator.pick_first(results) == 0
        
        results_false = [None, False, "world", 0] # False é um valor válido
        assert ResultAggregator.pick_first(results_false) is False


    def test_pick_last_basic(self):
        results = [None, "hello", "world", None]
        assert ResultAggregator.pick_last(results) == "world"

    def test_pick_last_last_is_value(self):
        results = ["hello", None, "last_val"]
        assert ResultAggregator.pick_last(results) == "last_val"

    def test_pick_last_all_none(self):
        results = [None, None, None, None]
        assert ResultAggregator.pick_last(results) is None

    def test_pick_last_empty_list(self):
        assert ResultAggregator.pick_last([]) is None
        
    def test_pick_last_mixed_types_valid_last(self):
        results = ["hello", 0, None, False] # False é um valor válido
        assert ResultAggregator.pick_last(results) is False
        
        results_zero = ["hello", False, None, 0] # 0 é um valor válido
        assert ResultAggregator.pick_last(results_zero) == 0

    def test_summarize_with_llm_client_placeholder(self):
        """Testa a chamada de summarize com um llm_client (ainda é placeholder)."""
        results = ["First sentence.", "Second sentence."]
        task_desc = "Test Summarization with LLM"
        # O mock_llm_client não precisa fazer nada, pois a lógica de summarize
        # não o utiliza ativamente na implementação atual (placeholder).
        mock_llm_client = object() 
        
        expected = f"Resumo para a tarefa '{task_desc}':\nFirst sentence.\nSecond sentence."
        # O resultado deve ser o mesmo do placeholder, pois o llm_client não é usado.
        assert ResultAggregator.summarize(results, task_desc, llm_client=mock_llm_client) == expected
```
