# -*- coding: utf-8 -*-

from odoo import api, models,fields

class change_status_facture(models.TransientModel):
    _name = "change.status.facture"
    
    status = fields.Char(string='Status')
    facture_total_id = fields.Many2one(string='Facture total', comodel_name='facture.total')
    
    @api.multi
    def change_status_facture_action(self):
        
        return {
            'type': 'ir.actions.act_window',
                'name': 'Confirmation de changement de statut',
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'second.confirm.facture',
                'target': 'new',
                'context':{'state': self._context.get('state'), 'default_facture_total_id':self.facture_total_id.id, 'default_status': self._context.get('default_status')}
                }

            
        
