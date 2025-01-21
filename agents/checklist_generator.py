
import json
import re

import regex
from flask import g
from langchain.chains import LLMChain, SimpleSequentialChain
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate

from gql.agent import INSERT_AGENT_RESULT
from services.hasura_service import HasuraService
from utils.utils import is_json
from utils.langchain.langchain_utils import parse_agent_result_and_get_json


class ChecklistGenerator():
    # Variables
    checklist_agent_id: str
    hasura_service = HasuraService()

    def __init__(self, checklist_agent_id: str):
        self.checklist_agent_id = checklist_agent_id

    def store_results(self, generated_checklist):
        userId = ""
        if g.get('jwt_session', {}).get('sub', None) is None:
            return
        else:
            userId = g.jwt_session.get('sub')

        # Convert to string if JSON
        generated_checklist_str = generated_checklist
        if is_json(generated_checklist_str):
            generated_checklist_str = json.dumps(generated_checklist)

        agent_result = {
            "agent_id": self.checklist_agent_id,
            "thoughts": "Generate a checklist based on the generated prompt",
            "action": "GenerateChecklist",
            "action_input": "Generate a checklist based on the generated prompt",
            "results": generated_checklist_str,
            "is_final_answer": True,
            "created_by": userId
        }
        self.hasura_service.execute(INSERT_AGENT_RESULT, {
            "agent_result": agent_result
        })

    def generate_checklist_using_subsequent_chain(self, generated_prompt: str):
        # Chain to generate a checklist
        llm = OpenAI(temperature=0.5, model_name="gpt-3.5-turbo")
        dynamic_template = """You are an expert checklist maker/creator. It is your job to create a very clear and detailed checklist using below Prompt,
            
            Prompt: "{final_prompt}"
            
             In order to do this we will follow the following rules: 
                - Ask relevant questions: Ask yourself relevant questions and improve the quality of the checklist
                - Identify the tasks: Make a list of all the tasks required to achieve your goal. Try to be as specific as possible and break down larger tasks into smaller, more manageable steps
                - Generate detailed tasks: Use given prompt to generate a more detailed checklist and detailed subtasks
                - Prioritize tasks: Determine the order in which tasks should be completed. Consider factors such as dependencies, time constraints, and importance when prioritizing tasks
                - Tasks Limit: The total number of tasks, including subtasks, must not exceed 15. This is mandatory.

            Begin: Remember ask relevant questions to improve the quality of the checklist
            
            Important: Do not return half results, return full results. Never exceed 15 tasks (including subtasks) in total. If tasks exceed the limit, combine or prioritize to stay within 15 tasks/subtasks total.
            
            {format_instructions}"""
        checklist_format_instructions = """The output should be a markdown code snippet formatted in the following schema, including the leading and trailing "\`\`\`json" and "\`\`\`":

            ```json
            {
                "title" : "", // checklist title
                "tasks": [ // list of tasks in the checklist
                    "title" : "", // task title
                    "subtasks" : [ 
                        // list of sub tasks
                    ]
                ]
            }
            ```"""
        prompt_template = PromptTemplate(
            input_variables=["final_prompt"], template=dynamic_template, partial_variables={"format_instructions": checklist_format_instructions})
        checklist_creation_chain = LLMChain(llm=llm, prompt=prompt_template)

        # This is the overall chain where we run these all the chains in sequence.
        overall_chain = SimpleSequentialChain(
            chains=[checklist_creation_chain])
        result = overall_chain.run(generated_prompt)

        # Parse the output and get JSON
        json_result = parse_agent_result_and_get_json(result)

        self.store_results(json_result)

        return json_result
