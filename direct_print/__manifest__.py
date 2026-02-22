{
    "name": "Direct Print",
    "version": "1.6.0",
    "summary": "Send PDFs directly to network printers without downloading.",
    "author": "Custom",
    "category": "Tools",
    "depends": ["base", "web"],
    "data": [
        "security/ir.model.access.csv",
        "views/direct_print_views.xml",
    ],
    "post_init_hook": "_post_init_hook",
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
