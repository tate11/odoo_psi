# -*- coding: utf-8 -*-

from odoo import api,models,fields, exceptions

class direction_total(models.Model):
    _name = "direction.total"
    
    name = fields.Char(string='Nom', required=True, size = 50)