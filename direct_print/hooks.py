import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Called after module installation to create Direct Print actions."""
    try:
        env['direct.print.printer'].action_create_print_actions()
    except Exception as e:
        _logger.warning("Direct Print: Could not create actions during install: %s", e)
