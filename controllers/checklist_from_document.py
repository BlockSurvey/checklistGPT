import html
from os import close
from utils.langchain.document_loaders.pdf_loader import PdfLoader
from utils.langchain.document_loaders.url_loader import UrlLoader
from utils.langchain.document_loaders.txt_loader import TxtLoader

from langchain.chains import LLMChain
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from utils.langchain.langchain_utils import parse_agent_result_and_get_json
from utils.langchain.document_loaders.document_loader_abc import DocumentLoaderInterface
from utils.langchain.document_loaders.document_utils import generate_embeddings_from_text
from utils.langchain.document_loaders.document_utils import generate_md5_for_uploaded_file, generate_md5_for_text
import concurrent.futures
from utils.embeddings_utils import save_embeddings, fetch_embeddings_from_database
from utils.checklist_utils import save_checklist, process_generated_checklist

import numpy as np
from sklearn.cluster import KMeans


class ChecklistFromDocument:
    org_id = None
    project_id = None

    def __init__(self, org_id, project_id) -> None:
        self.org_id = org_id
        self.project_id = project_id
        pass

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
            llm = OpenAI(temperature=0.5, model_name="gpt-3.5-turbo")
            dynamic_template = """You are an expert summarizer for given any text. It is your job to generate a summary for the given below text. Text will be enclosed in triple backticks.
            
            Text: ```{text}```

            In order to do this we will follow the following rules:
                - Goal is to give a paragraph summary that reader will have a full understanding
                - Summary should be concise and easy to read
                - It should be an prompt to generate a checklist
            """

            prompt_template = PromptTemplate(
                input_variables=["text"], template=dynamic_template)

            summarization_chain = LLMChain(
                llm=llm, prompt=prompt_template)

            result = summarization_chain.run(
                {"text": doc})

            return result

        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = list(executor.map(summarize_doc, selected_docs))
            return results

    def generate_prompt(self, summarized_docs):
        joined_summarized_docs = "\n".join(summarized_docs)

        # Chain to generate a checklist
        llm = OpenAI(temperature=0.5, model_name="gpt-3.5-turbo")
        dynamic_template = """You are an expert prompt generator for checklist creation. It is your job to generate a Prompt from given summarized text,
        
        Summarized Text: ```{text}```

        In order to do this we will follow the following rules:
            - Prompt should be concise and easy to read
            - It should be an prompt to generate a checklist
        """

        prompt_template = PromptTemplate(
            input_variables=["text"], template=dynamic_template)

        summarization_chain = LLMChain(
            llm=llm, prompt=prompt_template)

        result = summarization_chain.run(
            {"text": joined_summarized_docs})

        return result

    def generate_checklist_using_prompt(self, prompt):

        # Chain to generate a checklist
        llm = OpenAI(temperature=0.5, model_name="gpt-3.5-turbo")
        dynamic_template = """You are an expert checklist maker/creator. It is your job to create a very clear checklist using below Prompt,
        
        Prompt: "{final_prompt}"
        
        In order to do this we will follow the following rules: 
            - Ask relevant questions: Ask yourself relevant questions and improve the quality of the checklist
            - Identify the tasks: Make a list of all the tasks required to achieve your goal. Try to be as specific as possible and break down larger tasks into smaller, more manageable steps
            - Generate detailed tasks: Use given prompt to generate a more detailed checklist and detailed subtasks
            - Prioritize tasks: Determine the order in which tasks should be completed. Consider factors such as dependencies, time constraints, and importance when prioritizing tasks
            - Number of tasks: Minimum 15 tasks would be great

        Begin: Remember ask relevant questions to improve the quality of the checklist

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

    def generate_checklist(self, text, name, md5_hash):
        if text is None or text == "":
            raise ValueError("Missing required parameters")

        embeddings = None
        splitted_docs = None

        # Fetch embeddings from database if it exists
        fetched_embeddings = fetch_embeddings_from_database(
            md5_hash, self.org_id)
        if (fetched_embeddings is None):
            result = generate_embeddings_from_text(text)
            embeddings = result.get("embeddings")
            splitted_docs = result.get("splitted_docs")

            # Save embeddings to database
            save_embeddings(splitted_docs, embeddings,
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

        checklist_result = self.generate_checklist_using_prompt(
            generated_prompt)

        # Parse the output and get JSON
        json_result = parse_agent_result_and_get_json(checklist_result)

        return json_result

    def get_document_loader(self, uploaded_file, uploaded_file_content_type) -> DocumentLoaderInterface:
        if uploaded_file_content_type == "application/pdf":
            return PdfLoader(uploaded_file)
        elif uploaded_file_content_type == "text/plain":
            return TxtLoader(uploaded_file)

    def save_checklist(self, generated_checklist):
        # Create a checklist to DB
        insert_checklist = process_generated_checklist(
            "", generated_checklist, self.project_id)
        save_checklist(insert_checklist)

        checklist_id = ""
        if insert_checklist and len(insert_checklist) > 0:
            checklist_id = insert_checklist[0].get('id')

        return checklist_id

    def generate_checklist_from_document(self, uploaded_file, uploaded_file_content_type, uploaded_file_name):
        if uploaded_file is None or uploaded_file_content_type is None or uploaded_file_name is None:
            raise ValueError("Missing required parameters")

        md5_hash = generate_md5_for_uploaded_file(uploaded_file)

        document_loader = self.get_document_loader(
            uploaded_file, uploaded_file_content_type)
        text = document_loader.get_text()

        generated_checklist = self.generate_checklist(
            text, uploaded_file_name, md5_hash)

        # Save checklist
        checklist_id = self.save_checklist(generated_checklist)

        return checklist_id

    def generate_checklist_from_url(self, url):
        if url is None or url == "":
            raise ValueError("Missing required parameters")

        md5_hash = generate_md5_for_text(url)

        html_loader = UrlLoader(url)
        text = html_loader.get_text()

        generated_checklist = self.generate_checklist(text, url, md5_hash)

        # Save checklist
        checklist_id = self.save_checklist(generated_checklist)

        return checklist_id

    def generate_checklist_from_text(self, text, name):
        if text is None or text == "":
            raise ValueError("Missing required parameters")

        md5_hash = generate_md5_for_text(text)

        generated_checklist = self.generate_checklist(text, name, md5_hash)

        # Save checklist
        checklist_id = self.save_checklist(generated_checklist)

        return checklist_id

    def generate_checklist_using_given_prompt(self, prompt):
        if prompt is None or prompt == "":
            raise ValueError("Missing required parameters")

        checklist_result = self.generate_checklist_using_prompt(
            prompt)

        # Parse the output and get JSON
        generated_checklist = parse_agent_result_and_get_json(checklist_result)

        # Save checklist
        checklist_id = self.save_checklist(generated_checklist)

        return checklist_id
