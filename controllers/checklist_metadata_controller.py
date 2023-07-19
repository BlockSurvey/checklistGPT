from os import error
from agents.checklist_metadata_generator import ChecklistMetadataGenerator


class ChecklistMetadataController():

    def generate_checklist_metadata(self, tasks):
        try:
            checklist_metadata_generator = ChecklistMetadataGenerator()
            result = checklist_metadata_generator.bulk_generate_metadata(tasks)

            return result
        except ValueError as error:
            raise error
