import json
import gc

import jwt
from flask import Flask, g, jsonify, request
from flask_cors import CORS

import config
from config import JWT_SECRET
from controllers.checklist_controller import ChecklistController
from controllers.checklist_using_agent_controller import ChecklistUsingAgentController
from controllers.checklist_metadata_controller import ChecklistMetadataController
from controllers.checklist_from_document import ChecklistFromDocument
from controllers.checklist_status_indicators_controller import ChecklistStatusIndicatorsController
from utils.agent_utils import get_agent_by_id
from utils.utils import is_valid_url
from werkzeug.exceptions import RequestEntityTooLarge

# from memory_profiler import profile

app = Flask(__name__)
CORS(app)

# Set the maximum allowed content length to 50MB
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024


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


@app.route('/generate-checklist', methods=['POST'])
def generate_checklist_api():
    # Generate a checklist and it will not be persisted in database

    payload = request.get_json()
    prompt = payload.get("prompt", None)

    # Null validation
    if (prompt is None or prompt == ""):
        return jsonify({'error': {'message': 'Checklist prompt cannot be null'}}), 400

    checklist = ChecklistController()
    result = checklist.generate_checklist(
        prompt)
    response = {
        "data": {
            "result": result
        }
    }
    return jsonify(response)


@app.route('/generate-checklist-using-agent', methods=['POST'])
def generate_checklist_using_agent_api():
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
        checklist = ChecklistUsingAgentController(
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
    finally:
        gc.collect()


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
    finally:
        gc.collect()


@app.route('/generate-checklist-from-document', methods=['POST'])
# @profile
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

    ALLOWED_CONTENT_TYPES = {'application/pdf', 'text/plain', 'text/csv',
                             'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/vnd.ms-excel',
                             'application/vnd.openxmlformats-officedocument.wordprocessingml.document'}
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
    finally:
        gc.collect()


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
    finally:
        gc.collect()


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
    finally:
        gc.collect()


@app.route('/generate-checklist-using-prompt', methods=['POST'])
def generate_checklist_using_prompt():
    payload = request.get_json()
    org_id = payload.get("orgId", None)
    project_id = payload.get("projectId", None)
    prompt = payload.get("prompt", None)
    is_detailed_checklist = payload.get("isDetailedChecklist", None)

    if ((org_id is None or org_id == "") or (project_id is None or project_id == "") or (prompt is None or prompt == "")):
        return jsonify({'error': {'message': 'Missing parameters'}}), 400

    words = prompt.split()

    if (len(words) < 3):
        return jsonify({'error': {'message': 'Prompt should contain minimum of 3 words'}}), 400
    elif len(words) > 100:
        return jsonify({'error': {'message': 'Text should contain maximum of 100 words'}}), 400

    try:
        checklist_from_document = ChecklistFromDocument(org_id, project_id)
        result = checklist_from_document.generate_checklist_using_given_prompt(
            prompt, is_detailed_checklist)

        return jsonify({"data": {
            "checklistId": result
        }})
    except ValueError as error:
        print("An error occurred:", error)
        return jsonify({'error': {'message': str(error)}}), 500
    finally:
        gc.collect()


@app.route('/generate-checklist-status-indicators', methods=['POST'])
def generate_checklist_status_indicators():
    payload = request.get_json()
    checklist_title = payload.get("title", None)
    tasks = payload.get("tasks", None)

    if (checklist_title is None or checklist_title == ""):
        return jsonify({'error': {'message': 'Checklist title cannot be null'}}), 400

    if (tasks is None or len(tasks) == 0):
        return jsonify({'error': {'message': 'Tasks cannot be null'}}), 400

    try:
        checklist_metadata_generator = ChecklistStatusIndicatorsController()
        result = checklist_metadata_generator.generate_status_indicators(
            checklist_title, tasks)

        return jsonify({"data": result})
    except ValueError as error:
        print("An error occurred:", error)
        return jsonify({'error': {'message': str(error)}}), 500
    finally:
        gc.collect()


@app.errorhandler(RequestEntityTooLarge)
def file_too_large(e):
    return jsonify({'error': {'message': str("File is too large")}}), 413


@app.route('/')
def root_path():
    return 'It is working...'


# if __name__ == '__main__':
#     app.run(host='localhost', port=8080, debug=True, threaded=True)
