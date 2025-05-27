from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TYPE_CHECKING

# Importar AgentMemory para type hinting
from .memory import AgentMemory

# Usar TYPE_CHECKING para evitar importação circular com JtechMCPCrew
if TYPE_CHECKING:
    from .crew import JtechMCPCrew # Import JtechMCPCrew para type hinting

class JtechMCPWorkflow(ABC):
    """Classe base abstrata para workflows de execução de múltiplos agentes."""
    
    def __init__(self, shared_memory: Optional[AgentMemory] = None):
        """Inicializa o workflow.

        Args:
            shared_memory: Uma instância opcional de AgentMemory que pode ser usada
                           pelo workflow para armazenar ou recuperar dados entre tarefas/agentes.
        """
        # Se nenhuma memória compartilhada é passada, o workflow pode criar uma própria
        # ou depender da memória do Crew que será passada no execute().
        # Por simplicidade, vamos permitir que seja None aqui e o Crew passe a sua.
        self._shared_memory = shared_memory 

    @property
    def shared_memory(self) -> Optional[AgentMemory]:
        """Retorna a instância de AgentMemory associada a este workflow."""
        return self._shared_memory

    @shared_memory.setter
    def shared_memory(self, memory: AgentMemory) -> None:
        """Define a instância de AgentMemory para este workflow."""
        self._shared_memory = memory
    
    @abstractmethod
    async def execute(
        self,
        crew: 'JtechMCPCrew', # Usar string para JtechMCPCrew para evitar import circular
        task_description: str, # Descrição da tarefa geral para o workflow
        context: Optional[Dict[str, Any]] = None,
        # A memória compartilhada pode ser passada aqui explicitamente pelo Crew,
        # ou o workflow pode usar a que foi definida no seu construtor ou via setter.
        # Para consistência, vamos esperar que o Crew a passe no execute.
        shared_memory: AgentMemory 
    ) -> Dict[str, Any]:
        """Executa o workflow com o crew e a tarefa especificados.

        Este método deve ser implementado por subclasses para definir a lógica
        específica de como os agentes no crew colaboram para realizar a tarefa.

        Args:
            crew: A instância de JtechMCPCrew que executará este workflow.
            task_description: A descrição da tarefa principal a ser realizada.
            context: Um dicionário opcional de contexto inicial para o workflow.
                     Pode ser usado para passar dados iniciais para a primeira tarefa
                     ou para configurar o workflow.
            shared_memory: A memória compartilhada fornecida pelo Crew. O workflow
                           deve usar esta instância para compartilhar dados entre
                           as etapas/agentes.

        Returns:
            Um dicionário contendo o resultado final da execução do workflow.
        """
        pass


from typing import Any, Dict, List, Optional, TYPE_CHECKING

# Import JtechMCPTask e AgentMemory (AgentMemory já importado acima para JtechMCPWorkflow)
from .task import JtechMCPTask
# from .memory import AgentMemory # AgentMemory já está importado

# Logger para o workflow
import logging
logger = logging.getLogger(__name__)

# Usar TYPE_CHECKING para evitar importação circular com JtechMCPCrew
# (já definido no início do arquivo para JtechMCPWorkflow)
# if TYPE_CHECKING:
#     from .crew import JtechMCPCrew


