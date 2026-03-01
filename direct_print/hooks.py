import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Called after module installation to create Direct Print actions
    and clean up legacy data from previous versions."""
    _cleanup_legacy_data(env)
    try:
        env['direct.print.action']._ensure_print_actions()
    except Exception as e:
        _logger.warning("Direct Print: Could not create actions during install: %s", e)


def _cleanup_legacy_data(env):
    """Remove database artefacts left by the v1.x printer/user-default models.

    This runs on every install/upgrade so the module can be safely upgraded
    from an older version without manually uninstalling first.
    """
    cr = env.cr

    # Remove old menu items that reference deleted actions/models
    old_xmlids = [
        'direct_print.menu_direct_print_printers',
        'direct_print.menu_direct_print_user_defaults',
        'direct_print.menu_detect_windows_printers',
        'direct_print.action_direct_print_printer',
        'direct_print.action_detect_windows_printers_menu',
        'direct_print.action_direct_print_user_default',
    ]
    for xmlid in old_xmlids:
        try:
            rec = env.ref(xmlid, raise_if_not_found=False)
            if rec:
                rec.unlink()
                _logger.info("Direct Print: removed legacy record %s", xmlid)
        except Exception:
            pass

    # Drop old tables if they still exist
    for table in ('direct_print_printer', 'direct_print_user_default'):
        try:
            cr.execute("SELECT 1 FROM information_schema.tables WHERE table_name = %s", (table,))
            if cr.fetchone():
                cr.execute('DROP TABLE IF EXISTS "%s" CASCADE' % table)
                _logger.info("Direct Print: dropped legacy table %s", table)
        except Exception:
            pass

    # Remove orphaned ir.model records for deleted models
    for model_name in ('direct.print.printer', 'direct.print.user.default'):
        try:
            cr.execute("DELETE FROM ir_model WHERE model = %s", (model_name,))
        except Exception:
            pass

