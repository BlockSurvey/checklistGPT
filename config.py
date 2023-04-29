import os
from dotenv import load_dotenv

# Load the environment variables from the .env file
load_dotenv()

# Read the environment variables and assign them to constants
HASURA_API_URL = os.environ.get('HASURA_API_URL')
HASURA_SECRET_KEY = os.environ.get('HASURA_SECRET_KEY')
HASURA_EVENT_SECRET_KEY = os.environ.get('HASURA_EVENT_SECRET_KEY')

JWT_SECRET = os.environ.get('JWT_SECRET')
