from gql.agent import GET_AGENT_BY_ID_QUERY
from services.hasura_service import HasuraService


def get_agent_by_id(agent_id):
    if (agent_id is None or agent_id == ""):
        raise ValueError("agent_id is required")

    # get agent by id from database
    hasura_service = HasuraService()
    result = hasura_service.execute(GET_AGENT_BY_ID_QUERY, {
        "agent_id": agent_id
    })

    return result
