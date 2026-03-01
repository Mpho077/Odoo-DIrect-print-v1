from . import models
from . import wizards
from . import hooks


def _post_init_hook(env):
    """Called after module installation to create Direct Print actions."""
    hooks.post_init_hook(env)