class SequentialWorkflow(JtechMCPWorkflow):
    """Workflow que executa uma lista de tarefas em sequência.

    Cada tarefa é executada por seu agente designado, e o resultado de uma tarefa
    pode ser passado como contexto para a próxima.
    """
    
    def __init__(
        self,
        tasks: Optional[List[JtechMCPTask]] = None,
        shared_memory: Optional[AgentMemory] = None,
    ) -> None:
        """Inicializa o SequentialWorkflow.

        Args:
            tasks: Uma lista opcional de JtechMCPTask a serem executadas em sequência.
            shared_memory: Uma instância opcional de AgentMemory.
        """
        super().__init__(shared_memory)
        self.tasks: List[JtechMCPTask] = tasks if tasks is not None else []

    def add_task(self, task: JtechMCPTask) -> None:
        """Adiciona uma tarefa à sequência do workflow."""
        self.tasks.append(task)
        if logger.isEnabledFor(logging.DEBUG): # Para não construir a string desnecessariamente
            logger.debug(f"Tarefa '{task.description}' adicionada ao SequentialWorkflow. Total de tarefas: {len(self.tasks)}")

    async def execute(
        self,
        crew: 'JtechMCPCrew',
        task_description: str, # Descrição da tarefa geral para o workflow
        context: Optional[Dict[str, Any]] = None,
        shared_memory: AgentMemory # Memória compartilhada vinda do Crew
    ) -> Dict[str, Any]:
        """Executa as tarefas sequencialmente.

        O contexto é atualizado com o resultado de cada tarefa e passado para a próxima.
        A memória compartilhada também pode ser usada para trocar dados mais complexos.

        Args:
            crew: A instância de JtechMCPCrew.
            task_description: A descrição da tarefa geral para o workflow.
            context: Contexto inicial para a primeira tarefa.
            shared_memory: A memória compartilhada fornecida pelo Crew.

        Returns:
            Um dicionário contendo o resultado da última tarefa e possivelmente
            outros dados relevantes do contexto final ou da memória compartilhada.
        """
        if crew.verbose:
            logger.info(f"Workflow Sequencial '{self.__class__.__name__}' iniciado para a tarefa: '{task_description}' com {len(self.tasks)} subtarefas.")

        # Usa a shared_memory fornecida pelo crew
        self.shared_memory = shared_memory # Garante que o workflow use a memória do Crew
        
        current_context = context.copy() if context is not None else {}
        # Adiciona a descrição geral da tarefa ao contexto inicial, se não estiver lá
        if 'workflow_task_description' not in current_context:
            current_context['workflow_task_description'] = task_description
            
        final_results: Dict[str, Any] = {"task_outputs": []}

        for i, task in enumerate(self.tasks):
            task_label = task.name or task.description # Para logs e chaves
            if crew.verbose:
                logger.info(f"Executando tarefa {i+1}/{len(self.tasks)}: '{task_label}' com o agente '{task.agent_name}'")

            agent = crew.get_agent(task.agent_name)
            if not agent:
                error_msg = f"Agente '{task.agent_name}' não encontrado no crew '{crew.name}' para a tarefa '{task_label}'."
                logger.error(error_msg)
                final_results['error'] = error_msg
                final_results['status'] = "FALHOU"
                # Adicionar informação da tarefa que falhou
                final_results["task_outputs"].append({
                    "task_name": task_label,
                    "agent_name": task.agent_name,
                    "status": "FALHOU_SETUP",
                    "error": error_msg
                })
                return final_results

            # Mesclar contexto da tarefa específica com o contexto atual do workflow
            task_execution_context = current_context.copy()
            if task.context: # Contexto específico da JtechMCPTask
                task_execution_context.update(task.context)
            
            # Adicionar o output da tarefa anterior ao contexto da tarefa atual, se existir
            if i > 0 and final_results["task_outputs"] and final_results["task_outputs"][-1].get("status") == "CONCLUÍDA":
                task_execution_context['last_task_output'] = final_results["task_outputs"][-1].get("output")

            try:
                # O agente executa sua tarefa. A descrição da tarefa do objeto JtechMCPTask é o 'query'
                # O 'context' aqui é o contexto acumulado do workflow + contexto específico da tarefa.
                task_output_str = await agent.run(query=task.description, context=task_execution_context)
                
                task_result = {
                    "task_name": task_label,
                    "agent_name": task.agent_name,
                    "output": task_output_str,
                    "status": "CONCLUÍDA"
                }
                final_results["task_outputs"].append(task_result)
                
                # Atualizar o contexto geral do workflow com o output da tarefa atual
                current_context[f"task_{task_label.replace(' ', '_')}_output"] = task_output_str
                current_context[f"agent_{task.agent_name}_last_output"] = task_output_str


                # Também podemos popular a memória compartilhada
                if self.shared_memory:
                    # Usar um ID único para a tarefa se disponível, senão nome ou índice
                    task_id_for_memory = task.task_id or task.name or f"task_{i+1}"
                    self.shared_memory.add_memory(f"task_{task_id_for_memory}_output", task_output_str)
                    self.shared_memory.add_memory(f"agent_{task.agent_name}_last_output", task_output_str)

                if crew.verbose:
                    log_output = task_output_str[:100] + "..." if len(task_output_str) > 100 else task_output_str
                    logger.info(f"Tarefa '{task_label}' concluída por '{task.agent_name}'. Resultado parcial: {log_output}")

            except Exception as e:
                error_msg = f"Erro ao executar a tarefa '{task_label}' com o agente '{task.agent_name}': {e}"
                logger.error(error_msg, exc_info=True) # exc_info=True para logar o traceback
                task_result = {
                    "task_name": task_label,
                    "agent_name": task.agent_name,
                    "error": str(e),
                    "status": "FALHOU"
                }
                final_results["task_outputs"].append(task_result)
                final_results['error'] = error_msg # Erro geral do workflow
                final_results['status'] = "FALHOU"
                return final_results # Termina o workflow em caso de erro em uma tarefa

        if crew.verbose:
            logger.info(f"Workflow Sequencial '{self.__class__.__name__}' concluído para: '{task_description}'")
        
        final_results['status'] = "CONCLUÍDO"
        final_results['final_context'] = current_context
        if final_results["task_outputs"] and final_results["task_outputs"][-1].get("status") == "CONCLUÍDA":
            final_results['final_output'] = final_results["task_outputs"][-1].get("output")
        elif not final_results["task_outputs"]:
             final_results['final_output'] = "Nenhuma tarefa foi executada."
        else:
            final_results['final_output'] = "Workflow concluído, mas a última tarefa não produziu um output direto ou falhou."


        return final_results


