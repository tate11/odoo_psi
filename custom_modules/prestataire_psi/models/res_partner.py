# -*- coding: utf-8 -*-

from odoo import models, fields

class ResPartner(models.Model):
    _name = "res.partner"
    _inherit = "res.partner"
    
    project_ids = fields.Many2many('project.project', string='Projets')