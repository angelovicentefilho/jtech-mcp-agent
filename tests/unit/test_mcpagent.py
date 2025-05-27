import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch, call # Added call

from langchain_core.agents import AgentFinish # For mocking AgentExecutor output

from jtech_mcp_executor.agents.mcpagent import JtechMCPAgent
# Assuming BaseLanguageModel and JtechMCPClient are mocked for tests
# from langchain.schema.language_model import BaseLanguageModel (mocked by MockLLM)
# from jtech_mcp_executor.client import JtechMCPClient (mocked by MockMCPClient)

# Mock básico para LLM e Client
@pytest.fixture
def mock_llm():
    return MagicMock(name="MockLLM")

@pytest.fixture
def mock_mcp_client():
    client = MagicMock(name="MockMCPClient")
    client.get_all_active_sessions.return_value = {}
    client.create_all_sessions = AsyncMock(return_value={"session1": MagicMock(name="MockSession1")})
    return client

@pytest.fixture
def basic_agent(mock_llm, mock_mcp_client):
    """Fixture para um JtechMCPAgent básico para testes de role e receive_message."""
    agent = JtechMCPAgent(llm=mock_llm, client=mock_mcp_client)
    return agent

@pytest.fixture
@pytest.mark.asyncio
async def initialized_agent(mock_llm, mock_mcp_client):
    """Fixture para um JtechMCPAgent que foi inicializado, com _agent_executor mockado."""
    
    # Patch LangChainAdapter constructor and its methods
    with patch('jtech_mcp_executor.agents.mcpagent.LangChainAdapter') as MockAdapterConstructor:
        mock_adapter_instance = MagicMock(name="MockAdapterInstance")
        # Assume create_tools returns a list with at least one mock tool for system message generation
        mock_tool = MagicMock(name="MockTool")
        mock_tool.name = "mock_tool_for_tests" 
        mock_adapter_instance.create_tools = AsyncMock(return_value=[mock_tool])
        MockAdapterConstructor.return_value = mock_adapter_instance

        # Patch create_system_message to prevent complex prompt building logic
        with patch('jtech_mcp_executor.agents.mcpagent.create_system_message') as mock_create_system_message:
            mock_system_message_instance = MagicMock(name="MockSystemMessage")
            mock_system_message_instance.content = "Mocked system prompt"
            mock_create_system_message.return_value = mock_system_message_instance

            agent = JtechMCPAgent(llm=mock_llm, client=mock_mcp_client, auto_initialize=False)
            
            # Mock _create_agent to return a mock AgentExecutor
            # The AgentExecutor itself needs to be an AsyncMock if its methods are async
            mock_executor_instance = AsyncMock(name="MockAgentExecutor")
            
            # Mock the _atake_next_step method on this executor instance
            # It should return an AgentFinish to terminate the loop in agent.run()
            mock_agent_finish = AgentFinish(return_values={"output": "Final result from mock executor"}, log="")
            mock_executor_instance._atake_next_step = AsyncMock(return_value=mock_agent_finish)

            # Assign the fully mocked executor to the agent
            agent._agent_executor = mock_executor_instance
            
            # Simulate parts of initialize() that are needed for run() to proceed
            agent._tools = mock_adapter_instance.create_tools.return_value # list of mock tools
            agent._system_message = mock_system_message_instance
            agent._initialized = True # Mark as initialized
            
            # Ensure the agent executor has max_iterations if run() tries to set it.
            # The AsyncMock spec for AgentExecutor might not include attributes by default.
            mock_executor_instance.max_iterations = agent.max_steps 


    return agent


