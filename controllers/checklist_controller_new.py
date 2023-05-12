import uuid
from typing import Any, Dict, List

from agents.checklist_generator import ChecklistGenerator
from agents.checklist_prompt_generator import ChecklistPromptGenerator
from utils.agent_utils import (create_agent, create_agent_manager_and_agent,
                               get_organization_agent_managers_by_id)
from utils.checklist_utils import save_checklist
from utils.utils import get_user_id


class ChecklistControllerNew():
    org_id: str
    project_id: str
    name: str
    project: str
    organization: str
    agent_manager_id: str

    # Dependencies

    def __init__(self, org_id: str, project_id: str, name: str, project: str, organization: str, agent_manager_id: str) -> None:
        self.org_id = org_id
        self.project_id = project_id
        self.name = name
        self.project = project
        self.organization = organization
        self.agent_manager_id = agent_manager_id

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

    def generate_checklist(self):
        # Null validation
        if ((self.org_id is None or self.org_id == "") or
           (self.name is None or self.name == "") or
           (self.project is None or self.project == "") or
           (self.organization is None or self.organization == "") or
           (self.agent_manager_id is None or self.agent_manager_id == "")):
            raise ValueError("Missing required parameters")

        try:
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
                self.name, self.project, self.organization)

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

            # Create a checklist to DB
            insert_checklist = self.process_generated_checklist(
                agent_manager_id, generated_checklist, self.project_id)
            checklist_mutation_result = save_checklist(insert_checklist)

            # Create a agent to generate a metadata
            # Generate metadata
            # Store the metadata result

            # Store the metadata with checklist
            return checklist_mutation_result
        except ValueError as e:
            raise e
