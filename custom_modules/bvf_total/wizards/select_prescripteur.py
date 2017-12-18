# -*- coding: utf-8 -*-

from odoo import api, models,fields, SUPERUSER_ID
from datetime import date, timedelta, datetime

class select_prescripteur(models.TransientModel):
    _name = "select.prescripteur"
    
    def _compute_bvf_ids(self):
        return self._context.get('bvf_list')
    
    def domain_utilisateur_id(self):
        group = self.env.ref('bvf_total.group_prescripteur')
        return "[('id','in',%s)]"%group.users.ids
    
    utilisateur_id = fields.Many2one(string='Prescripteur', comodel_name='res.users', domain=domain_utilisateur_id)
    bvf_ids = fields.Many2many(string='BVFs', comodel_name='bvf.total', default=_compute_bvf_ids)
    
                
    @api.multi
    def select_prescripteur_confirm_action(self):
        for record in self.bvf_ids:  
            record.responsable_id = self.utilisateur_id                    
            date_today = date.today().strftime('%d/%m/%Y')  
            record.date_approbation_dir = date_today
            record.prescripteur_resp = self.env.user.login   
            record.state = 'envoi_presc'
                
        """return {
            'type': 'ir.actions.act_window',
                'name': 'Confirmation de changement de statut',
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'change.status',
                'target': 'new',
                'context':{'state': 'envoi_presc', 'default_bfv_total_id':self.id, 'default_status':'Envoi au prescripteur'}
                }"""
                    
    