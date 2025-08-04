import asyncio
import os

from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from dotenv import load_dotenv
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.tools.mcp import McpWorkbench, StdioServerParams, SseServerParams

# Load environment variables from .env file
load_dotenv()
server_params=StdioServerParams(
        command="docker",
        args=[
            "run",
            "-i",
            "--rm",
            "-e", f"GITHUB_PERSONAL_ACCESS_TOKEN={os.getenv('GITHUB_API_KEY')}",
            "ghcr.io/github/github-mcp-server",
        ],)

async def FirstProgram():
    model_client= OpenAIChatCompletionClient(model="gemini-1.5-flash-8b")
    #client = ChatCompletionClient.load_component(config)
    agent1 = AssistantAgent(name="PoliticalExpert",model_client=model_client,system_message=""" How is politics in Andhra Pradesh""")
    agent2 = AssistantAgent(name="Citizen", model_client=model_client,system_message=""" You are Citizen of Andhra Pradesh""")
    team= RoundRobinGroupChat(participants=[agent1,agent2],termination_condition=MaxMessageTermination(max_messages=4))
    await Console(team.run_stream(task="Let disucss about politics of Andhra Pradesh"))
    async with McpWorkbench(server_params=server_params) as workbench:
        agent3 = AssistantAgent(name="MCPForGitHub", model_client=model_client, workbench=workbench,system_message="""After 
         Completion of 2 agent tasks please use this to push the code to github
         If there is no .yml file in the appropriate directory, create a new one with the content:
         name: AgenticAILatest Once push the code to github please start the execution""")
        # Initialize UserProxyAgent
        user_proxy = UserProxyAgent(
            name="user_proxy"  # Set to ALWAYS to always prompt for human input
            # Prompt for human input at each step
        )
        team2 = RoundRobinGroupChat(participants=[user_proxy, agent3],
                                   termination_condition=TextMentionTermination("GITHUB PUSH COMPLETED"))
        await Console(team2.run_stream(task="Let Push the Code to GitHub"))
    await model_client.close()

asyncio.run(FirstProgram())