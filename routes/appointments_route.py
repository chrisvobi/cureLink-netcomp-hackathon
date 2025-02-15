from flask import render_template

def init_appointments_route(app):
    @app.route('/appointments')
    def appointments_page():
        return render_template('appointments.html')  
