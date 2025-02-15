from flask import render_template

def init_appointments_history_route(app):
    @app.route('/appointments_history')
    def appointments_history_page():
        return render_template('appointments_history.html')  