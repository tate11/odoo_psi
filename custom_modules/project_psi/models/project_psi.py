# -*- coding: utf-8 -*-
from odoo import api, fields, models

class Project_psi(models.Model):
    _inherit = "project.project"
    employee_ids = fields.Many2many('hr.employee',string='Employés')
    partner_ids = fields.Many2many('res.partner',string='Fournisseur')
    
class Hr_employee_psi(models.Model):
    _inherit = 'hr.employee'
    project_ids = fields.Many2many('project.project', string='Projets')

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'
    project_id = fields.Many2one('project.project', 'Project', domain=lambda self: 
                                     [('id','in', tuple([x.id for x in self.env['hr.employee'].search([('user_id','=',self.env.user.id)]).project_ids]
                                     								)
                                     				   )])
