from langchain.chains import LLMChain
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate

from agents.checklist_prompt_generator import ChecklistPromptGenerator


class ChecklistController():
    checklist_agent_id: str

    def __init__(self, checklist_agent_id: str):
        self.checklist_agent_id = checklist_agent_id

    def generate_checklist(self):
        # Null validation
        if (self.checklist_agent_id is None or self.checklist_agent_id == ""):
            return "Checklist agent id cannot be null"

        print("started")
        checklist_prompt_generator = ChecklistPromptGenerator(
            self.checklist_agent_id)
        generated_prompt = checklist_prompt_generator.generate_prompt()
        print("ended")
        return generated_prompt
        # generated_prompt = "Create a detailed and efficient checklist for preparing a CARO report in accordance with the Indian corporate law, including all necessary requirements and considerations for ensuring a comprehensive and effective report. To ensure the checklist remains up-to-date and relevant, regularly review and update it based on feedback from users, changes to regulatory requirements and industry standards, emerging risks and threats, and comparison to similar checklists used in other industries or jurisdictions. Take steps to ensure the accuracy and completeness of the checklist, including verifying information, involving relevant stakeholders, and complying with all relevant regulations and guidelines."
        print(generated_prompt)

        # if (finalPrompt["iterations"] and len(finalPrompt["iterations"]) > 0 and finalPrompt["iterations"][0]["prompt"]):
        #     finalPrompt = finalPrompt["iterations"][0]["prompt"]

        # gpt-3.5-turbo / gpt-4
        llm = OpenAI(temperature=0.5, model_name="gpt-3.5-turbo")

        dynamicTemplate = """
            {final_prompt}

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
                    "title" : "",
                    "tasks" : [ 
                        // list of sub tasks in the checklist
                        "title" : "", // sub task title
                        "tasks": [ 
                            // if possible list of sub sub tasks in the checklist
                            "title" : "",
                            "tasks" : [ 
                                // list of sub tasks in the checklist
                                "title" : "" // sub task title
                            ]
                        ]
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
        result = chain.run(generated_prompt)
        print(result)
        return result
