from flask import Flask, jsonify, request

import config
from controllers.checklist_controller import ChecklistController

app = Flask(__name__)


@app.route('/generate-checklist-prompt')
def generate_checklist_prompt_api():
    checklist_agent_id = request.args.get('id', None)
    checklist_name = request.args.get('name', None)
    checklist_project = request.args.get('project', None)
    checklist_organization = request.args.get('organization', None)
    checklist = ChecklistController(checklist_agent_id)
    result = checklist.generate_checklist_prompt(
        checklist_name, checklist_project, checklist_organization)
    response = {
        "data": {
            "result": result
        }
    }
    return jsonify(response)


@app.route('/generate-checklist', methods=['POST'])
def generate_checklist_api():
    payload = request.get_json()
    checklist_agent_id = payload["id"] or None
    checklist_prompt = payload["prompt"] or None
    checklist = ChecklistController(checklist_agent_id)
    result = checklist.generate_checklist(
        checklist_prompt)
    response = {
        "data": {
            "result": result
        }
    }
    return jsonify(response)


@app.route('/')
def root_path():
    return 'It is working...'


# if __name__ == '__main__':
#     app.run(host='localhost', port=8080, debug=True, threaded=True)
