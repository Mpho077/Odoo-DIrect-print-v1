from odoo import models, fields, api, _
from odoo.exceptions import UserError
import json


class DirectPrintWizard(models.TransientModel):
    _name = 'direct.print.wizard'
    _description = 'Direct Print Wizard'

    printer_id = fields.Many2one(
        'direct.print.printer',
        string='Printer',
        required=True,
        default=lambda self: self._get_default_printer()
    )
    report_id = fields.Many2one(
        'ir.actions.report',
        string='Report',
        domain="[('model', '=', model)]",
        required=True,
    )
    report_ref = fields.Char(string='Report Reference')
    res_ids = fields.Char(string='Record IDs')
    model = fields.Char(string='Model')
    remember_printer = fields.Boolean(
        string='Set as my default printer',
        default=False,
        help='If checked, this printer will be set as your default printer for future prints.'
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        
        # Get model from context
        model = self._context.get('default_model') or self._context.get('active_model')
        res['model'] = model
        
        # Get record IDs
        res_ids = self._context.get('default_res_ids') or self._context.get('active_ids') or []
        if self._context.get('active_id') and not res_ids:
            res_ids = [self._context.get('active_id')]
        res['res_ids'] = json.dumps(res_ids)
        
        # Get report from context or find first available for model
        report_ref = self._context.get('default_report_ref')
        if report_ref:
            res['report_ref'] = report_ref
            report = self._get_report_from_ref(report_ref)
            if report:
                res['report_id'] = report.id
        elif model:
            # Find available reports for this model
            reports = self.env['ir.actions.report'].search([('model', '=', model)], limit=1)
            if reports:
                res['report_id'] = reports.id
        
        return res

    def _get_report_from_ref(self, report_ref):
        """Get report record from reference (xml_id or id_xxx format)."""
        if not report_ref:
            return False
        try:
            if report_ref.startswith('id_'):
                rid = int(report_ref[3:])
                return self.env['ir.actions.report'].browse(rid)
            else:
                return self.env.ref(report_ref)
        except Exception:
            return False

    def _get_default_printer(self):
        """Get the user's default printer if set."""
        default_printer = self.env['direct.print.user.default'].get_user_default()
        if default_printer:
            return default_printer.id
        first_printer = self.env['direct.print.printer'].search([], limit=1)
        return first_printer.id if first_printer else False

    def action_print_direct(self):
        self.ensure_one()
        
        if not self.report_id:
            raise UserError(_('Please select a report to print.'))

        # Save printer as default if requested
        if self.remember_printer and self.printer_id:
            self.env['direct.print.user.default'].set_user_default(self.printer_id.id)

        # Parse record IDs
        try:
            res_ids = json.loads(self.res_ids) if self.res_ids else []
            if not res_ids:
                raise UserError(_('No records to print.'))
        except (json.JSONDecodeError, TypeError):
            raise UserError(_('Invalid record IDs.'))

        # Get report data from context if available
        report_data = self._context.get('direct_print_report_data')

        # Generate PDF
        try:
            result = self.env['ir.actions.report']._render_qweb_pdf(self.report_id, res_ids=res_ids, data=report_data)
            pdf = result[0] if isinstance(result, tuple) else result
            if not pdf:
                raise UserError(_('Report generation returned no data.'))
        except Exception as e:
            raise UserError(_('Failed to generate report PDF: %s') % e)

        # Send to printer
        try:
            filename = '%s-%s.pdf' % (self.model or 'document', '-'.join(map(str, res_ids[:3])))
            self.printer_id.send(pdf, filename=filename)
        except Exception as e:
            raise UserError(_('Printing failed: %s') % e)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Print Job Sent'),
                'message': _('Document sent to printer: %s') % self.printer_id.name,
                'type': 'success',
                'sticky': False,
            }
        }

