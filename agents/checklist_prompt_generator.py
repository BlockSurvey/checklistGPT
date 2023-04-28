from langchain.agents import AgentExecutor, LLMSingleActionAgent, Tool
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.utilities import GoogleSearchAPIWrapper

from utils.langchain.custom_output_parser import CustomOutputParser
from utils.langchain.custom_prompt_template import CustomPromptTemplate


class ChecklistPromptGenerator():
    # Variables
    checklist_agent_id: str

    def __init__(self, checklist_agent_id: str):
        self.checklist_agent_id = checklist_agent_id

    def generate_prompt(self):
        # gpt-3.5-turbo / gpt-4
        llm = ChatOpenAI(
            temperature=0.5, model_name="gpt-3.5-turbo")

        prompt_creator_prompt = PromptTemplate.from_template(
            "Generate or improve the quality of the prompt for checklist creation. Improve this prompt: {text}"
        )
        prompt_creator_chain = LLMChain(
            llm=llm, prompt=prompt_creator_prompt)

        relevant_prompt = PromptTemplate.from_template(
            "You are an expert to come up with more relevant questions for a given objective. Come up with a relevant question list for this objective: {objective}"
        )
        relevant_chain = LLMChain(llm=llm, prompt=relevant_prompt)

        google_search = GoogleSearchAPIWrapper()

        tools = [
            Tool(
                name="PromptGenerator",
                func=prompt_creator_chain.run,
                description="useful for reviewing, generating, re-iterating and refining a prompt, you could use this tool to generate a prompt",
            ),
            Tool(
                name="Search",
                func=google_search.run,
                description="useful for when you need to answer questions about current events or status. Even if the answer is not found in Search tool, you could use this tool to find the answer.",
            ),
            Tool(
                name="RelevantQuestions",
                func=relevant_chain.run,
                description="useful for when you need to come up with relevant questions for the given objective. Input: an objective to create a relevant question list. Output: a relevant question list for that objective. Please be very clear what the objective is!",
            )
        ]

        # Set up the base template
        template = """Create a prompt for checklist as best you can by asking relevant questions, You have access to the following tools:

        {tools}

        Use the following format:

        Guidelines: the input guidelines you must use to generate a prompt for checklist creation
        Thought: you should always ask yourself relevant questions and improve the quality of the prompt for checklist creation
        Action: the action to take, should be one of [{tool_names}]
        Action Input: the input to the action
        Observation: the result of the action
        ... (this Thought/Action/Action Input/Observation can repeat N times)
        Thought: I now know the final answer
        Final Answer: the final answer should be a well refined and actionable prompt

        Begin! Remember that your final answer should be a well refined and actionable prompt

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
        output_parser = CustomOutputParser()
        tool_names = [tool.name for tool in tools]
        agent = LLMSingleActionAgent(llm_chain=llm_chain, output_parser=output_parser, stop=[
            "\nObservation:"], allowed_tools=tool_names, return_intermediate_steps=True)
        agent_executor = AgentExecutor.from_agent_and_tools(
            agent=agent, tools=tools, verbose=True)
        guidelines = """
            I want you to become my checklist master creator, by helping me to create the best possible checklist. 

            In order to do this we will follow the following process: 


            - Based on the "checklist_name" I give you, you will generate the following: 
            - An improved prompt for the checklist creation with standard, guidelines and methodologies for "industry". 
            - Ask yourself relevant questions and improve the quality of the checklist creation prompt. 
            - We will go through this process repeatedly three times to arrive at a final prompt

            checklist_name: on-page SEO checklist
            industry: software
            team or project: SEO
        """
        output = agent_executor.run(guidelines)
        return output


# generatePrompt(1)
