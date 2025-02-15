from flask import render_template, request

def init_main_route(app):
    @app.route('/main', methods=['GET', 'POST'])
    def main_page():
        return render_template('main.html')
