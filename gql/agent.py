CREATE_AGENT_MANAGER_AND_AGENT_MUTATION = """
    mutation CreateAgentManagerAndAgent($agentManager: [agent_managers_insert_input!]!, $agent: [agents_insert_input!]!) {
        insert_agent_managers(
            objects: $agentManager
        ) {
            returning {
                id
            }
        }

        insert_agents(
            objects: $agent
        ) {
            returning {
                id
            }
        }
    }
"""

CREATE_AGENT_AGENT_MUTATION = """
    mutation CreateAgentMutation($agent: [agents_insert_input!]!) {
        insert_agents(
            objects: $agent
        ) {
            returning {
                id
            }
        }
    }
"""

GET_AGENT_BY_ID_QUERY = """
    query getAgentById($agent_id: uuid!) {
        agents(where: {id: {_eq: $agent_id}}) {
            id
            name
        }
    }
"""

INSERT_AGENT_RESULT = """
    mutation insert_agent_result($agent_result: agent_results_insert_input!) {
        insert_agent_results (objects: [$agent_result]) {
            returning {
                id
            }
            affected_rows
        }
    }
"""

GET_ORGANIZATION_AGENT_MANAGERS_QUERY = """
    query GetOrganization($org_id: uuid!) {
        organization(where: {id: {_eq: $org_id}}) {
            agent_managers {
                id
            }
            pricing_subscription {
                pricing_plan {
                    pricing_limitations(where: {type: {_eq: "ai_checklists"}}) {
                        id
                        type
                        value_type
                        value
                    }
                }
            }
        }
    }
"""
