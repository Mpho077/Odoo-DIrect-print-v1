from odoo import models, fields, api, _


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    use_direct_print = fields.Boolean(
        string='Use Direct Print',
        default=False,
        help='If enabled, this report will open a printer selection dialog instead of downloading the PDF.'
    )

    def report_action(self, docids, data=None, config=True):
        """Override to intercept print action and show printer selection dialog."""
        # Only intercept if this report has direct print enabled
        if not self.use_direct_print:
            return super().report_action(docids, data=data, config=config)
        
        # Check if we have printers configured
        printers = self.env['direct.print.printer'].search([], limit=1)
        if not printers:
            return super().report_action(docids, data=data, config=config)
        
        # Get active_ids
        if docids:
            if isinstance(docids, models.Model):
                active_ids = docids.ids
            elif isinstance(docids, int):
                active_ids = [docids]
            elif isinstance(docids, list):
                active_ids = docids
        else:
            active_ids = self.env.context.get('active_ids', [])
        
        # Get the report reference
        report_ref = self.get_external_id().get(self.id, '')
        if not report_ref:
            report_ref = 'id_%s' % self.id
        
        return {
            'name': _('Print Document'),
            'type': 'ir.actions.act_window',
            'res_model': 'direct.print.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_report_ref': report_ref,
                'default_res_ids': active_ids,
                'default_model': self.model,
                'direct_print_report_data': data,
            },
        }
