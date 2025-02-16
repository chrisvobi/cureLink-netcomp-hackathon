from flask import Flask
from routes import init_routes

app = Flask(__name__)
app.template_folder = "templates"
app.secret_key = "your_secret_key"  # Change this to a secure secret key

init_routes(app)

if __name__ == '__main__':
    app.run(debug=True)
