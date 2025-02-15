from flask import Flask, request
from routes import init_routes

app = Flask(__name__)
app.template_folder = "templates"

init_routes(app)

if __name__ == '__main__':
    app.run(debug=True)
