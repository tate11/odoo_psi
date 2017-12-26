# -*- coding: utf-8 -*-
from odoo import models, api
from odoo.exceptions import Warning

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'
    
    @api.v8
    @api.onchange('product_id', 'product_uom_id', 'unit_amount', 'currency_id')
    def on_change_unit_amount(self):
        print "on_change_unit_amount"
       
        
    @api.model
    def create(self, vals):
        print vals
        print "create account.analytic.line"
        account_analytic_line_s = self.env['account.analytic.line'].search([('project_id', '=', vals['project_id']), ('date', '=', vals['date'])])
        if vals['name'] == False :
            vals['name'] = '.'
        if len(account_analytic_line_s) != 0 :
            for account in account_analytic_line_s :
                if self.env.user.id == account.user_id.id  and vals.get('tag_ids'):
                    account.write({'unit_amount' : vals['unit_amount'] + self.unit_amount })
                    return account
        print len(account_analytic_line_s)
        res = super(AccountAnalyticLine, self).create(vals)
        return res
    
    @api.multi
    def write(self, vals):
        print "write  account.analytic.line"
        total = 0.0
        print self.date
        vals_emp = { 'date' : self.date}
        employees = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)])
        heure_par_jour = self.get_heure_par_jour(employees, vals_emp)
        print "heure_par_jour", heure_par_jour
        account_analytic_line_s = self.env['account.analytic.line'].search([('date', '=', self.date)])
        for account in account_analytic_line_s :
            if self.env.user.id == account.user_id.id:
                total += account.unit_amount
        print "total : ",total
        
        if vals.get('unit_amount') :
            total += vals.get('unit_amount')
            if total > heure_par_jour :
                raise Warning(u'Le nombre d\'heure pour cette tâche dépasse de {}'.format(self.float_time_to_time(heure_par_jour)))
                return False
            if vals.get('unit_amount') > heure_par_jour :
                raise Warning(u'Le nombre d\'heure pour cette tâche dépasse de {}'.format(self.float_time_to_time(heure_par_jour)))
                return False
        return super(AccountAnalyticLine, self).write(vals)
