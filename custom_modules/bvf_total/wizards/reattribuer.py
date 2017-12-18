# -*- coding: utf-8 -*-

from odoo import api, models,fields

class reattribuer_bvf(models.TransientModel):
    _name = "reattribuer.bvf"
    
    def _compute_bvf_ids(self):
        return self._context.get('active_ids')
    
    @api.model
    def filter_users(self):
        
        group = self.env.ref('bvf_total.group_prescripteur')
        print 'self.env.user.service_id'
        print self.env.user.service_id.name
        if self.env.user in group.users:
            print group.users.mapped('service_id.name')
            return "[('id','in',%s)]"%group.users.filtered(lambda x:x.service_id == self.env.user.service_id).ids
        
        group = self.env.ref('bvf_total.group_comptables')
        if self.env.user in group.users:
            return "[('id','in',%s)]"%group.users.ids
        
        group = self.env.ref('bvf_total.group_tresoriers')
        if self.env.user in group.users:
            return "[('id','in',%s)]"%group.users.ids
        
        group = self.env.ref('bvf_total.group_agent_administratif')
        if self.env.user in group.users:
            return "[('id','in',%s)]"%group.users.ids                              
                
        
    utilisateur_id = fields.Many2one(string='Utilisateur', comodel_name='res.users', domain=filter_users)
    #utilisateur_id = fields.Many2one(string='Utilisateur', comodel_name='res.users', default=filter_users)
    commentaire = fields.Text(string='Commentaire', size = 200)
    bvf_ids = fields.Many2many(string='BVFs', comodel_name='bvf.total', default=_compute_bvf_ids)
    
    @api.multi
    def reattribuer_bvf_action(self):
        for bvf in self.bvf_ids:
            if(bvf.state == 'recu_verifiee'):
                bvf.message_post(body=('Agent Administratif responsable : %s <br/> Commentaire : %s') %(self.utilisateur_id.name, self.commentaire) )
                bvf.responsable_id = self.utilisateur_id
            if(bvf.state == 'envoi_presc' or bvf.state == 'retour_prescr_treso'):
                bvf.responsable_id = self.utilisateur_id
                bvf.prescripteur_resp = self.utilisateur_id.name
                bvf.message_post(body=('Prescripteur responsable : %s <br/> Commentaire : %s') %(bvf.prescripteur_resp, self.commentaire) )
            elif(bvf.state == 'ok_paimt_normal' or bvf.state == 'ok_paimt_immediat'or bvf.state == 'refacturer' or bvf.state == 'compta_gen_nd'):
                bvf.comptable_resp =  self.utilisateur_id.name
                bvf.message_post(body=('Comptable responsable : %s <br/> Commentaire : %s') %(bvf.comptable_resp, self.commentaire) )
            elif(bvf.state == 'bon_a_payer' or bvf.state == 'recu_treso' or bvf.state == 'Payée'):
                bvf.tresorier_resp =  self.utilisateur_id.name   
                bvf.message_post(body=('Tresorier responsable : %s <br/> Commentaire : %s') %(bvf.tresorier_resp, self.commentaire) )           