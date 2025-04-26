from langchain.chains import LLMChain
from langchain.llms import OpenAI
from langchain_core.prompts.prompt import PromptTemplate

import concurrent.futures

from utils.langchain.langchain_utils import parse_agent_result_and_get_json


class ChecklistMetadataGenerator():
    # Variables
    llm = OpenAI(temperature=0.5, model_name="gpt-3.5-turbo")

    def bulk_generate_metadata(self, checklist, tasks):

        def generate_metadata(task):
            # Chain to generate a checklist
            llm = self.llm
            dynamic_template = """You are an expert checklist metadata creator. It is your job to create very clear metadata for the given below Task of Checklist,
            
                Checklist: "{checklist}"
                Task: "{task}"

                In order to do this we will follow the following rules:
                    - Ask relevant questions: Ask yourself relevant questions and improve the quality of the task metadata
                    - Generate a detailed description that helps to understand the task
                    - Generate list of references if applicable
                
                Begin: Remember ask relevant questions to improve the quality of the task metadata
                
                {format_instructions}"""
            checklist_format_instructions = """The output should be a markdown code snippet formatted in the following schema, including the leading and trailing "\`\`\`json" and "\`\`\`":

                ```json
                {
                    "description" : "", // Generate a detailed description that helps to understand the task
                    "references" : [
                        // List of references links to understand in detail for completing the task
                    ],
                    "completion_criteria" : "", // Defining specific criteria or metrics that determine the successful completion of the task.
                    "complexity" : "", // Predict the complexity of the task for the given checklist, it should be either Low/Medium/High
                    "priority" : "", // Predict the priority of the task for the given checklist, it should be either Low/Medium/High
                    "estimated_time_to_complete" : "", // Predict the estimated time to complete in minutes. It should be a number.
                    "frequency" : "", // Predict the frequency of the task. It should be either Daily/Monthly/Quarterly/Yearly.
                    "instructions" : [] // List of instructions
                }
                ```"""
            prompt_template = PromptTemplate(
                input_variables=["checklist", "task"], template=dynamic_template, partial_variables={"format_instructions": checklist_format_instructions})
            task_metadata_creation_chain = LLMChain(
                llm=llm, prompt=prompt_template)

            result = task_metadata_creation_chain.run(
                {"checklist": checklist, "task": task})

            # Parse the output and get JSON
            json_result = parse_agent_result_and_get_json(result)

            # Append task with result back for reference
            json_result['task'] = task

            return json_result

        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = list(executor.map(generate_metadata, tasks))
            return results
