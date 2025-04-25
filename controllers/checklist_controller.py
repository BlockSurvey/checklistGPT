from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain_core.runnables import RunnableSequence
from langchain_core.prompts.prompt import PromptTemplate
from utils.langchain.langchain_utils import parse_agent_result_and_get_json


class ChecklistController():
    llm = ChatOpenAI(temperature=0.5, model="gpt-3.5-turbo")

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

        # New PromptTemplate
        prompt_template = PromptTemplate.from_template(dynamic_template)

        # Build the RunnableSequence chain
        chain: RunnableSequence = prompt_template.partial(
            format_instructions=checklist_format_instructions
        ) | self.llm

        # Invoke the chain with the prompt
        result = chain.invoke({"final_prompt": prompt})

        return result.content 

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
