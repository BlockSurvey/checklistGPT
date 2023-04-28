from flask import Flask, jsonify, request

import config
from controllers.checklist_controller import ChecklistController

app = Flask(__name__)


@app.route('/generate-checklist')
def generate_checklist_api():
    checklist_agent_id = request.args.get('id', None)
    checklist = ChecklistController(checklist_agent_id)
    result = checklist.generate_checklist()
    response = {
        "data": {
            result: result
        }
    }
    return jsonify(response)


@app.route('/')
def root_path():
    return 'It is working...'


# if __name__ == '__main__':
#     app.run(host='localhost', port=8080, debug=True, threaded=True)
