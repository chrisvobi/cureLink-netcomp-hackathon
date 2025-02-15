from flask import render_template, redirect, url_for, request

def init_login_route(app):
    @app.route('/')
    def login():
        return render_template('login.html')

    @app.route('/redirect_page', methods=['POST'])
    def redirect_page():
        return render_template('redirect_page.html')
