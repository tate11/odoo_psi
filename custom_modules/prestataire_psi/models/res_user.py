# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Users(models.Model):
    _name = "res.users"
    _inherit = "res.users"
    
    @api.model
    def create(self, vals):
        user = super(Users, self).create(vals)
        user.partner_id.active = user.active
        if user.has_group('prestataire_psi.group_prestataire'):
            user.partner_id.user_id = user
            user.partner_id.supplier = True
        if user.partner_id.company_id:
            user.partner_id.write({'company_id': user.company_id.id})
        return user