from flask import render_template, request

def init_home_route(app):
    @app.route('/main', methods=['GET', 'POST'])
    def main_page():
        symptoms_info = None
        headache_info = None

        if request.method == 'POST':
            if 'symptoms_info' in request.form:
                symptoms_info = request.form['symptoms_info']
            elif 'headache_info' in request.form:
                headache_info = request.form['headache_info']

        return render_template('main.html', symptoms_info=symptoms_info, headache_info=headache_info)
