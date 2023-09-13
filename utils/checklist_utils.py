import uuid
from typing import Any, Dict, List

from gql.checklist import CREATE_MULTIPLE_CHECKLIST_MUTATION, CREATE_MULTIPLE_CHECKLIST_WITH_STATUS_INDICATORS_MUTATION
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


def save_checklist_with_status_indicators(insert_checklist: List[Dict], insert_status_indicators: List[Dict]):
    if (insert_checklist is None or len(insert_checklist) == 0):
        raise ValueError("Checklist must present to insert.")

    # get agent by id from database
    hasura_service = HasuraService()
    result = hasura_service.execute(CREATE_MULTIPLE_CHECKLIST_WITH_STATUS_INDICATORS_MUTATION, {
        "checklist": insert_checklist,
        "checklist_status_indicators": insert_status_indicators
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

        tasks = generated_checklist.get(
            'tasks') or generated_checklist.get('subtasks')

        if isinstance(tasks[0], str):
            tasks = [{'title': task_title}
                     for task_title in tasks]

        insert_child_checklist(
            root_node, tasks, insert_checklist, root_node['id'], project_id)

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


def process_generated_status_indicators(status_indicators: List[str], checklist_id: str) -> List[Dict]:
    # Validation
    if (status_indicators is None or len(status_indicators) == 0 or checklist_id is None or checklist_id == ""):
        return []

    insert_status_indicators = []

    for index, status_indicator in enumerate(status_indicators):
        status_indicator_object = {
            'id': str(uuid.uuid4()),
            'name': status_indicator,
            'order_number': index,
            'checklist_id': checklist_id,
            "created_by": get_user_id(),
            "created_at": "now()"
        }

        insert_status_indicators.append(status_indicator_object)

    return insert_status_indicators