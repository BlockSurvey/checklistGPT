from langchain.agents import AgentExecutor, LLMSingleActionAgent, Tool, AgentType
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain_google_community import GoogleSearchAPIWrapper

from utils.langchain.custom_output_parser import CustomOutputParser
from utils.langchain.custom_prompt_template import CustomPromptTemplate


class ChecklistPromptGenerator():
    # Variables
    checklist_agent_id: str

    def __init__(self, checklist_agent_id: str):
        self.checklist_agent_id = checklist_agent_id

    def generate_prompt(self, checklist_name, checklist_project, checklist_organization, checklist_role):
        # gpt-3.5-turbo / gpt-4
        llm = ChatOpenAI(
            temperature=0.5, model="gpt-3.5-turbo")

        prompt_creator_prompt = PromptTemplate.from_template(
            "You are an expert in generating a very detailed and clear prompt for checklist creation. Ensure the generated checklist follows the exact instructions, quantities, steps, and details given in '{text}'. Do NOT omit, modify, or generalize any steps unless explicitly instructed and include any details, material or content mentioned."
        )
        prompt_creator_chain = LLMChain(
            llm=llm, prompt=prompt_creator_prompt)

        relevant_prompt = PromptTemplate.from_template(
            "You are an expert to come up with relevant questions for a given objective. Extract and ensure compliance with all steps, instructions, quantities, and details given in '{objective}'"
        )
        relevant_chain = LLMChain(llm=llm, prompt=relevant_prompt)

        llm_search_prompt = PromptTemplate.from_template(
            "You are an assistant who is an expert at answering questions about anything. Answer this question: {question}"
        )
        llm_search_chain = LLMChain(llm=OpenAI(
            temperature=0), prompt=llm_search_prompt)

        google_search = GoogleSearchAPIWrapper()

        tools = [
            Tool(
                name="PromptGenerator",
                func=prompt_creator_chain.run,
                description="useful for reviewing, generating, re-iterating and refining a prompt, you could use this tool to generate a prompt",
            ),
            Tool(
                name="WebSearch",
                func=google_search.run,
                description="useful for when you need to answer questions about current events or status. Even if the answer is not found in Search tool, you could use this tool to find the answer.",
            ),
            Tool(
                name="RelevantQuestions",
                func=relevant_chain.run,
                description="useful for when you need to come up with relevant questions for the given objective. Input: an objective to create a relevant question list. Output: a relevant question list for that objective. Please be very clear what the objective is!",
            ),
            Tool(
                name="LLMSearch",
                func=llm_search_chain.run,
                description="useful for when you need to answer the question. I am trained large language model with global data till Jun 2021. Input: a question. Output: the answer. Please be very clear what the question is!",
            ),
        ]

        # Set up the base template
        template = """Generate a prompt as best you can by asking relevant questions and finding answers for given guidelines, You have access to the following tools:

        {tools}

        Use the following format:

        Guidelines: the input guidelines you must use to generate a prompt for checklist creation
        Thought: you should always ask yourself relevant questions, find answer and improve the quality of the prompt for checklist creation
        Action: the action to take, should be one of [{tool_names}]
        Action Input: the input to the action
        Observation: the result of the action
        ... (this Thought/Action/Action Input/Observation can repeat N times)
        Thought: I now know the final answer
        Final Answer: the final answer should be a very detailed prompt to create a checklist for given guidelines

        Begin! Remember that your final answer should be a very clear and detailed prompt

        Guidelines: {input}
        {agent_scratchpad}"""
        prompt = CustomPromptTemplate(
            template=template,
            tools=tools,
            # This omits the `agent_scratchpad`, `tools`, and `tool_names` variables because those are generated dynamically
            # This includes the `intermediate_steps` variable because that is needed
            input_variables=["input", "intermediate_steps"],
            checklist_agent_id=self.checklist_agent_id
        )
        llm_chain = LLMChain(llm=llm, prompt=prompt)
        output_parser = CustomOutputParser(
            checklist_agent_id=self.checklist_agent_id)

        tool_names = [tool.name for tool in tools]
        agent = LLMSingleActionAgent(llm_chain=llm_chain, output_parser=output_parser, stop=[
            "\nObservation:"], allowed_tools=tool_names, agent=AgentType.OPENAI_FUNCTIONS)
        agent_executor = AgentExecutor.from_agent_and_tools(
            agent=agent, tools=tools,llm=llm)

        guidelines = """
            Generate a refined, more-detailed prompt to create a "{checklist_name}" checklist for the role of "{checklist_role}" in the "{checklist_organization}" industry.

            in order to improve the prompt, follow the following process:
            - An improved prompt for the checklist creation with standard, guidelines and methodologies for the role of "{checklist_role}" in the "{checklist_organization}" industry.
            - Ensure **strict adherence** to include any **specific numbers, steps, tasks, details, material, content or instructions** from "{checklist_name}"
            - Format the checklist with **structured methodologies and best practices** relevant to "{checklist_role}" in the "{checklist_organization}" industry. 
        """.format(checklist_name=checklist_name, checklist_organization=checklist_organization, checklist_role=checklist_role)

        # If the checklist_role is None or empty
        if (checklist_role is None or checklist_role == ""):
            guidelines = """
                Generate a refined, more-detailed prompt to create a "{checklist_name}" checklist.

                in order to improve the prompt, follow the following process:
                - An improved prompt for the checklist creation with standard, guidelines and methodologies for the "{checklist_organization}" industry. 
                - Ensure **strict adherence** to include any **specific numbers, steps, tasks, details, material, content or instructions** from "{checklist_name}"
                - Format the checklist with **structured methodologies and best practices** relevant to the "{checklist_organization}" industry.  
            """.format(checklist_name=checklist_name, checklist_organization=checklist_organization)
        # If the checklist_organization is None or empty
        if (checklist_organization is None or checklist_organization == ""):
            guidelines = """
                Generate a refined, more-detailed prompt to create a "{checklist_name}" checklist.

                in order to improve the prompt, follow the following process:
                - An improved prompt for the checklist creation with standard, guidelines and methodologies
            """.format(checklist_name=checklist_name)

        output = agent_executor.invoke(guidelines)
        return output

        # project: {checklist_project}
