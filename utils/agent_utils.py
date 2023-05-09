from gql.agent import GET_AGENT_BY_ID_QUERY, GET_ORGANIZATION_AGENT_MANAGERS_QUERY, CREATE_AGENT_MANAGER_AND_AGENT_MUTATION, CREATE_AGENT_AGENT_MUTATION
from services.hasura_service import HasuraService
from utils.utils import get_user_id


def get_agent_by_id(agent_id):
    if (agent_id is None or agent_id == ""):
        raise ValueError("agent_id is required")

    # get agent by id from database
    hasura_service = HasuraService()
    result = hasura_service.execute(GET_AGENT_BY_ID_QUERY, {
        "agent_id": agent_id
    })

    return result


def get_organization_agent_managers_by_id(org_id):
    if (org_id is None or org_id == ""):
        raise ValueError("org_id is required")

    # get agent by id from database
    hasura_service = HasuraService()
    result = hasura_service.execute(GET_ORGANIZATION_AGENT_MANAGERS_QUERY, {
        "org_id": org_id
    })

    return result


def create_agent_manager_and_agent(agent_manager_id: str, agent_manager_name: str, agent_id: str,  agent_name: str, org_id: str, checklist_name: str):
    if ((agent_manager_id is None or agent_manager_id == "") or
            (agent_id is None or agent_id == "")):
        raise ValueError("agent_manager_id and agent_id are required")

    # get agent by id from database
    hasura_service = HasuraService()
    result = hasura_service.execute(CREATE_AGENT_MANAGER_AND_AGENT_MUTATION, {
        "agentManager": {
            "id": agent_manager_id,
            "name": agent_manager_name,
            "org_id": org_id,
            "created_by": get_user_id()
        },
        "agent": {
            "id": agent_id,
            "name": agent_name,
            "agent_manager_id": agent_manager_id,
            "created_by": get_user_id()
        }
    })

    return result


def create_agent(agent_manager_id: str, agent_id: str, agent_name: str):
    if ((agent_manager_id is None or agent_manager_id == "") or
        (agent_id is None or agent_id == "") or
            (agent_name is None or agent_name == "")):
        raise ValueError("agent_manager_id, agent_id, agent_name are required")

    # get agent by id from database
    hasura_service = HasuraService()
    result = hasura_service.execute(CREATE_AGENT_AGENT_MUTATION, {
        "agent": {
            "id": agent_id,
            "name": agent_name,
            "agent_manager_id": agent_manager_id,
            "created_by": get_user_id()
        }
    })

    return result
