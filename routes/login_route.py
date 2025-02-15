from flask import render_template, redirect, url_for, request

def init_login_route(app):
    @app.route('/')
    def login():
        return render_template('login.html')
