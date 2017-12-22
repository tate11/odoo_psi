# -*- coding: utf-8 -*-

from odoo import api,models,fields

class res_users(models.Model):
    
    _inherit = "res.users"    
    
    mail = fields.Char(related='partner_id.email', string='E-mail', store=True)
    
