from flask import Flask, session
from routes import init_routes
import json

# Load the secret key from config.json
with open('config.json') as config_file:
    config = json.load(config_file)
    secret_key = config['SECRET_KEY']

# Initialize the Flask app
app = Flask(__name__)
app.template_folder = "templates"
app.secret_key = secret_key  

# Register application routes
init_routes(app)

# Ensure session is not stored permanently in memory
def make_session_not_permanent():
    session.permanent = False

# Run the Flask application
if __name__ == '__main__':
    app.run(debug=True)