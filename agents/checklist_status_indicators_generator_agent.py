
from langchain.chains import LLMChain
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate

from utils.langchain.langchain_utils import parse_agent_result_and_get_json


class ChecklistStatusIndicatorsGeneratorAgent():
    # Variables
    llm = OpenAI(temperature=0.5, model_name="gpt-3.5-turbo")

    def __init__(self) -> None:
        pass

    def generate_status_indicators(self, title, tasks):
        # Chain to generate a checklist
        llm = self.llm
        dynamic_template = """You are a helpful assistant to generate a set of "status indicators" for checklist tasks. Generate a set of "status indicators" to convey the current condition or state of each item on the the given Checklist,

            Checklist: "{checklist}"
            Tasks: "{tasks}"
            
            In order to generate a set of "status indicators" we will follow the following rules: 
                - Understand the given above few tasks of the checklist and it has more tasks
                - **Ensure status indicators align with the checklist's purpose & constraints**.
                - It should be more generic to all task
                - It should have only one positive status indicators and should be a past tense.
                - It should have only one negative status indicators and should be a past tense.
                - It should have only one re-action to the negative status indicators (like "Need attention", "Need repair", "Need review")
                - Don't include in progress states like "in hold", "in progress", "Pending"
                - Include "Not Applicable(N/A)" in the list of status indicators if it is required and it should be last one
                - It should be a single word (or) max of three words
                - It should be only 4 unique status indicators
            
            {format_instructions}"""
        checklist_format_instructions = """The output should be a markdown code snippet formatted in the following schema, including the leading and trailing "\`\`\`json" and "\`\`\`":

            ```json
            {
                "status_indicators" : [
                    // List of status indicators as string
                ]
            }
            ```"""
        prompt_template = PromptTemplate(
            input_variables=["checklist", "tasks"], template=dynamic_template, partial_variables={"format_instructions": checklist_format_instructions})
        status_indicators_creator_chain = LLMChain(
            llm=llm, prompt=prompt_template)

        result = status_indicators_creator_chain.run(
            {"checklist": title, "tasks": ", ".join(tasks)})

        # Parse the output and get JSON
        json_result = parse_agent_result_and_get_json(result)

        return json_result
