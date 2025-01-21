import openai
from utils.langchain.document_loaders.docx_loader import DocxLoader
from utils.langchain.document_loaders.pdf_loader import PdfLoader
from utils.langchain.document_loaders.url_loader import UrlLoader
from utils.langchain.document_loaders.txt_loader import TxtLoader
from utils.langchain.document_loaders.csv_loader import CsvLoader
from utils.langchain.document_loaders.excel_loader import ExcelLoader
from utils.langchain.document_loaders.image_loader import ImageLoader

from langchain.chains import LLMChain
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from utils.langchain.langchain_utils import parse_agent_result_and_get_json
from utils.langchain.document_loaders.document_loader_abc import DocumentLoaderInterface
from utils.langchain.document_loaders.document_utils import DocumentUtils
from utils.checklist_utils import save_checklist_with_status_indicators, process_generated_checklist, process_generated_status_indicators
from langchain.text_splitter import RecursiveCharacterTextSplitter
import gc

from agents.checklist_status_indicators_generator_agent import ChecklistStatusIndicatorsGeneratorAgent

class ChecklistFromDocumentDirectText:
    org_id = None
    project_id = None
    document_utils = DocumentUtils()

    llm = OpenAI(temperature=0.5, model_name="gpt-3.5-turbo")

    def __init__(self, org_id, project_id) -> None:
        self.org_id = org_id
        self.project_id = project_id
        pass
    
    def generate_checklist_from_document(self, uploaded_file, uploaded_file_content_type, uploaded_file_name):
        if uploaded_file is None or uploaded_file_content_type is None or uploaded_file_name is None:
            raise ValueError("Content in the Uploaded file not found")

        # Extract text from the uploaded document
        document_loader = self.get_document_loader(uploaded_file, uploaded_file_content_type)
        text = document_loader.get_text()

        if not text or text.strip() == "":
            raise ValueError("No content found in the File.")

        # Directly generate a checklist from the extracted text
        checklist_result = self.generate_checklist_from_text(text)
        
        # Parse the output and get JSON
        json_result = parse_agent_result_and_get_json(checklist_result)
        
        # Generate status indicators
        generated_status_indicators = self.generate_status_indicators(
            json_result)

        # Save the checklist
        checklist_id = self.save_checklist(
            json_result, generated_status_indicators)

        return checklist_id

    def generate_checklist_from_text(self, text, prompt=None):
        """
        Converts extracted text directly into a checklist format.
        """
        llm = self.llm
        dynamic_template = """You are an expert checklist creator. Based on the provided text, create a checklist.
        
        Text: ```{text}```
        
        Instructions:
        - Extract key actionable tasks directly from the text entirely without paraphrasing or changes.
        - Ensure all provided text is covered and used to generate tasks.
        - Limit the total number of tasks, including subtasks, to 15 while ensuring all provided text is covered. This is mandatory.
        - Create subtasks for each major task where possible.
        - If a prompt is provided, use it to refine or expand the checklist.
        - Format the checklist as a JSON object.
        - Ensure each task is clear and concise.

        Important:  Do not return half results, return full results. Do not exceed number of tasks(including subtasks) more than 15. If tasks exceed the limit, combine or prioritize to stay within 15 tasks/subtasks total.

        {format_instructions}"""

        checklist_format_instructions = """The output should be a markdown code snippet formatted in the following schema, including the leading and trailing "\`\`\`json" and "\`\`\`":

        ```json
        {
            "title": "", // checklist title based on the document
            "tasks": [
                {
                    "title": "", // main task
                    "subtasks": [ // subtasks for the task
                        ""
                    ]
                }
            ]
        }
        ```"""

        # Modify the `PromptTemplate` to handle optional `prompt`
        input_variables = ["text"]
        if prompt:
            dynamic_template += "\nAdditional Prompt: ```{prompt}```"
            input_variables.append("prompt")

        prompt_template = PromptTemplate(
            input_variables=input_variables,
            template=dynamic_template,
            partial_variables={"format_instructions": checklist_format_instructions},
        )

        checklist_chain = LLMChain(llm=llm, prompt=prompt_template)

        # Pass the parameters dynamically
        params = {"text": text}
        if prompt:
            params["prompt"] = prompt

        try:
            return checklist_chain.run(params)
        except openai.error.InvalidRequestError as e:
            if "maximum context length" in str(e):
                raise ValueError("File contents are too large to process.") from e
            else:
                raise ValueError(f"An error occurred during File processing: {str(e)}. Please try again.") from e
        except Exception as e:
            raise ValueError(f"Unexpected error while generating the checklist: {str(e)}. Please try again.") from e

    def save_checklist(self, generated_checklist, generated_status_indicators):
        # Create a checklist to DB
        insert_checklist = process_generated_checklist(
            "", generated_checklist, self.project_id)

        checklist_id = ""
        if insert_checklist and len(insert_checklist) > 0:
            checklist_id = insert_checklist[0].get('id')

        insert_status_indicators = process_generated_status_indicators(
            generated_status_indicators, checklist_id)

        save_checklist_with_status_indicators(
            insert_checklist, insert_status_indicators)

        return checklist_id

    def get_document_loader(self, uploaded_file, uploaded_file_content_type) -> DocumentLoaderInterface:
        if uploaded_file_content_type == "application/pdf":
            return PdfLoader(uploaded_file)
        elif uploaded_file_content_type == "text/plain":
            return TxtLoader(uploaded_file)
        elif uploaded_file_content_type == "text/csv":
            return CsvLoader(uploaded_file)
        elif uploaded_file_content_type in ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "application/vnd.ms-excel"]:
            return ExcelLoader(uploaded_file)
        elif uploaded_file_content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return DocxLoader(uploaded_file)
        else:
            raise ValueError("Unsupported file type")
        
    def generate_status_indicators(self, generated_checklist):
        status_indicators = []
        if generated_checklist and generated_checklist.get('title') and generated_checklist.get('tasks') and len(generated_checklist.get('tasks')) > 0:
            tasks = generated_checklist.get(
                'tasks') or generated_checklist.get('subtasks')

            # Convert to object array
            if isinstance(tasks[0], str):
                tasks = [{'title': task_title}
                         for task_title in tasks]

            # Convert to string array
            tasks = [task.get("title") for task in tasks]

            checklist_status_indicators_generator_agent = ChecklistStatusIndicatorsGeneratorAgent()
            generated_status_indicators = checklist_status_indicators_generator_agent.generate_status_indicators(
                generated_checklist.get('title'), tasks)

            if generated_status_indicators and generated_status_indicators.get('status_indicators') and len(generated_status_indicators.get('status_indicators')) > 0:
                status_indicators = generated_status_indicators.get(
                    'status_indicators')

        return status_indicators