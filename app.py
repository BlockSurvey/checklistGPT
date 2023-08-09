import json

import jwt
from flask import Flask, g, jsonify, request
from flask_cors import CORS

import config
from config import JWT_SECRET
from controllers.checklist_controller import ChecklistController
from controllers.checklist_controller_new import ChecklistControllerNew
from controllers.checklist_metadata_controller import ChecklistMetadataController
from controllers.checklist_from_document import ChecklistFromDocument
from utils.agent_utils import get_agent_by_id
from utils.utils import is_valid_url

app = Flask(__name__)
CORS(app)


@app.before_request
def token_required():
    if request.method != 'OPTIONS':
        # Exclude some routes from token verification, for example the login route
        # if request.path == '/login':
        #     return None

        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return jsonify({'error': {'message': 'Token is missing!'}}), 400

        jwtSecretObject = json.loads(JWT_SECRET)

        try:
            token = auth_header.split(' ')[1]
            payload = jwt.decode(
                token, jwtSecretObject['key'], algorithms=['HS256'])
            # Store the decoded payload in the 'g' object
            g.jwt_session = payload
        except jwt.ExpiredSignatureError:
            return jsonify({'error': {'message': 'Token has expired!'}}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': {'message': 'Invalid token!'}}), 401


@app.route('/generate-checklist-prompt', methods=['POST'])
def generate_checklist_prompt_api():
    payload = request.get_json()
    checklist_agent_id = payload.get("agent_id", None)
    checklist_name = payload.get("name", None)
    checklist_project = payload.get("project", None)
    checklist_organization = payload.get("organization", None)

    # Null validation
    if ((checklist_agent_id is None or checklist_agent_id == "") or
        (checklist_name is None or checklist_name == "") or
        (checklist_project is None or checklist_project == "") or
            (checklist_organization is None or checklist_organization == "")):
        return jsonify({'error': {'message': 'Checklist agent id, checklist name, checklist project and checklist organization cannot be null'}}), 400

    agentDetails = get_agent_by_id(checklist_agent_id)
    if (agentDetails.get("data", None) is None or agentDetails["data"].get("agents", None) is None or
            len(agentDetails["data"]["agents"]) == 0):
        return jsonify({'error': {'message': 'Oops! Agent not found'}}), 400

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
    checklist_agent_id = payload.get("agent_id", None)
    checklist_prompt = payload.get("prompt", None)

    # Null validation
    if ((checklist_agent_id is None or checklist_agent_id == "") or
            (checklist_prompt is None or checklist_prompt == "")):
        return jsonify({'error': {'message': 'Checklist agent id and checklist prompt cannot be null'}}), 400

    agentDetails = get_agent_by_id(checklist_agent_id)
    if (agentDetails.get("data", None) is None or agentDetails["data"].get("agents", None) is None or
            len(agentDetails["data"]["agents"]) == 0):
        return jsonify({'error': {'message': 'Oops! Agent not found'}}), 400

    checklist = ChecklistController(checklist_agent_id)
    result = checklist.generate_checklist(
        checklist_prompt)
    response = {
        "data": {
            "result": result
        }
    }
    return jsonify(response)


@app.route('/generate-checklist-using-ai', methods=['POST'])
def generate_checklist_using_ai_api():
    payload = request.get_json()
    org_id = payload.get("orgId", None)
    project_id = payload.get("projectId", None)
    name = payload.get("name", None)
    project = payload.get("project", None)
    organization = payload.get("organization", None)
    agent_manager_id = payload.get("id", None)

    # Null validation
    if ((org_id is None or org_id == "") or
        (project_id is None or project_id == "") or
        (name is None or name == "") or
        (project is None or project == "") or
            (agent_manager_id is None or agent_manager_id == "")):
        return jsonify({'error': {'message': 'Missing parameters'}}), 400

    try:
        checklist = ChecklistControllerNew(
            org_id, project_id, name, project, organization, agent_manager_id)
        checklist.generate_checklist()

        return jsonify({
            "data": {
                "message": "Checklist generated successfully",
            }
        }), 200
    except ValueError as error:
        print("An error occurred:", error)
        return jsonify({'error': {'message': str(error)}}), 500


@app.route('/generate-checklist-metadata', methods=['POST'])
def generate_checklist_metadata():
    payload = request.get_json()
    checklist = payload.get("checklist", None)
    tasks = payload.get("tasks", None)

    if (checklist is None or checklist == ""):
        return jsonify({'error': {'message': 'Checklist cannot be null'}}), 400

    if (tasks is None or len(tasks) == 0):
        return jsonify({'error': {'message': 'Tasks cannot be null'}}), 400

    try:
        checklist_metadata_generator = ChecklistMetadataController()
        result = checklist_metadata_generator.generate_checklist_metadata(
            checklist,
            tasks)

        return jsonify({"data": {
            "metadata": result
        }})
    except ValueError as error:
        print("An error occurred:", error)
        return jsonify({'error': {'message': str(error)}}), 500


@app.route('/generate-checklist-from-document', methods=['POST'])
def generate_checklist_from_document():
    if 'file' not in request.files:
        return jsonify({'error': {'message': 'Missing parameters'}}), 400

    file = request.files['file']

    # Fetch payload data (form data)
    org_id = request.form.get('orgId', default=None)
    project_id = request.form.get('projectId', default=None)

    # Validation
    if ((org_id is None or org_id == "") or (project_id is None or project_id == "") or (file.filename == '')):
        return jsonify({"error": {"message": "Missing parameters"}}), 400

    ALLOWED_CONTENT_TYPES = {'application/pdf', 'text/plain'}
    if (file.content_type not in ALLOWED_CONTENT_TYPES):
        return jsonify({"error": {"message": "File type not allowed."}}), 400

    try:
        checklist_from_document = ChecklistFromDocument(org_id, project_id)
        result = checklist_from_document.generate_checklist_from_document(
            file, file.content_type, file.filename)

        return jsonify({"data": {
            "checklistId": result
        }})
    except ValueError as error:
        print("An error occurred:", error)
        return jsonify({'error': {'message': str(error)}}), 500


@app.route('/generate-checklist-from-url', methods=['POST'])
def generate_checklist_from_url():
    payload = request.get_json()
    org_id = payload.get("orgId", None)
    project_id = payload.get("projectId", None)
    url = payload.get("url", None)

    if ((org_id is None or org_id == "") or (project_id is None or project_id == "") or (url is None or url == "")):
        return jsonify({'error': {'message': 'Missing parameters'}}), 400

    if (is_valid_url(url) == False):
        return jsonify({'error': {'message': 'Invalid URL'}}), 400

    try:
        checklist_from_document = ChecklistFromDocument(org_id, project_id)
        result = checklist_from_document.generate_checklist_from_url(url)

        return jsonify({"data": {
            "checklistId": result
        }})
    except ValueError as error:
        print("An error occurred:", error)
        return jsonify({'error': {'message': str(error)}}), 500


@app.route('/generate-checklist-from-text', methods=['POST'])
def generate_checklist_from_text():
    payload = request.get_json()
    org_id = payload.get("orgId", None)
    project_id = payload.get("projectId", None)
    text = payload.get("text", None)

    if ((org_id is None or org_id == "") or (project_id is None or project_id == "") or (text is None or text == "")):
        return jsonify({'error': {'message': 'Missing parameters'}}), 400

    words = text.split()

    if (len(words) < 100):
        return jsonify({'error': {'message': 'Text should contain minimum of 100 words'}}), 400
    elif len(words) > 5000:
        return jsonify({'error': {'message': 'Text should contain maximum of 5000 words'}}), 400

    try:
        checklist_from_document = ChecklistFromDocument(org_id, project_id)
        result = checklist_from_document.generate_checklist_from_text(
            text, " ".join(words[0:10]))

        return jsonify({"data": {
            "checklistId": result
        }})
    except ValueError as error:
        print("An error occurred:", error)
        return jsonify({'error': {'message': str(error)}}), 500


@app.route('/')
def root_path():
    return 'It is working...'


# if __name__ == '__main__':
#     app.run(host='localhost', port=8080, debug=True, threaded=True)
