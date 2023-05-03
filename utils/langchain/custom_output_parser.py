import re
from typing import Union
from flask import g

from langchain.agents import AgentOutputParser
from langchain.schema import AgentAction, AgentFinish

from gql.agent import INSERT_AGENT_RESULT
from services.hasura_service import HasuraService


class CustomOutputParser(AgentOutputParser):
    checklist_agent_id: str

    def parse(self, llm_output: str) -> Union[AgentAction, AgentFinish]:
        # Check if agent should finish
        if "Final Answer:" in llm_output:
            self.store_results(llm_output.split(
                "Final Answer:")[-1].strip())
            return AgentFinish(
                # Return values is generally always a dictionary with a single `output` key
                # It is not recommended to try anything else at the moment :)
                return_values={"output": llm_output.split(
                    "Final Answer:")[-1].strip()},
                log=llm_output,
            )
        # Parse out the action and action input
        regex = r"Action\s*\d*\s*:(.*?)\nAction\s*\d*\s*Input\s*\d*\s*:[\s]*(.*)"
        match = re.search(regex, llm_output, re.DOTALL)
        if not match:
            # raise ValueError(f"Could not parse LLM output: `{llm_output}`")
            self.store_results(llm_output.strip())
            return AgentFinish(
                # Return values is generally always a dictionary with a single `output` key
                # It is not recommended to try anything else at the moment :)
                return_values={"output": llm_output.strip()},
                log=llm_output,
            )

            # action = "PromptGenerator"
            # action_input = "Generate a final prompt using the prompt generator based on your research"
            # return AgentAction(tool=action, tool_input=action_input.strip(" ").strip('"'), log=llm_output)

        action = match.group(1).strip()
        action_input = match.group(2)
        return AgentAction(tool=action, tool_input=action_input.strip(" ").strip('"'), log=llm_output)

    def store_results(self, observation):
        userId = ""
        if g.get('jwt_session', {}).get('sub', None) is None:
            return
        else:
            userId = g.jwt_session.get('sub')

        hasura_service = HasuraService()
        agent_result = {
            "agent_id": self.checklist_agent_id,
            "thoughts": "",
            "action": "FinalAnswer",
            "action_input": "",
            "results": observation,
            "is_final_answer": True,
            "created_by": userId
        }
        hasura_service.execute(INSERT_AGENT_RESULT, {
            "agent_result": agent_result
        })
