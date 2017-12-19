# -*- coding: utf-8 -*-

from datetime import date
from odoo import api, models,fields
from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT

class second_confirm(models.TransientModel):
    _name = "second.confirm.facture"
        
    status = fields.Char(string='Status')
    facture_total_id = fields.Many2one(string='Facture total', comodel_name='bvf.total')
    
    @api.multi
    def second_confirm_facture_action(self):
        self.facture_total_id.update({'state': self._context.get('state')})
        #print 'self.facture_total_id.state ------------ '
        #print self._context.get('state')
        #print self.bfv_total_id
        
        if self._context.get('state') == 'resent':
            # Si une facture est retournée au fournisseur, le renommer par n° facture+RFx, x allant de 1 à 9
            last_facture = self.facture_total_id.search([('fournisseur','=',self.facture_total_id.fournisseur.id), ('numero','ilike',self.facture_total_id.numero+'%'), ('id','!=', self.facture_total_id.id)], order='numero desc',limit=1)
            if not last_facture:
                self.facture_total_id.numero = self.facture_total_id.numero + ' RF1'
            else:
                self.facture_total_id.numero = last_facture.numero[:-1] + str(int(last_facture.numero[-1])+1)
                        
        """else:            
            return {
                'type': 'ir.actions.act_window',
                    'name': 'Selectionner le prescripteur',
                    'view_mode': 'form',
                    'view_type': 'form',
                    'res_model': 'select.prescripteur',
                    'target': 'new',
                    'context':{'bvf_list':self._context.get('active_ids')}
                    }"""
            

            
        
