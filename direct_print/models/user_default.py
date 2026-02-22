from odoo import models, fields, api, _


class DirectPrintUserDefault(models.Model):
    _name = 'direct.print.user.default'
    _description = 'User Default Printer'
    _rec_name = 'user_id'

    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True,
        ondelete='cascade',
        index=True,
    )
    printer_id = fields.Many2one(
        'direct.print.printer',
        string='Default Printer',
        required=True,
        ondelete='cascade',
    )

    _sql_constraints = [
        ('user_unique', 'unique(user_id)', 'Each user can only have one default printer!')
    ]

    @api.model
    def get_user_default(self, user_id=None):
        """Get the default printer for a user."""
        if user_id is None:
            user_id = self.env.uid
        default = self.search([('user_id', '=', user_id)], limit=1)
        return default.printer_id if default else False

    @api.model
    def set_user_default(self, printer_id, user_id=None):
        """Set the default printer for a user."""
        if user_id is None:
            user_id = self.env.uid
        existing = self.search([('user_id', '=', user_id)], limit=1)
        if existing:
            existing.write({'printer_id': printer_id})
        else:
            self.create({'user_id': user_id, 'printer_id': printer_id})
        return True
