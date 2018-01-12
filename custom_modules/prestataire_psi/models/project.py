# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Task(models.Model):
    _inherit = "project.task"
    
    project_id = fields.Many2one('project.project', 'Project', domain=lambda self: 
                                     [('id','in', tuple([x.id for x in self.env['res.users'].browse(self.env.user.id).partner_id.project_ids]
                                                                     )
                                                        )])
  
    
    @api.onchange('project_id')
    def onchange_project_id(self):
        print "User : ",self.env.user.id
        res_partners = self.env['res.users'].search([('id','=',self.env.user.id)])
        for rp in res_partners.partner_id.project_ids :
            for p in rp.project_ids :
                print "Project name : ",p.name