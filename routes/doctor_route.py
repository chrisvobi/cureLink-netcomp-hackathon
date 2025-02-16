from flask import render_template

def init_doctor_route(app):
    @app.route('/doctor')
    def doctor_page():
        return render_template('doctor_main.html')  