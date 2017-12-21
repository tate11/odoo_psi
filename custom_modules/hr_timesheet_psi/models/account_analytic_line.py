# -*- coding: utf-8 -*-
from odoo import models, api

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'
    
    @api.v8
    @api.onchange('product_id', 'product_uom_id', 'unit_amount', 'currency_id')
    def on_change_unit_amount(self):
        print "on_change_unit_amount"
       
        
    @api.model
    def create(self, vals):
        print "create"
        account_analytic_line_s = self.env['account.analytic.line'].search([('project_id','=',vals['project_id']),('date','=',vals['date'])])
        if vals['name'] == False :
            vals['name'] = '.'
        if len(account_analytic_line_s) != 0 :
            for account in account_analytic_line_s :
                if self.env.user.id == account.user_id.id :
                    print vals['unit_amount']
                    account.write({'unit_amount' : vals['unit_amount']})
                    return account
        print len(account_analytic_line_s)
        res = super(AccountAnalyticLine, self).create(vals)
        return res