import html
from os import close
import gc

from utils.langchain.document_loaders.docx_loader import DocxLoader
from utils.langchain.document_loaders.pdf_loader import PdfLoader
from utils.langchain.document_loaders.url_loader import UrlLoader
from utils.langchain.document_loaders.txt_loader import TxtLoader
from utils.langchain.document_loaders.csv_loader import CsvLoader
from utils.langchain.document_loaders.excel_loader import ExcelLoader
from utils.langchain.document_loaders.image_loader import ImageLoader

from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain_core.runnables import RunnableSequence
from langchain_core.prompts.prompt import PromptTemplate
from utils.langchain.langchain_utils import parse_agent_result_and_get_json
from utils.langchain.document_loaders.document_loader_abc import DocumentLoaderInterface
from utils.langchain.document_loaders.document_utils import DocumentUtils
import concurrent.futures
from utils.embeddings_utils import EmbeddingUtils
from utils.checklist_utils import save_checklist_with_status_indicators, process_generated_checklist, process_generated_status_indicators
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings

from agents.checklist_status_indicators_generator_agent import ChecklistStatusIndicatorsGeneratorAgent

import numpy as np
from sklearn.cluster import KMeans

# from memory_profiler import profile


class ChecklistFromDocument:
    org_id = None
    project_id = None
    embedding_utils = EmbeddingUtils()
    document_utils = DocumentUtils()

    llm = ChatOpenAI(temperature=0.5, model="gpt-3.5-turbo")

    def __init__(self, org_id, project_id) -> None:
        self.org_id = org_id
        self.project_id = project_id
        pass

    def generate_embeddings_from_text(self, text):
        # Text splitter
        text_splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", " ", "", "\t"], chunk_size=10000, chunk_overlap=500)
        splitted_docs = text_splitter.create_documents([text])

        embeddings_model = OpenAIEmbeddings()

        embeddings = embeddings_model.embed_documents(
            [doc.page_content for doc in splitted_docs])

        # Delete the object
        del embeddings_model

        return {
            "splitted_docs": splitted_docs,
            "embeddings": embeddings
        }

    def form_cluster(self, num_clusters, embeddings):
        kmeans = KMeans(n_clusters=num_clusters,
                        random_state=42).fit(embeddings)
        return kmeans

    def get_closest_points_from_kmeans(self, num_clusters, embeddings, kmeans):
        closest_indices = []
        for i in range(num_clusters):
            distances = np.linalg.norm(
                embeddings - kmeans.cluster_centers_[i], axis=1)
            closest_index = np.argmin(distances)
            closest_indices.append(closest_index)

        return closest_indices

    def summarize_selected_docs(self, selected_docs):

        def summarize_doc(doc):
            # Chain to generate a checklist
            llm = self.llm
            dynamic_template = """You are an expert summarizer for given any text. It is your job to generate a summary for the given below text. Text will be enclosed in triple backticks.
            
            Text: ```{text}```

            In order to do this we will follow the following rules:
                - Goal is to give a paragraph summary that reader will have a full understanding
                - Summary should be concise and easy to read
                - It should be an prompt to generate a checklist
            """

            prompt_template = PromptTemplate(
                input_variables=["text"], template=dynamic_template)

            summarization_chain: RunnableSequence = prompt_template | llm

            result = summarization_chain.invoke(
                {"text": doc})

            return result

        # with concurrent.futures.ThreadPoolExecutor() as executor:
        #     results = list(executor.map(summarize_doc, selected_docs))
        #     return results

        executor = concurrent.futures.ThreadPoolExecutor()

        # Submitting tasks to the executor and gathering future objects
        futures = [executor.submit(summarize_doc, selected_doc)
                   for selected_doc in selected_docs]

        # Waiting for all tasks to complete
        results = [future.result()
                   for future in concurrent.futures.as_completed(futures)]

        # Explicitly shutting down the executor
        executor.shutdown()

        return results

    def generate_prompt(self, summarized_docs):
        joined_summarized_docs = "\n".join([doc.content if hasattr(doc, 'content') else str(doc) for doc in summarized_docs])

        # Chain to generate a checklist
        llm = self.llm
        dynamic_template = """You are an expert prompt generator for checklist creation. It is your job to generate a Prompt from given summarized text,
        
        Summarized Text: ```{text}```

        In order to do this we will follow the following rules:
            - Prompt should be concise and easy to read
            - It should be an prompt to generate a checklist
        """

        prompt_template = PromptTemplate(
            input_variables=["text"], template=dynamic_template)

        summarization_chain: RunnableSequence = prompt_template | llm

        result = summarization_chain.invoke(
            {"text": joined_summarized_docs})

        return result

    def generate_checklist_using_prompt(self, prompt):
        # Chain to generate a checklist
        llm = self.llm
        dynamic_template = """You are an expert checklist maker/creator. It is your job to create a very clear checklist using below Prompt,
        
        Prompt: "{final_prompt}"
        
        Follow these rules strictly:
            - The **total number of tasks must always be maximum 10.**
            - 10 maximum tasks are to be generated, do not add subtasks.
        
        In order to do this we will follow the following rules:
            - Ask relevant questions: Ask yourself relevant questions and improve the quality of the checklist
            - Identify the tasks: Make a list of all the tasks required to achieve your goal. Try to be as specific as possible and break down larger tasks into smaller, more manageable steps
            - Generate detailed tasks: Use given prompt to generate a more detailed checklist and subtasks
            - Prioritize tasks: Determine the order in which tasks should be completed. Consider factors such as dependencies, time constraints, and importance when prioritizing tasks

        Begin: Remember ask relevant questions to improve the quality of the checklist. Ensure the checklist is practical, structured, and within the 10-item limit.
        
        Important: Never exceed 10 tasks in total. If tasks exceed the limit, combine or prioritize to stay within 10 tasks total.

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

        checklist_chain = LLMChain(
            llm=llm, prompt=prompt_template)

        result = checklist_chain.run(
            {"final_prompt": prompt})

        return result

    def generate_checklist(self, text, name, md5_hash, prompt):
        if text is None or text == "":
            raise ValueError("Content not found in the file.")

        embeddings = None
        splitted_docs = None

        # Fetch embeddings from database if it exists
        fetched_embeddings = self.embedding_utils.fetch_embeddings_from_database(
            md5_hash, self.org_id)
        if (fetched_embeddings is None):
            result = self.generate_embeddings_from_text(text)
            embeddings = result.get("embeddings")
            splitted_docs = result.get("splitted_docs")

            # Save embeddings to database
            self.embedding_utils.save_embeddings(splitted_docs, embeddings,
                                                 name, md5_hash, self.org_id)
        else:
            embeddings = fetched_embeddings.get("embeddings", None)
            splitted_docs = fetched_embeddings.get("splitted_docs", None)

        # Validation
        if (embeddings is None or splitted_docs is None or len(embeddings) != len(splitted_docs)):
            raise ValueError("Embeddings or splitted_docs not found")

        # Calculate the number of clusters
        num_clusters = len(splitted_docs)
        if num_clusters >= 2 and num_clusters <= 5:
            num_clusters = 2
        elif num_clusters > 5 and num_clusters <= 10:
            num_clusters = 3
        elif num_clusters > 10 and num_clusters <= 15:
            num_clusters = 4
        elif num_clusters > 15 and num_clusters <= 20:
            num_clusters = 5
        elif num_clusters > 20:
            num_clusters = ((10/50)*len(splitted_docs))
            # Convert num_clusters to int
            num_clusters = int(num_clusters)

        kmeans = self.form_cluster(num_clusters, embeddings)
        closest_indices = self.get_closest_points_from_kmeans(
            num_clusters, embeddings, kmeans)

        selected_indices = sorted(closest_indices)
        selected_docs = [splitted_docs[selected_index]
                         for selected_index in selected_indices]

        summarized_docs = self.summarize_selected_docs(selected_docs)

        generated_prompt = self.generate_prompt(summarized_docs)

        if prompt:
            generated_prompt += f"\n{prompt}"

        checklist_result = self.generate_checklist_using_prompt(
            generated_prompt)

        # Parse the output and get JSON
        json_result = parse_agent_result_and_get_json(checklist_result)

        # Clear object
        del fetched_embeddings
        del embeddings
        del splitted_docs

        del kmeans
        del closest_indices
        del selected_indices
        del selected_docs

        del summarized_docs
        del generated_prompt

        del checklist_result

        gc.collect()

        return json_result

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

    def get_document_loader(self, uploaded_file, uploaded_file_content_type) -> DocumentLoaderInterface:
        if uploaded_file_content_type == "application/pdf":
            return PdfLoader(uploaded_file)
        elif uploaded_file_content_type == "text/plain":
            return TxtLoader(uploaded_file)
        elif uploaded_file_content_type == "text/csv":
            return CsvLoader(uploaded_file)
        elif uploaded_file_content_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" or uploaded_file_content_type == "application/vnd.ms-excel":
            return ExcelLoader(uploaded_file)
        elif uploaded_file_content_type == "image/png" or uploaded_file_content_type == "image/jpeg":
            return ImageLoader(uploaded_file)
        elif uploaded_file_content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return DocxLoader(uploaded_file)

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

    def generate_checklist_from_document(self, uploaded_file, uploaded_file_content_type, uploaded_file_name,prompt):
        if uploaded_file is None or uploaded_file_content_type is None or uploaded_file_name is None:
            raise ValueError("Content in the Uploaded file not found")

        md5_hash = self.document_utils.generate_md5_for_uploaded_file(
            uploaded_file)

        document_loader = self.get_document_loader(
            uploaded_file, uploaded_file_content_type)
        text = document_loader.get_text()

        # Generate checklist
        generated_checklist = self.generate_checklist(
            text, uploaded_file_name, md5_hash, prompt)

        # Generate status indicators
        generated_status_indicators = self.generate_status_indicators(
            generated_checklist)

        # Save checklist
        checklist_id = self.save_checklist(
            generated_checklist, generated_status_indicators)

        return checklist_id

    def generate_checklist_from_url(self, url, prompt):
        if url is None or url == "":
            raise ValueError("Content in the Uploaded URL not found")

        md5_hash = self.document_utils.generate_md5_for_text(url)

        html_loader = UrlLoader(url)
        text = html_loader.get_text()

        generated_checklist = self.generate_checklist(text, url, md5_hash, prompt)

        # Generate status indicators
        generated_status_indicators = self.generate_status_indicators(
            generated_checklist)

        # Save checklist
        checklist_id = self.save_checklist(
            generated_checklist, generated_status_indicators)

        return checklist_id

    def generate_checklist_from_text(self, text, name):
        if text is None or text == "":
            raise ValueError("Missing required parameters")

        md5_hash = self.document_utils.generate_md5_for_text(text)

        generated_checklist = self.generate_checklist(text, name, md5_hash)

        # Generate status indicators
        generated_status_indicators = self.generate_status_indicators(
            generated_checklist)

        # Save checklist
        checklist_id = self.save_checklist(
            generated_checklist, generated_status_indicators)

        return checklist_id

    def generate_minimal_checklist_using_prompt(self, prompt):
        # Chain to generate a checklist
        llm = self.llm
        dynamic_template = """You are an expert checklist maker/creator. It is your job to create a very clear checklist using below Prompt,
        
        Prompt: "{final_prompt}"
        
        In order to do this we will follow the following rules: 
            - Generate detailed tasks: Use given prompt to generate a more detailed checklist
            - Number of tasks: Minimum 15 tasks would be great
            - Do not include sequential number

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

    def generate_checklist_using_given_prompt(self, prompt, is_detailed_checklist):
        if prompt is None or prompt == "":
            raise ValueError("Missing required parameters")

        checklist_result = None
        if is_detailed_checklist is True:
            checklist_result = self.generate_checklist_using_prompt(
                prompt)
        else:
            checklist_result = self.generate_minimal_checklist_using_prompt(
                prompt)

        # Parse the output and get JSON
        generated_checklist = parse_agent_result_and_get_json(checklist_result)

        # Generate status indicators
        generated_status_indicators = self.generate_status_indicators(
            generated_checklist)

        # Save checklist
        checklist_id = self.save_checklist(
            generated_checklist, generated_status_indicators)

        return checklist_id
