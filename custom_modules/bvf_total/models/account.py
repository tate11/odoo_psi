# -*- coding: utf-8 -*-

from odoo import api,models,fields, exceptions

class AccountJournal(models.Model):
    _inherit = "account.journal"
    
    def _default_currency(self):
        return self.env['res.currency'].search('name','=','MGA')[0].id
    
    currency_total_id = fields.Many2one('res.currency', string="Currency", oldname='currency', _default=_default_currency)
        