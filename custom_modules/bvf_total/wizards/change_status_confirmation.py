# -*- coding: utf-8 -*-

from datetime import date
from odoo import api, models,fields
from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT

class change_status(models.TransientModel):
    _name = "change.status"
        
    status = fields.Char(string='Status')
    bfv_total_id = fields.Many2one(string='Bvf total', comodel_name='bvf.total')
    
    @api.multi
    def change_status_action(self):
        if self._context.get('state') != 'envoi_presc':
            return {
                'type': 'ir.actions.act_window',
                    'name': 'Confirmation de changement de statut',
                    'view_mode': 'form',
                    'view_type': 'form',
                    'res_model': 'second.confirm',
                    'target': 'new',
                    'context':{'state': self._context.get('state'), 'default_bfv_total_id':self.bfv_total_id.id, 'default_status': self._context.get('default_status')}
                    }
            
            """    
            #self.bfv_total_id.sudo().update({'state': self._context.get('state')})
            self.bfv_total_id.state = self._context.get('state')
            self.bfv_total_id.responsable_id = self.env.user
            
            date_today = date.today().strftime('%d/%m/%Y')  
                
            # PASSAGE AU POLE COMPTA
            if self._context.get('state') == 'ok_paimt_normal' or self._context.get('state') == 'refacturer' or self._context.get('state') == 'compta_gen_nd':
                self.bfv_total_id.date_reception_compte = date_today
                self.bfv_total_id.comptable_resp = self.env.user.login 
                group_comptable = self.env.ref('bvf_total.group_comptables')
                self.bfv_total_id.responsable_ids = group_comptable.users 
                self.bfv_total_id.responsable_id = False             
            
            # PASSAGE AU POLE TRESO   
            elif self._context.get('state') == 'bon_a_payer' or self._context.get('state') == 'ok_paimt_immediat' or self._context.get('state') == 'recu_treso':
                self.bfv_total_id.date_reception_compte_banque = date_today
                self.bfv_total_id.tresorier_resp = self.env.user.login   
                group_treso = self.env.ref('bvf_total.group_tresoriers')
                self.bfv_total_id.responsable_ids = group_treso.users
                self.bfv_total_id.responsable_id = False   
                
            # PASSAGE AU RETOUR AUX AGENTS ADMINS     
            elif self._context.get('state') == 'recu_verifiee':
                self.bfv_total_id.responsable_id = self.bfv_total_id.agentadmin_resp_id    
                self.bfv_total_id.responsable_ids = False
                
            print 'responsable_ids ------------ '
            print self.bfv_total_id.responsable_ids
            print 'responsable_id ------------ '
            print self.bfv_total_id.responsable_id"""
                        
        else:            
            return {
                'type': 'ir.actions.act_window',
                    'name': 'Selectionner le prescripteur',
                    'view_mode': 'form',
                    'view_type': 'form',
                    'res_model': 'select.prescripteur',
                    'target': 'new',
                    'context':{'bvf_list':self._context.get('active_ids')}
                    }
            

            
        
