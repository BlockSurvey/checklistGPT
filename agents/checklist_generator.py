
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


class ChecklistGenerator():
    # Variables
    checklist_agent_id: str
    hasura_service = HasuraService()

    def __init__(self, checklist_agent_id: str):
        self.checklist_agent_id = checklist_agent_id

    def generate_checklist(self, generated_prompt: str):
        # gpt-3.5-turbo / gpt-4
        llm = OpenAI(temperature=0.5, model_name="gpt-3.5-turbo")

        dynamicTemplate = """
            Create a checklist using below Prompt,
            Prompt: "{final_prompt}"

             In order to do this we will follow the following process: 
                - Identify the tasks: Make a list of all the tasks required to achieve your goal. Try to be as specific as possible and break down larger tasks into smaller, more manageable steps.
                - Prioritize tasks: Determine the order in which tasks should be completed. Consider factors such as dependencies, time constraints, and importance when prioritizing tasks.
                - Keep it simple: A checklist should be simple and straightforward, so try to avoid adding too many details or making it too complex. Focus on the essentials and keep it short and sweet.
                - Number of tasks: Minimum number of tasks should be around 15 always and maximum of 30.

            Note: Ask yourself relevant questions and improve the quality of the checklist creation and generate minimum of 15 tasks and subtasks.

            Task metadata: Please include the following information for each task in the checklist:
                - Task description
                - Task time estimate
                - Task priority
                - Task dependencies
                - Task reference links, if possible
                - Task subtasks
                - Task subtasks description
                - Task subtasks time estimate
                - Task subtasks dependencies
                - Task subtasks priority
            
            Additionally, please include the following information at the end of the checklist:

            Ideal frequency for running the checklist
            Potential stakeholders for review with their role names used in the organization
            Citations and references for the standards and guidelines used in creating the checklist with URLs

            {format_instructions}
        """

        format_instructions = """
            The output should be a markdown code snippet formatted in the following schema, including the leading and trailing "\`\`\`json" and "\`\`\`":

            ```json
            {
                "title": string  // title of the checklist
                "tasks": [ 
                    // list of tasks in the checklist
                    "title" : "", // task title, it should be an actionable sentence
                    "description" : "", // task description, it should be little more descriptive of the task"
                    "time_estimate" : "", // task time estimate
                    "priority" : "", // task priority
                    "dependencies" : "", // task dependencies
                    "reference_links" : "", // task reference links, if possible
                    "subtasks" : [ 
                        // list of sub tasks in the checklist
                        "title" : "", // task title, it should be an actionable sentence
                        "description" : "", // task description, it should be little more descriptive of the task"
                        "time_estimate" : "", // task time estimate
                        "priority" : "", // task priority
                        "dependencies" : "", // task dependencies
                        "reference_links" : "" // task reference links, if possible
                    ]
                ]
            }
            ```
        """

        prompt = PromptTemplate(
            input_variables=["final_prompt"],
            template=dynamicTemplate,
            partial_variables={"format_instructions": format_instructions}
        )

        chain = LLMChain(llm=llm, prompt=prompt)
        generated_checklist = chain.run(generated_prompt)

        # Parse the output and get JSON
        pattern = r'```json(.*?)```'
        match = re.search(pattern, generated_checklist, re.DOTALL)
        if match:
            json_string = match.group(1)
            generated_checklist = json.loads(json_string)
        else:
            json_pattern = r'\{(?:[^{}]|(?R))*\}'
            match = regex.search(json_pattern, generated_checklist)
            if match:
                json_string = match.group()
                generated_checklist = json.loads(json_string)
            else:
                print("No match found")

        self.store_results(generated_checklist)

        return generated_checklist

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

    def parse_result_and_get_json(self, result):
        result_string = result
        # Parse the output and get JSON
        pattern = r'```json(.*?)```'
        match = re.search(pattern, result_string, re.DOTALL)
        if match:
            json_string = match.group(1)
            result_string = json.loads(json_string)
        else:
            json_pattern = r'\{(?:[^{}]|(?R))*\}'
            match = regex.search(json_pattern, result_string)
            if match:
                json_string = match.group()
                result_string = json.loads(json_string)
            else:
                print("No match found")

        return result_string

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
                - Number of tasks: Minimum 15 tasks would be great

            Begin: Remember ask relevant questions to improve the quality of the checklist
            
            Important: Do not return half results, return full results.
            
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
        json_result = self.parse_result_and_get_json(result)

        self.store_results(json_result)

        return json_result
