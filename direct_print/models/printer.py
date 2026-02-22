from odoo import models, fields, api, _
from odoo.exceptions import UserError
import socket
import tempfile
import subprocess
import os


class DirectPrintPrinter(models.Model):
    _name = 'direct.print.printer'
    _description = 'Direct Network Printer'

    name = fields.Char(required=True)
    ip = fields.Char(string='IP / Host', required=True)
    port = fields.Integer(default=9100)
    protocol = fields.Selection([
        ('raw', 'Raw (port 9100 - JetDirect)'),
        ('lpr', 'lpr command'),
        ('cups', 'CUPS (pycups)')
    ], default='raw', required=True)
    note = fields.Text()
    active = fields.Boolean(default=True)
    last_test_result = fields.Char(string='Last Test Result', readonly=True)
    last_test_date = fields.Datetime(string='Last Test Date', readonly=True)

    def action_test_connection(self):
        """Test the printer connection and report status."""
        self.ensure_one()
        result_message = ''
        success = False

        try:
            if self.protocol == 'raw':
                # Test TCP connection to the printer
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(5)
                try:
                    s.connect((self.ip, int(self.port or 9100)))
                    success = True
                    result_message = _('Connection successful! Printer is reachable at %s:%s') % (self.ip, self.port or 9100)
                finally:
                    s.close()

            elif self.protocol == 'lpr':
                # Test if lpr command is available
                try:
                    result = subprocess.run(['lpstat', '-p'], capture_output=True, timeout=5)
                    if result.returncode == 0:
                        success = True
                        result_message = _('LPR service is available. Printer queue ready.')
                    else:
                        result_message = _('LPR service returned an error.')
                except FileNotFoundError:
                    result_message = _('LPR command not found on this system.')
                except subprocess.TimeoutExpired:
                    result_message = _('LPR service timed out.')

            elif self.protocol == 'cups':
                try:
                    import cups
                    conn = cups.Connection()
                    printers = conn.getPrinters()
                    if self.name in printers:
                        success = True
                        result_message = _('CUPS printer "%s" found and ready.') % self.name
                    elif printers:
                        available = ', '.join(list(printers.keys())[:5])
                        result_message = _('Printer "%s" not found in CUPS. Available: %s') % (self.name, available)
                    else:
                        result_message = _('No CUPS printers configured.')
                except ImportError:
                    result_message = _('pycups library not installed on the server.')
                except Exception as e:
                    result_message = _('CUPS connection error: %s') % str(e)

            else:
                result_message = _('Unknown protocol: %s') % self.protocol

        except socket.timeout:
            result_message = _('Connection timed out. Printer may be offline or unreachable.')
        except socket.error as e:
            result_message = _('Connection failed: %s') % str(e)
        except Exception as e:
            result_message = _('Test failed: %s') % str(e)

        # Update test result fields
        self.write({
            'last_test_result': ('✓ ' if success else '✗ ') + result_message,
            'last_test_date': fields.Datetime.now(),
        })

        # Show notification to user
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Printer Test: %s') % self.name,
                'message': result_message,
                'type': 'success' if success else 'warning',
                'sticky': False,
            }
        }

    def send(self, pdf_bytes, filename='report.pdf'):
        self.ensure_one()
        if not pdf_bytes:
            raise UserError(_('No PDF data to send to printer.'))
        try:
            if self.protocol == 'raw':
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(10)
                try:
                    s.connect((self.ip, int(self.port or 9100)))
                    s.sendall(pdf_bytes)
                finally:
                    s.close()
                return True
            elif self.protocol == 'lpr':
                fd, path = tempfile.mkstemp(suffix='.pdf')
                try:
                    os.write(fd, pdf_bytes)
                finally:
                    os.close(fd)
                cmd = ['lpr', '-P', self.name, path] if self.name else ['lpr', path]
                subprocess.check_call(cmd)
                os.remove(path)
                return True
            elif self.protocol == 'cups':
                try:
                    import cups
                except Exception as e:
                    raise UserError(_('pycups is not available on the server: %s') % e)
                conn = cups.Connection()
                printers = conn.getPrinters()
                pname = self.name if self.name in printers else (list(printers.keys())[0] if printers else None)
                if not pname:
                    raise UserError(_('No CUPS printers found.'))
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                tmp.write(pdf_bytes)
                tmp.close()
                conn.printFile(pname, tmp.name, filename, {})
                os.remove(tmp.name)
                return True
            else:
                raise UserError(_('Unknown printer protocol %s') % self.protocol)
        except Exception as e:
            raise UserError(_('Failed to send to printer %s: %s') % (self.name or self.ip or '', e))

    @api.model
    def action_create_print_actions(self):
        """Create Direct Print server actions for supported models."""
        DIRECT_PRINT_MODELS = [
            'sale.order',
            'account.move', 
            'purchase.order',
            'stock.picking',
        ]
        
        code_template = """
if records:
    action = {
        'name': 'Direct Print',
        'type': 'ir.actions.act_window',
        'res_model': 'direct.print.wizard',
        'view_mode': 'form',
        'target': 'new',
        'context': {
            'default_model': records._name,
            'active_model': records._name,
            'active_ids': records.ids,
            'active_id': records.ids[0] if records.ids else False,
        },
    }
"""
        
        IrModel = self.env['ir.model']
        IrActionsServer = self.env['ir.actions.server']
        created = []
        
        for model_name in DIRECT_PRINT_MODELS:
            model = IrModel.search([('model', '=', model_name)], limit=1)
            if not model:
                continue
            
            existing = IrActionsServer.search([
                ('name', '=', 'Direct Print'),
                ('model_id', '=', model.id),
            ], limit=1)
            
            if existing:
                continue
            
            IrActionsServer.create({
                'name': 'Direct Print',
                'model_id': model.id,
                'binding_model_id': model.id,
                'binding_view_types': 'form,list',
                'state': 'code',
                'code': code_template,
            })
            created.append(model_name)
        
        msg = _('Created Direct Print actions for: %s') % ', '.join(created) if created else _('All Direct Print actions already exist.')
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Direct Print'),
                'message': msg,
                'type': 'success',
                'sticky': False,
            }
        }
