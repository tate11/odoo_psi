# -*- coding: utf-8 -*-

from datetime import date, datetime

from odoo import models, fields, api


class hr_holidays_psi(models.Model):
    _inherit = "hr.holidays"
    
    psi_category = fields.Many2one('hr.psi.category.details','Catégorie professionnelle')
    
    @api.model
    def create(self, values):
        got_droit = self.check_droit(values)
        
        #holidays = super(hr_holidays_psi, self).create()
        #return holidays
    
    def check_droit(self, values):
        current_employee = self.env['hr.contract'].search([('employee_id', '=', values['employee_id'])])
        date_start = datetime.strptime(current_employee.date_start,"%Y-%m-%d")
        date_from = datetime.strptime(values['date_from'],"%Y-%m-%d %H:%M:%S")
        delta = date_from - date_start
        print delta.days
        return False     
    