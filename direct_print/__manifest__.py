{
    "name": "Direct Print",
    "version": "2.0.0",
    "summary": "Print documents via the browser print dialog — works with any local or network printer.",
    "author": "Custom",
    "category": "Tools",
    "depends": ["base", "web", "account", "sale", "purchase", "stock"],
    "data": [
        "security/ir.model.access.csv",
        "views/direct_print_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "direct_print/static/src/js/browser_print_action.js",
        ],
    },
    "post_init_hook": "_post_init_hook",
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
