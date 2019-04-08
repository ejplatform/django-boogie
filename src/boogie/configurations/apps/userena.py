from ..base import Conf


class UserenaConf(Conf):
    USERENA_ACTIVATION_REQUIRED = False
    USERENA_SIGNIN_AFTER_SIGNUP = True
    USERENA_DISABLE_PROFILE_LIST = True
    USERENA_ACTIVATION_DAYS = 7
    USERENA_FORBIDDEN_USERNAMES = (
        "signup",
        "signout",
        "signin",
        "activate",
        "me",
        "password",
        "login",
        "codeschool",
    )
    USERENA_USE_HTTPS = False
    USERENA_REGISTER_PROFILE = False
    USERENA_SIGNIN_REDIRECT_URL = "/"
    USERENA_REDIRECT_ON_SIGNOUT = "/"
    USERENA_PROFILE_LIST_TEMPLATE = "auth/profile-list.jinja2"
