from flask import render_template, session, redirect, url_for



def init_doctor_route(app):
    @app.route('/doctor')
    def doctor_page():
        if 'user_id' not in session:
            return redirect(url_for('login'))  # Redirect if not logged in
        return render_template('doctor_main.html')
