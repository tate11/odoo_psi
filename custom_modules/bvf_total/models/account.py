# -*- coding: utf-8 -*-

from odoo import api,models,fields, exceptions

class AccountJournal(models.Model):
    _inherit = "account.journal"
    
    def _default_currency_id(self):
        length_currency = len(self.env['res.currency'].search([('name', '=', 'MGA')]))
        if length_currency != 0 :
            return self.env['res.currency'].search([('name', '=', 'MGA')])[0].id
        return 0;
    
    currency_id = fields.Many2one('res.currency', string="Currency", oldname='currency', default=_default_currency_id)
    
    @api.multi
    @api.depends('name', 'currency_id', 'company_id', 'company_id.currency_id')
    def name_get(self):
        res = []
        for journal in self:
            currency = journal.currency_id or journal.company_id.currency_id
            name = journal.name
            res += [(journal.id, name)]
        return res
        