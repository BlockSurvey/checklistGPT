import uuid
import re, json
from typing import Any, Dict, List

from agents.checklist_generator import ChecklistGenerator
from agents.checklist_prompt_generator import ChecklistPromptGenerator
from utils.agent_utils import (create_agent, create_agent_manager_and_agent,
                               get_organization_agent_managers_by_id)
from utils.checklist_utils import save_checklist_with_status_indicators, process_generated_status_indicators
from utils.utils import get_user_id

from agents.checklist_status_indicators_generator_agent import ChecklistStatusIndicatorsGeneratorAgent

class ChecklistUsingAgentController():
    org_id: str
    project_id: str
    name: str
    project: str
    organization: str
    agent_manager_id: str
    role: str

    # Dependencies

    def __init__(self, org_id: str, project_id: str, name: str, project: str, organization: str, agent_manager_id: str, role: str) -> None:
        self.org_id = org_id
        self.project_id = project_id
        self.name = name
        self.project = project
        self.organization = organization
        self.agent_manager_id = agent_manager_id
        self.role = role

    def org_limit_validation(self) -> bool:
        query_result = get_organization_agent_managers_by_id(self.org_id)
        if (query_result.get("data", None) is None or
            query_result["data"].get("organization", None) is None or
                len(query_result["data"]["organization"]) == 0):
            raise ValueError("You are not a member of the organization")

        org_data = query_result["data"]["organization"][0]

        if (org_data.get("pricing_subscription", None) is None or
            org_data["pricing_subscription"].get("pricing_plan", None) is None or
                org_data["pricing_subscription"]["pricing_plan"].get("pricing_limitations", None) is None or
                len(org_data["pricing_subscription"]["pricing_plan"]["pricing_limitations"]) == 0):
            raise ValueError(
                "Organization pricing plan limitation is not set")

        ai_checklists_limitation_count = org_data["pricing_subscription"][
            "pricing_plan"]["pricing_limitations"][0]["value"]

        agent_managers = []
        if (org_data.get("agent_managers", None) is not None):
            agent_managers = org_data["agent_managers"]

        if (len(agent_managers) >= int(ai_checklists_limitation_count)):
            raise ValueError(
                "AI Checklist limit reached for this organization. Please upgrade or contact support.")

        return True

    def process_generated_checklist(self, agent_manager_id: str, generated_checklist: Any, project_id: str):
        if generated_checklist and generated_checklist.get('title') and generated_checklist.get('tasks') and len(generated_checklist.get('tasks')) > 0:
            insert_checklist = []
            root_node = {
                'id': str(uuid.uuid4()),
                'title': generated_checklist.get('title'),
                'order_number': 0,
                'project_id': project_id,
                'agent_manager_id': agent_manager_id,
                "created_by": get_user_id(),
                "created_at": "now()"
            }

            insert_checklist.append(root_node)

            self.insert_child_checklist(root_node, generated_checklist.get(
                'tasks') or generated_checklist.get('subtasks'), insert_checklist, root_node['id'], project_id)

            return insert_checklist

    def insert_child_checklist(self, root_node: Dict, tasks: List[Any], insert_checklist: List[Dict], checklist_id: str, project_id: str):
        for index, task in enumerate(tasks):
            child_node = {
                'id': str(uuid.uuid4()),
                'title': task.get('title'),
                'description': task.get('description'),
                'order_number': index,
                'parent_id': root_node['id'],
                'checklist_id': checklist_id,
                'project_id': project_id,
                'priority': task.get('priority'),
                'time_estimate': task.get('time_estimate'),
                "created_by": get_user_id(),
                "created_at": "now()"
            }

            insert_checklist.append(child_node)

            if ((task.get('tasks') and len(task.get('tasks')) > 0) or (task.get('subtasks') and len(task.get('subtasks')) > 0)):
                subtasks = task.get('tasks') or task.get('subtasks')

                if isinstance(subtasks[0], str):
                    subtasks = [{'title': subtask_title}
                                for subtask_title in subtasks]

                self.insert_child_checklist(child_node, subtasks,
                                            insert_checklist, checklist_id, project_id)

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

    def generate_checklist(self):
        # Null validation
        if ((self.org_id is None or self.org_id == "") or
           (self.name is None or self.name == "") or
           (self.project is None or self.project == "") or
           (self.agent_manager_id is None or self.agent_manager_id == "")):
            raise ValueError("Missing required parameters")

        # Free organization can have only three agentMangers
        self.org_limit_validation()

        # Create an agentManager and agent
        agent_manager_id = self.agent_manager_id
        agent_manager_name = "Agent Manager for checklist - " + self.name
        prompt_generator_agent_id = str(uuid.uuid4())
        agent_name = "Agent for checklist prompt generator - " + self.name
        agent_manager_mutation_result = create_agent_manager_and_agent(
            agent_manager_id, agent_manager_name, prompt_generator_agent_id, agent_name, self.org_id, self.name)

        # Validate the mutations
        if (agent_manager_mutation_result.get("data", None) is None or
            agent_manager_mutation_result["data"].get("insert_agent_managers", None) is None or
            agent_manager_mutation_result["data"]["insert_agent_managers"].get("returning", None) is None or
            len(agent_manager_mutation_result["data"]["insert_agent_managers"]["returning"]) == 0 or
            agent_manager_mutation_result["data"].get("insert_agents", None) is None or
            agent_manager_mutation_result["data"]["insert_agents"].get("returning", None) is None or
                len(agent_manager_mutation_result["data"]["insert_agents"]["returning"]) == 0):
            raise ValueError("Agent Manager creation is failed")

        # Generate and a prompt
        checklist_prompt_generator = ChecklistPromptGenerator(
            prompt_generator_agent_id)
        generated_prompt = checklist_prompt_generator.generate_prompt(
            self.name, self.project, self.organization, self.role)

        # Create a agent to generate a checklist
        checklist_generator_agent_id = str(uuid.uuid4())
        checklist_generator_agent_name = "Agent for checklist generator - " + self.name
        agent_manager_mutation_result = create_agent(
            agent_manager_id, checklist_generator_agent_id, checklist_generator_agent_name)

        # Store the checklist result
        checklist_generator = ChecklistGenerator(
            checklist_generator_agent_id)
        generated_checklist = checklist_generator.generate_checklist_using_subsequent_chain(
            generated_prompt)
                
        raw = generated_checklist.get("output", "")
        # match ```json ... ```
        m = re.search(r"```json\s*(\{.*\})\s*```", raw, re.DOTALL)
        if not m:
            raise ValueError("Could not find JSON in LLM output.")

        parsed = json.loads(m.group(1))
        # now `parsed` is a dict like {"title": "...", "tasks":[...]}

        # Generate status indicators
        generated_status_indicators = self.generate_status_indicators(
            parsed)

        # Pre-process checklist to store in DB
        insert_checklist = self.process_generated_checklist(
            agent_manager_id, parsed, self.project_id)

        # Get the checklist id
        checklist_id = ""
        if insert_checklist and len(insert_checklist) > 0:
            checklist_id = insert_checklist[0].get('id')

        insert_status_indicators = process_generated_status_indicators(
            generated_status_indicators, checklist_id)

        # Save to DB
        checklist_mutation_result = save_checklist_with_status_indicators(
            insert_checklist, insert_status_indicators)

        # Create a agent to generate a metadata
        # Generate metadata
        # Store the metadata result

        # Store the metadata with checklist
        return checklist_mutation_result
