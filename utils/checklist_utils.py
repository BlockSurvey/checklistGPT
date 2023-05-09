from typing import Dict, List
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