import asyncio # Para asyncio.gather
from typing import Any, Dict, List, Optional, Callable, TYPE_CHECKING

# Import JtechMCPTask, AgentMemory (já devem estar importados)
# Import ResultAggregator para o agregador de resultados
from .task import JtechMCPTask
# from .memory import AgentMemory # Já importado
from .aggregator import ResultAggregator # Importar o agregador

# Logger para o workflow (logger já instanciado)
# import logging
# logger = logging.getLogger(__name__)

# if TYPE_CHECKING: # Já definido
#     from .crew import JtechMCPCrew

class ParallelWorkflow(JtechMCPWorkflow):
    """Workflow que executa múltiplas tarefas em paralelo e depois agrega seus resultados."""
    
    def __init__(
        self,
        tasks: Optional[List[JtechMCPTask]] = None,
        result_aggregator: Optional[Callable[[List[Any]], Any]] = None,
        # Adicionando o parâmetro task_description_for_aggregator para o agregador summarize
        task_description_for_aggregator: Optional[str] = "Resultados de tarefas paralelas",
        shared_memory: Optional[AgentMemory] = None,
    ) -> None:
        """Inicializa o ParallelWorkflow.

        Args:
            tasks: Uma lista opcional de JtechMCPTask a serem executadas em paralelo.
            result_aggregator: Uma função opcional para agregar os resultados das tarefas paralelas.
                               Se não fornecida, os resultados serão retornados como uma lista.
                               Pode ser um dos métodos de ResultAggregator.
            task_description_for_aggregator: Descrição opcional da tarefa para ser usada
                                             pelo agregador summarize.
            shared_memory: Uma instância opcional de AgentMemory.
        """
        super().__init__(shared_memory)
        self.tasks: List[JtechMCPTask] = tasks if tasks is not None else []
        self.result_aggregator = result_aggregator
        self.task_description_for_aggregator = task_description_for_aggregator

    def add_task(self, task: JtechMCPTask) -> None:
        """Adiciona uma tarefa à lista de tarefas paralelas."""
        self.tasks.append(task)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Tarefa '{task.description}' adicionada ao ParallelWorkflow. Total de tarefas: {len(self.tasks)}")


    async def _execute_single_task(
        self,
        crew: 'JtechMCPCrew',
        task: JtechMCPTask,
        workflow_context: Dict[str, Any], # Contexto geral do workflow
        shared_memory: AgentMemory
    ) -> Dict[str, Any]:
        """Método auxiliar para executar uma única tarefa e retornar seu resultado estruturado."""
        task_label = task.name or task.description
        if crew.verbose:
            logger.info(f"Iniciando tarefa paralela: '{task_label}' com o agente '{task.agent_name}'")

        agent = crew.get_agent(task.agent_name)
        if not agent:
            error_msg = f"Agente '{task.agent_name}' não encontrado para a tarefa paralela '{task_label}'."
            logger.error(error_msg)
            return {
                "task_name": task_label,
                "agent_name": task.agent_name,
                "error": error_msg,
                "status": "FALHOU_SETUP" # Status mais específico
            }

        task_execution_context = workflow_context.copy()
        if task.context:
            task_execution_context.update(task.context)
        
        try:
            task_output_str = await agent.run(query=task.description, context=task_execution_context)
            
            task_id_for_memory = task.task_id or task.name or task_label.replace(" ", "_")[:30]
            if self.shared_memory: # self.shared_memory é a instância do Crew
                 self.shared_memory.add_memory(f"parallel_task_{task_id_for_memory}_output", task_output_str)
                 self.shared_memory.add_memory(f"agent_{task.agent_name}_last_parallel_output", task_output_str)
            
            if crew.verbose:
                log_output = task_output_str[:100] + "..." if len(task_output_str) > 100 else task_output_str
                logger.info(f"Tarefa paralela '{task_label}' concluída por '{task.agent_name}'. Resultado parcial: {log_output}")
            return {
                "task_name": task_label,
                "agent_name": task.agent_name,
                "output": task_output_str,
                "status": "CONCLUÍDA"
            }
        except Exception as e:
            error_msg = f"Erro na tarefa paralela '{task_label}' com agente '{task.agent_name}': {e}"
            logger.error(error_msg, exc_info=True)
            return {
                "task_name": task_label,
                "agent_name": task.agent_name,
                "error": str(e),
                "status": "FALHOU"
            }

    async def execute(
        self,
        crew: 'JtechMCPCrew',
        task_description: str, 
        context: Optional[Dict[str, Any]] = None,
        shared_memory: AgentMemory 
    ) -> Dict[str, Any]:
        """Executa as tarefas em paralelo usando asyncio.gather e agrega os resultados."""
        if crew.verbose:
            logger.info(f"Workflow Paralelo '{self.__class__.__name__}' iniciado para: '{task_description}' com {len(self.tasks)} subtarefas.")

        self.shared_memory = shared_memory 
        
        workflow_context = context.copy() if context is not None else {}
        if 'workflow_task_description' not in workflow_context:
            workflow_context['workflow_task_description'] = task_description

        if not self.tasks:
            logger.warning(f"Workflow Paralelo '{self.__class__.__name__}' não possui tarefas para executar para: '{task_description}'.")
            return {
                "task_outputs": [],
                "aggregated_output": "Nenhuma tarefa para executar.",
                "status": "CONCLUÍDO_SEM_TAREFAS"
            }

        coroutines = [
            self._execute_single_task(crew, task, workflow_context, shared_memory) 
            for task in self.tasks
        ]
        
        task_execution_results = await asyncio.gather(*coroutines)

        final_results: Dict[str, Any] = {"task_outputs": task_execution_results}
        
        outputs_for_aggregation = [
            res.get("output") for res in task_execution_results 
            if res.get("status") == "CONCLUÍDA" and res.get("output") is not None
        ]

        if self.result_aggregator:
            try:
                if self.result_aggregator == ResultAggregator.summarize:
                    # Passa a descrição da tarefa geral do workflow OU a descrição específica do agregador
                    aggregator_task_context = self.task_description_for_aggregator or task_description
                    aggregated_output = self.result_aggregator(outputs_for_aggregation, aggregator_task_context)
                else:
                    aggregated_output = self.result_aggregator(outputs_for_aggregation)

                final_results['aggregated_output'] = aggregated_output
                if crew.verbose:
                    log_output_agg = str(aggregated_output)[:200] + "..." if len(str(aggregated_output)) > 200 else str(aggregated_output)
                    logger.info(f"Resultados agregados ({self.result_aggregator.__name__ if hasattr(self.result_aggregator, '__name__') else 'custom'}): {log_output_agg}")
            except Exception as e:
                logger.error(f"Erro ao agregar resultados com '{self.result_aggregator.__name__ if hasattr(self.result_aggregator, '__name__') else 'custom'}': {e}", exc_info=True)
                final_results['aggregation_error'] = str(e)
                final_results['aggregated_output'] = outputs_for_aggregation # Fallback para lista de outputs
        else:
            final_results['aggregated_output'] = outputs_for_aggregation

        if any(res.get("status") == "FALHOU" or res.get("status") == "FALHOU_SETUP" for res in task_execution_results):
            final_results['status'] = "CONCLUÍDO_COM_FALHAS"
            failed_tasks_count = sum(1 for res in task_execution_results if res.get("status") == "FALHOU" or res.get("status") == "FALHOU_SETUP")
            final_results['error'] = f"{failed_tasks_count} tarefa(s) falharam ou não puderam ser configuradas durante a execução paralela."
        elif not outputs_for_aggregation and self.tasks: # Havia tarefas, mas nenhuma produziu output para agregação (todas falharam ou não retornaram output)
            final_results['status'] = "CONCLUÍDO_SEM_OUTPUTS_VALIDOS"
            final_results['error'] = "Nenhuma tarefa produziu output válido para agregação."
        else:
            final_results['status'] = "CONCLUÍDO"

        if crew.verbose:
            logger.info(f"Workflow Paralelo '{self.__class__.__name__}' concluído para: '{task_description}'. Status: {final_results['status']}")
            
        return final_results


