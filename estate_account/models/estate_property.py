from odoo import models, fields, api, Command

class estate(models.Model):
    _inherit = 'estate.model'

    def sold_btn_clicked(self):
        res = super().sold_btn_clicked()
        if res:
            journal = self.env['account.move'].with_context(default_move_type='out_invoice')._get_default_journal()

            self.env['account.move'].create({
                'partner_id': self.buyer_id,
                'move_type': 'out_invoice',
                'journal_id': journal.id,
                'invoice_line_ids': [
                    Command.create({
                        'name': self.name,
                        'quantity': round((self.selling_price * 0.06), 2),
                        'price_unit': 1
                    }),
                    Command.create({
                        'name': 'Administrative Fess',
                        'quantity': 100.00,
                        'price_unit': 1
                    })
                ]
            })

        return res
