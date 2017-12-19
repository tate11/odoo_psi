# -*- coding: utf-8 -*-

from odoo import api,models,fields

class res_users(models.Model):
    
    _inherit = "res.users"    
    
    prenom = fields.Char(string='Prénoms', size=50, required=True)
    direction_id = fields.Many2one('direction.total', string='Direction', required=True)
    service_id= fields.Many2one('service.total', string='Service', required=True)
    mail = fields.Char(related='partner_id.email', string='E-mail', store=True)
    
    @api.multi
    @api.depends('name', 'prenom', 'login')
    def name_get(self):
        res = []
        for record in self:
            if self._context.get('dans_relance'):                
                name = ""
                if record.login: name += (record.login + " - ")
                if record.name: name += (record.name + " ")
                if record.prenom: name += (record.prenom)
                res.append((record.id, name))
            else:
                res = super(res_users, self).name_get()
        return res
    
    @api.onchange('direction_id')                
    def onchange_direction(self):
        res = {}
        if self.direction_id:
            self.service_id = False
            res['domain'] = {'service_id':[('direction_id','=',self.direction_id.id)]}
        return res

    @api.model
    def create(self, vals):
        vals['in_group_' + str(self.env['res.groups'].search([('name','=','Employé')])[0].id)]=True
        #user.partner_id.write({'company_id': user.company_id.id})
        user = super(res_users, self).create(vals)
        return user