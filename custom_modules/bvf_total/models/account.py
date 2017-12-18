# -*- coding: utf-8 -*-

from odoo import api,models,fields, exceptions

class AccountJournal(models.Model):
    _inherit = "account.journal"
    
    def _default_currency_id(self):
        return self.env['res.currency'].search([('name', '=', 'MGA')])[0].id
    
    currency_id = fields.Many2one('res.currency', string="Currency", oldname='currency', default=_default_currency_id)
        