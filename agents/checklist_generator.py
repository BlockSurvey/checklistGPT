
from langchain.chains import LLMChain
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate


class ChecklistGenerator():

    def generate_checklist(self, generated_prompt: str):
        # gpt-3.5-turbo / gpt-4
        llm = OpenAI(temperature=0.5, model_name="gpt-3.5-turbo")

        dynamicTemplate = """
            {final_prompt}

             In order to do this we will follow the following process: 
                - Identify the tasks: Make a list of all the tasks required to achieve your goal. Try to be as specific as possible and break down larger tasks into smaller, more manageable steps.
                - Prioritize tasks: Determine the order in which tasks should be completed. Consider factors such as dependencies, time constraints, and importance when prioritizing tasks.
                - Keep it simple: A checklist should be simple and straightforward, so try to avoid adding too many details or making it too complex. Focus on the essentials and keep it short and sweet.
                - Number of tasks: Minimum number of task and subtasks should be around 15 always. 

            Note: Ask yourself relevant questions and improve the quality of the checklist creation and generate minimum of 15 tasks and subtasks.

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
        return result
