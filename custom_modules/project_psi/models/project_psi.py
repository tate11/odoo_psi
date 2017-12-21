# -*- coding: utf-8 -*-
from odoo import api, fields, models

class Project_psi(models.Model):
    _inherit = "project.project"
    employee_ids = fields.Many2many('hr.employee',string='Employés')
