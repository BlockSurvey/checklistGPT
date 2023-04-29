
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