import json

import jwt
from flask import Flask, g, jsonify, request

import config
from config import JWT_SECRET
from controllers.checklist_controller import ChecklistController
from utils.agent_utils import get_agent_by_id

app = Flask(__name__)


@app.before_request
def token_required():
    # Exclude some routes from token verification, for example the login route
    # if request.path == '/login':
    #     return None

    auth_header = request.headers.get('Authorization')

    if not auth_header:
        return jsonify({'message': 'Token is missing!'}), 401

    jwtSecretObject = json.loads(JWT_SECRET)

    try:
        token = auth_header.split(' ')[1]
        payload = jwt.decode(
            token, jwtSecretObject['key'], algorithms=['HS256'])
        # Store the decoded payload in the 'g' object
        g.jwt_session = payload
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token has expired!'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Invalid token!'}), 401


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


@app.route('/')
def root_path():
    return 'It is working...'


# if __name__ == '__main__':
#     app.run(host='localhost', port=8080, debug=True, threaded=True)
