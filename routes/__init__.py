from .login_route import init_login_route
from .main_route import init_main_route
from .agent_route import init_agent_route
from .appointments_route import init_appointments_route
from .register_route import init_register_route
from .appointments_history_route import init_appointments_history_route
from .account_route import init_account_route

def init_routes(app):
    init_login_route(app)
    init_main_route(app)
    init_agent_route(app)
    init_appointments_route(app)
    init_register_route(app)
    init_appointments_history_route(app)
    init_account_route(app)
    
