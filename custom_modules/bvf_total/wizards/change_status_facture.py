# -*- coding: utf-8 -*-

from odoo import api, models,fields

class change_status_facture(models.TransientModel):
    _name = "change.status.facture"
    
    status = fields.Char(string='Status')
    facture_total_id = fields.Many2one(string='Facture total', comodel_name='facture.total')
    
    @api.multi
    def change_status_action(self):
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
            
        
