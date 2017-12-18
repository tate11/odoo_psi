# -*- coding: utf-8 -*-

from odoo import api, models,fields

class unlink_confirmation(models.TransientModel):
    _name = "unlink.confirmation"
    
    name = fields.Many2one(string='Name', comodel_name='fournisseur.total')
    
    @api.multi
    def unlink_fournisseur(self):
        self.name.unlink()