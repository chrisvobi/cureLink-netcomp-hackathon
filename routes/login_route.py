from flask import render_template

def init_login_route(app):
    @app.route('/')
    def login():
        return render_template('login.html')
