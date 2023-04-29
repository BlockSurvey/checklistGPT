import re
from typing import List
from flask import g

from langchain.agents import Tool
from langchain.prompts import StringPromptTemplate

from gql.agent import INSERT_AGENT_RESULT
from services.hasura_service import HasuraService


class CustomPromptTemplate(StringPromptTemplate):
    # The template to use
    template: str
    # The list of tools available
    tools: List[Tool]
    checklist_agent_id: str
    hasura_service = HasuraService()

    def format(self, **kwargs) -> str:
        # Get the intermediate steps (AgentAction, Observation tuples)
        # Format them in a particular way
        intermediate_steps = kwargs.pop("intermediate_steps")

        thoughts = ""
        for action, observation in intermediate_steps:
            thoughts += action.log
            thoughts += f"\nObservation: {observation}\nThought: "

        # Store the results of the prompt in the database
        self.store_results(thoughts)

        # Set the agent_scratchpad variable to that value
        kwargs["agent_scratchpad"] = thoughts
        # Create a tools variable from the list of tools provided
        kwargs["tools"] = "\n".join(
            [f"{tool.name}: {tool.description}" for tool in self.tools])
        # Create a list of tool names for the tools provided
        kwargs["tool_names"] = ", ".join([tool.name for tool in self.tools])
        return self.template.format(**kwargs)

    def store_results(self, thoughts):
        pattern = r"Thought:\s(.*?)\nAction:\s(.*?)\nAction Input:\s(.*?)\nObservation:\s(.*?)\n(?=Thought|$)"
        matches = re.findall(pattern, thoughts, re.DOTALL)

        userId = ""
        if g.get('jwt_session', {}).get('sub', None) is None:
            return
        else:
            userId = g.jwt_session.get('sub')

        if matches:
            thought, action, action_input, observation = matches[-1]
            agent_result = {
                "agent_id": self.checklist_agent_id,
                "thoughts": thought,
                "action": action,
                "action_input": action_input,
                "results": observation,
                "created_by": userId
            }
            self.hasura_service.execute(INSERT_AGENT_RESULT, {
                "agent_result": agent_result
            })
        else:
            print("No matches found")

        # for match in matches:
        #     thought, action, action_input, observation = match
        #     print(f"Thought: {thought}\nAction: {action}\nAction Input: {action_input}\nObservation: {observation}\n")
