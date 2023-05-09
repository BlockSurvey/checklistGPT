CREATE_MULTIPLE_CHECKLIST_MUTATION = """
  mutation CreateMultipleChecklist($checklist: [checklist_insert_input!]!) {
    insert_checklist(
      objects: $checklist
    ) {
      affected_rows
    }
  }
"""