class TestJtechMCPAgentOrchestrationFeatures:

    def test_agent_init_default_role(self, basic_agent: JtechMCPAgent):
        assert basic_agent.role is None
        assert basic_agent.role_description is None

    def test_agent_init_with_role(self, mock_llm, mock_mcp_client):
        # This test doesn't need the full initialized_agent fixture
        agent = JtechMCPAgent(
            llm=mock_llm, 
            client=mock_mcp_client, 
            role="Tester", 
            role_description="Tests things"
        )
        assert agent.role == "Tester"
        assert agent.role_description == "Tests things"

    def test_set_role(self, basic_agent: JtechMCPAgent):
        basic_agent.set_role("Researcher", "Gathers information")
        assert basic_agent.role == "Researcher"
        assert basic_agent.role_description == "Gathers information"
        # Test logger call if set_role logs
        # For this, we'd need to patch the logger in basic_agent's module
        # e.g. @patch('jtech_mcp_executor.agents.mcpagent.logger')

    def test_get_role(self, basic_agent: JtechMCPAgent):
        basic_agent.role = "Analyst"
        basic_agent.role_description = "Analyzes data"
        role, desc = basic_agent.get_role()
        assert role == "Analyst"
        assert desc == "Analyzes data"

    @pytest.mark.asyncio
    @patch('jtech_mcp_executor.agents.mcpagent.logger') # Patch logger in the mcpagent module
    async def test_receive_message_logs_correctly(self, mock_logger, basic_agent: JtechMCPAgent):
        basic_agent.role = "ReceiverAgent" # Give a role for more specific logging
        message_content = "Hello from another agent"
        sender_agent = "SenderAgent123"
        message_context = {"data_id": "123", "priority": "high"}
        
        await basic_agent.receive_message(message_content, sender_agent, message_context)
        
        expected_log_calls = [
            call(f"Agente '{basic_agent.role}' recebeu mensagem de '{sender_agent}': '{message_content}'"),
            call(f"Contexto da mensagem recebida: {message_context}")
        ]
        mock_logger.info.assert_has_calls(expected_log_calls, any_order=False)

    @pytest.mark.asyncio
    async def test_run_with_context_passes_to_executor(self, initialized_agent: JtechMCPAgent):
        # initialized_agent fixture provides an agent with _agent_executor already mocked.
        # The _agent_executor._atake_next_step is also mocked to return an AgentFinish.
        mock_executor_instance = initialized_agent._agent_executor
        
        test_query = "Test query for context propagation"
        run_context = {"user_id": "userXYZ", "session_info": "session_abc"}
        
        # Call the run method
        await initialized_agent.run(test_query, context=run_context)

        # Assert that _atake_next_step on the mock_executor_instance was awaited
        mock_executor_instance._atake_next_step.assert_awaited()
        
        # Get the arguments passed to the first call of _atake_next_step
        # call_args is a tuple (args, kwargs) or a CallArgs object
        # For an async mock, this would be await_args
        # assert_awaited() implies it was awaited at least once.
        # To get args of the first await:
        first_await_args = mock_executor_instance._atake_next_step.await_args_list[0]
        
        # The 'inputs' dict is passed as a keyword argument to _atake_next_step
        inputs_arg = first_await_args.kwargs.get('inputs', {})
        
        assert inputs_arg.get("input") == test_query
        # Check for the presence of context items in the inputs
        assert inputs_arg.get("user_id") == run_context["user_id"]
        assert inputs_arg.get("session_info") == run_context["session_info"]

    @pytest.mark.asyncio
    async def test_astream_with_context_passes_to_executor(self, initialized_agent: JtechMCPAgent):
        # Similar to test_run_with_context, but for astream
        # astream calls _generate_response_chunks_async, which calls _agent_executor.astream_events
        mock_executor_instance = initialized_agent._agent_executor
        
        # Mock astream_events on the executor instance. It should be an async generator.
        async def mock_astream_events_generator(*args, **kwargs):
            # Yield some mock StreamEvent or any event structure your agent expects
            mock_event = MagicMock(name="StreamEvent") # Replace with actual StreamEvent if needed
            mock_event.event = "on_chat_model_stream" # Example event type
            mock_event.data = {"chunk": "some streamed data"}
            yield mock_event
            # To signify completion for some stream consumers, you might need a final event
            # or just let the generator exit.

        mock_executor_instance.astream_events = mock_astream_events_generator
        # If astream_events is already an AsyncMock, configure its return_value
        # For an AsyncMock to be an async iterator, its return_value should be an async iterator
        # or it should be configured with side_effect to be an async generator function.
        # If it's a new attribute, assign the generator.
        # If it's an existing AsyncMock, reconfigure:
        # mock_executor_instance.astream_events.side_effect = mock_astream_events_generator


        test_query = "Test query for astream context"
        astream_context = {"stream_param": "value123", "user_id": "stream_user"}

        # Consume the async generator from astream
        async for _ in initialized_agent.astream(test_query, context=astream_context):
            pass # We just want to check the call to astream_events

        # Check how astream_events was called
        # If astream_events was assigned directly (not an AsyncMock attribute),
        # we'd need to patch it or wrap it.
        # Assuming it's an AsyncMock attribute of mock_executor_instance:
        
        # If mock_executor_instance.astream_events was already an AsyncMock:
        # mock_executor_instance.astream_events.assert_awaited() # Not quite, it's an async iter
        # We need to check its call arguments.
        # For an async generator, call_args might capture the first call that sets it up.

        # Let's re-mock astream_events as an AsyncMock specifically for this test
        # to capture its arguments easily.
        mock_executor_instance.astream_events = AsyncMock(side_effect=mock_astream_events_generator)

        async for _ in initialized_agent.astream(test_query, context=astream_context):
            pass
            
        mock_executor_instance.astream_events.assert_called_once() # Use assert_called_once for async iterators if appropriate for your mock setup
        call_args = mock_executor_instance.astream_events.call_args
        
        inputs_arg = call_args.args[0] # astream_events is called with (inputs, **kwargs)
        
        assert inputs_arg.get("input") == test_query
        assert inputs_arg.get("stream_param") == astream_context["stream_param"]
        assert inputs_arg.get("user_id") == astream_context["user_id"]

```
