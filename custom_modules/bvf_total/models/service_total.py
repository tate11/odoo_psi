# -*- coding: utf-8 -*-

from odoo import api,models,fields, exceptions

class service_total(models.Model):
    _name = "service.total"
    
    name = fields.Char(string='Nom', required=True, size = 50)    
    direction_id = fields.Many2one(string='Direction', comodel_name='direction.total')