# asyncio já importado para ParallelWorkflow
# from typing import Any, Dict, List, Optional, TYPE_CHECKING (já importados)
# from .task import JtechMCPTask (já importado)
# from .memory import AgentMemory (já importado)
# import logging (logger já instanciado)
# if TYPE_CHECKING: (já definido)
#     from .crew import JtechMCPCrew


class HierarchicalWorkflow(JtechMCPWorkflow):
    """Implementa um modelo supervisor/trabalhador.

    Um agente supervisor recebe uma tarefa principal e pode delegar sub-tarefas
    para agentes trabalhadores. O supervisor pode iterar, revisar o trabalho dos
    trabalhadores e refinar o resultado até que um critério seja atendido ou
    um número máximo de iterações seja alcançado.
    """
    
    def __init__(
        self,
        supervisor_agent_name: str, 
        worker_agent_names: List[str], 
        max_iterations: int = 5,
        shared_memory: Optional[AgentMemory] = None,
        supervisor_instructions_template: Optional[str] = None,
    ) -> None:
        """Inicializa o HierarchicalWorkflow.

        Args:
            supervisor_agent_name: O nome ou papel do agente supervisor.
            worker_agent_names: Lista de nomes ou papéis dos agentes trabalhadores.
            max_iterations: Número máximo de iterações entre supervisor e trabalhadores.
            shared_memory: Uma instância opcional de AgentMemory.
            supervisor_instructions_template: Um template de string para as instruções
                                              do supervisor. Pode conter placeholders como
                                              {task_description}, {worker_outputs_str}, 
                                              {worker_names}, {current_iteration}.
        """
        super().__init__(shared_memory)
        self.supervisor_agent_name = supervisor_agent_name
        self.worker_agent_names = worker_agent_names
        self.max_iterations = max_iterations
        
        self.supervisor_instructions_template = supervisor_instructions_template or \
            "Tarefa Principal: '{task_description}'.\n" \
            "Trabalhadores Disponíveis: {worker_names}.\n" \
            "Iteração Atual: {current_iteration} de {max_iterations}.\n" \
            "Resultados Anteriores dos Trabalhadores:\n{worker_outputs_str}\n\n" \
            "Seu papel é coordenar os trabalhadores para alcançar o objetivo da tarefa principal. " \
            "Analise os resultados anteriores e forneça instruções claras e específicas para um ou mais trabalhadores. " \
            "Se você acredita que a tarefa principal foi concluída satisfatoriamente com base nos resultados dos trabalhadores, " \
            "finalize sua resposta com a palavra 'CONCLUÍDO' em maiúsculas e forneça o resultado final consolidado. " \
            "Caso contrário, forneça as próximas instruções para os trabalhadores. " \
            "Você pode instruir um trabalhador específico mencionando seu nome (ex: '{worker_example_name}, por favor, faça X.') " \
            "ou dar uma instrução geral para todos. " \
            "Qual é o seu plano para esta iteração?"

    async def execute(
        self,
        crew: 'JtechMCPCrew',
        task_description: str, 
        context: Optional[Dict[str, Any]] = None,
        shared_memory: AgentMemory
    ) -> Dict[str, Any]:
        """Executa o workflow hierárquico."""
        if crew.verbose:
            logger.info(f"Workflow Hierárquico '{self.__class__.__name__}' iniciado para: '{task_description}' com supervisor '{self.supervisor_agent_name}' e trabalhadores: {self.worker_agent_names}")

        self.shared_memory = shared_memory # Garante que o workflow use a memória do Crew
        
        supervisor = crew.get_agent(self.supervisor_agent_name)
        if not supervisor:
            error_msg = f"Agente supervisor '{self.supervisor_agent_name}' não encontrado no crew '{crew.name}'."
            logger.error(error_msg)
            return {"status": "FALHOU_SETUP", "error": error_msg, "history": []}

        workers: Dict[str, Any] = {} # Usar Any para o tipo do agente JtechMCPAgent
        for name in self.worker_agent_names:
            worker = crew.get_agent(name)
            if not worker:
                error_msg = f"Agente trabalhador '{name}' não encontrado no crew '{crew.name}'."
                logger.error(error_msg)
                return {"status": "FALHOU_SETUP", "error": error_msg, "history": []}
            workers[name] = worker
        
        if not workers:
            error_msg = "Nenhum agente trabalhador válido foi configurado ou encontrado."
            logger.error(error_msg)
            return {"status": "FALHOU_SETUP", "error": error_msg, "history": []}

        current_context = context.copy() if context is not None else {}
        current_context['overall_task_description'] = task_description # Diferenciar da task_description da iteração
        current_context['available_workers'] = list(workers.keys())
        
        history = [] 
        worker_outputs_str = "Nenhum resultado de trabalhadores ainda."
        supervisor_final_output = "Workflow não produziu um output final do supervisor."


        for i in range(self.max_iterations):
            iteration = i + 1
            iteration_log = {"iteration": iteration, "supervisor_action": None, "worker_tasks_delegated": [], "worker_results": []}
            
            if crew.verbose:
                logger.info(f"Iniciando iteração {iteration}/{self.max_iterations} do workflow hierárquico para '{task_description}'.")

            # 1. Supervisor planeja/delega
            worker_example_name = list(workers.keys())[0] if workers else "TrabalhadorExemplo"
            supervisor_prompt = self.supervisor_instructions_template.format(
                task_description=task_description,
                worker_names=", ".join(workers.keys()),
                worker_example_name=worker_example_name,
                current_iteration=iteration,
                max_iterations=self.max_iterations,
                worker_outputs_str=worker_outputs_str
            )
            # Adicionar ao contexto específico desta chamada do supervisor
            supervisor_call_context = current_context.copy()
            supervisor_call_context['supervisor_iteration_prompt'] = supervisor_prompt 
            # Passar os outputs brutos da iteração anterior para o supervisor, se houver
            if iteration > 1 and history and "worker_results" in history[-1]:
                 supervisor_call_context['previous_iteration_worker_results'] = history[-1]["worker_results"]

            try:
                if crew.verbose:
                    logger.info(f"Supervisor '{self.supervisor_agent_name}' está planejando. Prompt (início): {supervisor_prompt[:250]}...")
                
                supervisor_output = await supervisor.run(query=supervisor_prompt, context=supervisor_call_context)
                supervisor_final_output = supervisor_output # Atualiza a cada iteração
                iteration_log["supervisor_action"] = supervisor_output
                
                if crew.verbose:
                    logger.info(f"Supervisor '{self.supervisor_agent_name}' output: {supervisor_output[:250]}...")
                if self.shared_memory:
                    self.shared_memory.add_memory(f"hierarchical_supervisor_iter_{iteration}_output", supervisor_output)

                if "CONCLUÍDO" in supervisor_output.upper(): # Não precisa ser i > 0, o supervisor pode concluir com base no input inicial
                    logger.info(f"Supervisor indicou conclusão na iteração {iteration}.")
                    history.append(iteration_log)
                    return {"status": "CONCLUÍDO", "final_output": supervisor_output, "history": history}
                
                # Delegação de tarefas para trabalhadores
                sub_tasks_coroutines = []
                delegated_worker_names = []

                # Lógica de delegação:
                # Se um nome de worker é mencionado, a tarefa é para ele.
                # Se múltiplos nomes, pode ser um desafio parsear qual tarefa é para quem sem um formato estruturado.
                # Simplificação: A primeira menção de worker direciona a tarefa inteira.
                # Se nenhum worker específico é mencionado, a tarefa é para todos.
                
                # Tentativa de identificar um worker específico no output do supervisor
                worker_targeted_by_supervisor: Optional[str] = None
                for worker_name_key in workers.keys():
                    # Usar word boundaries ou similar para evitar substrings pode ser melhor, mas para simplificar:
                    if worker_name_key.lower() in supervisor_output.lower(): 
                        worker_targeted_by_supervisor = worker_name_key
                        if crew.verbose: logger.info(f"Supervisor parece ter direcionado a tarefa para: {worker_targeted_by_supervisor}")
                        break # Pega o primeiro encontrado

                worker_task_description = supervisor_output # Por padrão, o output do supervisor é a tarefa
                
                worker_call_context = current_context.copy()
                worker_call_context['supervisor_instructions_for_this_iteration'] = supervisor_output


                if worker_targeted_by_supervisor:
                    worker_agent = workers[worker_targeted_by_supervisor]
                    coro = worker_agent.run(query=worker_task_description, context=worker_call_context.copy())
                    sub_tasks_coroutines.append(coro)
                    delegated_worker_names.append(worker_targeted_by_supervisor)
                    iteration_log["worker_tasks_delegated"].append({
                        "agent_name": worker_targeted_by_supervisor, 
                        "delegated_task_description": worker_task_description
                    })
                else: # Delegar para todos se nenhum específico foi identificado
                    if crew.verbose: logger.info("Nenhum trabalhador específico identificado no output do supervisor. Delegando para todos.")
                    for worker_name, worker_agent in workers.items():
                        coro = worker_agent.run(query=worker_task_description, context=worker_call_context.copy())
                        sub_tasks_coroutines.append(coro)
                        delegated_worker_names.append(worker_name)
                        iteration_log["worker_tasks_delegated"].append({
                            "agent_name": worker_name,
                            "delegated_task_description": worker_task_description
                        })
                
                # 2. Trabalhadores executam (em paralelo)
                processed_worker_outputs_for_next_supervisor_iteration = []
                if sub_tasks_coroutines:
                    raw_worker_outputs = await asyncio.gather(*sub_tasks_coroutines, return_exceptions=True)
                    
                    for idx, raw_output in enumerate(raw_worker_outputs):
                        worker_name = delegated_worker_names[idx]
                        worker_result_entry = {"agent_name": worker_name}

                        if isinstance(raw_output, Exception):
                            logger.error(f"Erro do trabalhador '{worker_name}' na iteração {iteration}: {raw_output}")
                            worker_result_entry["error"] = str(raw_output)
                            processed_worker_outputs_for_next_supervisor_iteration.append(f"Trabalhador {worker_name} FALHOU: {raw_output}")
                        else:
                            if crew.verbose: logger.info(f"Trabalhador '{worker_name}' (iteração {iteration}) output: {str(raw_output)[:100]}...")
                            worker_result_entry["output"] = raw_output
                            processed_worker_outputs_for_next_supervisor_iteration.append(f"Trabalhador {worker_name}: {raw_output}")
                            if self.shared_memory:
                                self.shared_memory.add_memory(f"hierarchical_worker_{worker_name}_iter_{iteration}_output", raw_output)
                        iteration_log["worker_results"].append(worker_result_entry)
                    
                    worker_outputs_str = "\n".join(processed_worker_outputs_for_next_supervisor_iteration)
                else:
                    worker_outputs_str = "Nenhuma sub-tarefa foi delegada aos trabalhadores nesta iteração pelo supervisor."
                    if crew.verbose: logger.info(worker_outputs_str)
                
                # Atualizar contexto para a próxima iteração do supervisor
                current_context['last_worker_outputs_summary_for_supervisor'] = worker_outputs_str
                current_context['previous_worker_results_structured'] = iteration_log["worker_results"]


            except Exception as e:
                logger.error(f"Erro durante a iteração {iteration} do workflow hierárquico: {e}", exc_info=True)
                iteration_log["error"] = str(e)
                history.append(iteration_log)
                return {"status": "FALHOU", "error": f"Erro na iteração {iteration}: {e}", "history": history, "final_output": supervisor_final_output}
            
            history.append(iteration_log)


        logger.warning(f"Workflow Hierárquico para '{task_description}' atingiu o número máximo de iterações ({self.max_iterations}).")
        return {
            "status": "MAX_ITERATIONS_REACHED", 
            "final_output": supervisor_final_output, 
            "history": history
        }