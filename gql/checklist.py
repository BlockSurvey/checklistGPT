CREATE_MULTIPLE_CHECKLIST_MUTATION = """
  mutation CreateMultipleChecklist($checklist: [checklist_insert_input!]!) {
    insert_checklist(
      objects: $checklist
    ) {
      affected_rows
    }
  }
"""

CREATE_MULTIPLE_CHECKLIST_WITH_STATUS_INDICATORS_MUTATION = """
  mutation CreateMultipleChecklistWithStatusIndicators($checklist: [checklist_insert_input!]!, $checklist_status_indicators: [checklist_status_indicators_insert_input!]!) {
    insert_checklist(
      objects: $checklist
    ) {
      affected_rows
    }

    insert_checklist_status_indicators(
      objects: $checklist_status_indicators
    ) {
      affected_rows
    }
  }
"""