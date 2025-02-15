from flask import render_template, request

def init_agent_route(app):
    @app.route('/agent', methods=['GET', 'POST'])
    def agent_page():
        step = 1  # Track which question to display
        symptoms_info = None
        headache_info = None

        if request.method == 'POST':
            if 'symptoms_info' in request.form:
                symptoms_info = request.form['symptoms_info']
                step = 2  # Move to the next question
            elif 'headache_info' in request.form:
                headache_info = request.form['headache_info']
                step = 3  # Further questions can be added if needed

        return render_template('agent.html', step=step, symptoms_info=symptoms_info, headache_info=headache_info)
