from .login_route import init_login_route
from .home_route import init_home_route

def init_routes(app):
    init_login_route(app)
    init_home_route(app)
