from .login_route import init_login_route
from .main_route import init_main_route
from .agent_route import init_agent_route

def init_routes(app):
    init_login_route(app)
    init_main_route(app)
    init_agent_route(app)
    
