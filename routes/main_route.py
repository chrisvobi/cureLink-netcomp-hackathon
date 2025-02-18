from flask import render_template, request, session, redirect, url_for


def init_main_route(app):
    @app.route('/main', methods=['GET', 'POST'])
    def main_page():
        if 'user_id' not in session:
            return redirect(url_for('login')) # Redirect if not logged in

        if session.get('user_type') != "patient":  
            return redirect(url_for('login'))  # Redirect doctors away
            
        return render_template('main.html')
