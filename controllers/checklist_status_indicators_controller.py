from agents.checklist_status_indicators_generator_agent import ChecklistStatusIndicatorsGeneratorAgent


class ChecklistStatusIndicatorsController():

    def __init__(self) -> None:
        pass

    def generate_status_indicators(self, title, tasks):
        try:
            checklist_status_indicators_generator_agent = ChecklistStatusIndicatorsGeneratorAgent()
            result = checklist_status_indicators_generator_agent.generate_status_indicators(
                title, tasks)

            return result
        except ValueError as error:
            raise error
