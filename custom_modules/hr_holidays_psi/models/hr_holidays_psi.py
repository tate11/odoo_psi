# -*- coding: utf-8 -*-

from odoo import models,fields

class hr_holidays_psi(models.Model):
    _inherit = "hr.holidays"
    
    psi_category = fields.Many2one('hr.psi.category.details','Catégorie professionnelle')
