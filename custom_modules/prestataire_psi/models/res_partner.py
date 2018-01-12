# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResPartner(models.Model):
    _name = "res.partner"
    _inherit = "res.partner"
    
    project_ids = fields.Many2many('project.project', string='Projets')
               
    @api.multi
    def write(self, vals):
        if vals.has_key('user_id') :
            user = self.env['res.users'].browse(vals['user_id'])
            user.write({'partner_id' : self.id})
        return super(ResPartner, self).write(vals)
    
    
    