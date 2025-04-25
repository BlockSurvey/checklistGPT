from langchain.chains import LLMChain
from langchain.llms import OpenAI
from langchain_core.prompts.prompt import PromptTemplate
from utils.langchain.langchain_utils import parse_agent_result_and_get_json


class ChecklistController():
    llm = OpenAI(temperature=0.5, model_name="gpt-3.5-turbo")

    def __init__(self):
        pass

    def generate_checklist_using_prompt(self, prompt):
        # Chain to generate a checklist
        llm = self.llm
        dynamic_template = """You are an expert checklist maker/creator. It is your job to create a very clear checklist using below Prompt,
        
        Prompt: "{final_prompt}"
        
        In order to do this we will follow the following rules: 
            - Generate detailed tasks: Use given prompt to generate a more detailed checklist
            - Number of tasks: Minimum 15 tasks would be great
            - Condition: Do not start with a number or hyphen

        {format_instructions}"""
        checklist_format_instructions = """The output should be a markdown code snippet formatted in the following schema, including the leading and trailing "\`\`\`json" and "\`\`\`":

        ```json
        {
            "title" : "", // checklist title
            "tasks": [ 
                // list of tasks
            ]
        }
        ```"""

        prompt_template = PromptTemplate(
            input_variables=["final_prompt"], template=dynamic_template, partial_variables={"format_instructions": checklist_format_instructions})

        checklist_chain = LLMChain(
            llm=llm, prompt=prompt_template)

        result = checklist_chain.run(
            {"final_prompt": prompt})

        return result

    def generate_checklist(self, prompt):
        # Null validation
        if (prompt is None or prompt == ""):
            return "Checklist prompt cannot be null"

        generated_checklist_string = self.generate_checklist_using_prompt(
            prompt)

        # Parse the output and get JSON
        generated_checklist = parse_agent_result_and_get_json(
            generated_checklist_string)

        return generated_checklist
