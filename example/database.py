import asyncio
import os
from dotenv import load_dotenv
from jtech_mcp_executor import JtechMCPAgent, JtechMCPClient
from langchain_google_genai import ChatGoogleGenerativeAI

async def postgres():
    load_dotenv()

    client = JtechMCPClient.from_config_file("/jtech/projects/code/jtech-mcp-executor/example/postgres-mcp.json")

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
    )

    agent = JtechMCPAgent(llm=llm, client=client, max_steps=30)
    
    try:
        result = await agent.run(
            """
            Preciso saber qual o faturamento os meses de janeiro até março, tabela revenue_forecast somente para plasticos, 
            apresente o valor em Reais (R$)""",
            max_steps=30,
        )
        print(f"\nResultado >>>: {result}")
    finally:
        if client.sessions:
            await client.close_all_sessions()

if __name__ == "__main__":
    asyncio.run(postgres())
