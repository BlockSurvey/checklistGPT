from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_core.runnables import RunnableSequence
from langchain.schema import AIMessage
import json
import re

class SamplePromptsGenerator:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id

    def generate(self, job_role: str, industry: str) -> list[str]:
        llm = ChatOpenAI(model="gpt-4", temperature=0.5)
        tpl = PromptTemplate.from_template(
            """
            You are a professional prompt‐engineer.  
            Generate **6 distinct** high‑quality AI prompts (each no more than 10 words)
            which an end‑user could feed into our checklist generator to create
            a checklist for a “{job_role}” in the “{industry}” industry.  
            
            Output **only** valid JSON in this exact form (without extra keys):

            ```json
            {{
              "prompts": [
                "…prompt text 1…",
                "…prompt text 2…",
                // exactly 6 entries total
              ]
            }}
            ```

            • Each prompt must be **very specific**, **unique**, **detailed**,  
              **relevant**, and **clear**.  
            • No list items, just the prompt text itself.  
            """
        )
        chain: RunnableSequence = tpl | llm
        # invoke returns an AIMessage (or similar)
        resp = chain.invoke({"job_role": job_role, "industry": industry})

        # extract the raw text
        if isinstance(resp, AIMessage):
            raw = resp.content
        else:
            raw = str(resp)

        # now run your regex on the string
        m = re.search(r"```json\s*(\{.*\})\s*```", raw, re.DOTALL)
        payload = m.group(1) if m else raw
        
        data = json.loads(payload)
        return data.get("prompts", [])

