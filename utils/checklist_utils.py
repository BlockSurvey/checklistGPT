import uuid
from typing import Any, Dict, List

from gql.checklist import CREATE_MULTIPLE_CHECKLIST_MUTATION
from services.hasura_service import HasuraService
from utils.utils import get_user_id


def save_checklist(insert_checklist: List[Dict]):
    if (insert_checklist is None or len(insert_checklist) == 0):
        raise ValueError("Checklist must present to insert.")

    # get agent by id from database
    hasura_service = HasuraService()
    result = hasura_service.execute(CREATE_MULTIPLE_CHECKLIST_MUTATION, {
        "checklist": insert_checklist
    })

    return result


def process_generated_checklist(agent_manager_id: str, generated_checklist: Any, project_id: str):
    if generated_checklist and generated_checklist.get('title') and generated_checklist.get('tasks') and len(generated_checklist.get('tasks')) > 0:
        insert_checklist = []
        root_node = {
            'id': str(uuid.uuid4()),
            'title': generated_checklist.get('title'),
            'order_number': 0,
            'project_id': project_id,
            "created_by": get_user_id(),
            "created_at": "now()"
        }
        
        if agent_manager_id:
            root_node['agent_manager_id'] = agent_manager_id

        insert_checklist.append(root_node)

        insert_child_checklist(root_node, generated_checklist.get(
            'tasks') or generated_checklist.get('subtasks'), insert_checklist, root_node['id'], project_id)

        return insert_checklist


def insert_child_checklist(root_node: Dict, tasks: List[Any], insert_checklist: List[Dict], checklist_id: str, project_id: str):
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

            insert_child_checklist(child_node, subtasks,
                                   insert_checklist, checklist_id, project_id)
