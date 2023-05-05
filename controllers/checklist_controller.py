from agents.checklist_generator import ChecklistGenerator
from agents.checklist_prompt_generator import ChecklistPromptGenerator


class ChecklistController():
    checklist_agent_id: str
    checklist_prompt_generator: ChecklistPromptGenerator
    checklist_generator: ChecklistGenerator

    def __init__(self, checklist_agent_id: str):
        self.checklist_agent_id = checklist_agent_id
        self.checklist_prompt_generator = ChecklistPromptGenerator(
            self.checklist_agent_id)
        self.checklist_generator = ChecklistGenerator(self.checklist_agent_id)

    def generate_checklist_prompt(self, checklist_name, checklist_project, checklist_organization):
        # Null validation
        if ((self.checklist_agent_id is None or self.checklist_agent_id == "") or
            (checklist_name is None or checklist_name == "") or
            (checklist_project is None or checklist_project == "") or
                (checklist_organization is None or checklist_organization == "")):
            return "Checklist agent id, checklist name, checklist project and checklist organization cannot be null"

        generated_prompt = self.checklist_prompt_generator.generate_prompt(
            checklist_name, checklist_project, checklist_organization)
        return generated_prompt

    def generate_checklist(self, checklist_prompt):
        # Null validation
        if ((self.checklist_agent_id is None or self.checklist_agent_id == "") or
                (checklist_prompt is None or checklist_prompt == "")):
            return "Checklist agent id and checklist prompt cannot be null"

        # generated_checklist = self.checklist_generator.generate_checklist(
        #     checklist_prompt)

        generated_checklist = self.checklist_generator.generate_checklist_using_subsequent_chain(
            checklist_prompt)

        return generated_checklist
