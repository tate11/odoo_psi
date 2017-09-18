# -*- coding: utf-8 -*-

from odoo import api,fields, models
from odoo.exceptions import UserError
from datetime import date

class HrWageAdvance(models.Model):
    
    _name = 'hr.wage.advance'
    
    def get_current_employee_id(self):
        employee_ids = self.env['hr.employee'].search([('user_id','=',self.env.uid)])
        if employee_ids:
            return employee_ids[0].id
        return False
    
    def get_departement_id(self):
        employee_obj = self.env['hr.employee']
        employee_ids = employee_obj.search([('user_id','=',self.env.uid)])
        if employee_ids:
            return employee_ids[0].department_id.id
        return False
    
    def get_manager_id(self):
        employee_obj = self.env['hr.employee']
        employee_ids = employee_obj.search([('user_id','=',self.env.uid)])
        if employee_ids:
            return employee_ids[0].parent_id.id
        return False
    
    
    name = fields.Char(string='Nom de la demande')
    employee_id = fields.Many2one('hr.employee', string='Demandeur', required=True, default=get_current_employee_id)
    department_id = fields.Many2one('hr.department', string=u'Département', required=True, default=get_departement_id)
    date = fields.Date(string='Date de la demande', default=date.today().strftime('%Y-%m-%d'), required=True)
    amount = fields.Float(string='Montant')
    manager_id = fields.Many2one('hr.employee', string='Responsable', required=True,default=get_manager_id)
    state = fields.Selection([
        ('draft', 'Nouveau'),
        ('ok', u'Validé'),
        ('not_ok', u'Refusé'),
    ], string='Etat', track_visibility='onchange',default='draft')
    
    @api.onchange('employee_id')
    def onchange_employee(self):
        self.name = 'Demande de '+ self.employee_id.name
        return
    
class HrPayslip(models.Model):
    _inherit = 'hr.payslip'
    
    def get_avance_salaire(self):
        advance_obj = self.env['hr.wage.advance']
        advances = advance_obj.search(['&','&','&',('employee_id','=',self.employee_id.id),('state','=','ok'),('date','>=',self.date_from),('date','<=',self.date_to)])
        total_advance = 0.0
        for advance in advances:
            total_advance += advance.amount 
        return total_advance
        
    @api.onchange('employee_id', 'date_from')
    def onchange_employee(self):
        self.input_line_ids = []
        res = super(HrPayslip, self).onchange_employee()
        if self.employee_id and self.date_from and self.date_to:
            input_data = {
                    'name': 'Montant avance quinzaine',
                    'code': 'AVANCE15',
                    'amount': self.get_avance_salaire(),
                    'contract_id': self.contract_id.id,
                }
            input_lines = self.input_line_ids.browse([])
            input_lines += input_lines.new(input_data)
            self.input_line_ids = input_lines
        return res

class hrPayrollInterim(models.Model):
    
    _name = 'hr.payroll.interim'
    
    def get_current_employee_id(self):
        employee_ids = self.env['hr.employee'].search([('user_id','=',self.env.uid)])
        if employee_ids:
            return employee_ids[0].id
        return False
    
    def get_departement_id(self):
        employee_obj = self.env['hr.employee']
        employee_ids = employee_obj.search([('user_id','=',self.env.uid)])
        if employee_ids:
            return employee_ids[0].department_id.id
        return False
    
    def get_manager_id(self):
        employee_obj = self.env['hr.employee']
        employee_ids = employee_obj.search([('user_id','=',self.env.uid)])
        if employee_ids:
            return employee_ids[0].parent_id.id
        return False
    
    employee_id = fields.Many2one('hr.employee', string='Demandeur', required=True, default=get_current_employee_id)
    department_id = fields.Many2one('hr.department', string=u'Département', required=True, default=get_departement_id)
    manager_id = fields.Many2one('hr.employee', string='Responsable', required=True,default=get_manager_id)