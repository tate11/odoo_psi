# -*- coding: utf-8 -*-

from odoo import api, models,fields, exceptions
from datetime import date

class Fournisseur_total(models.Model):
    _name = "fournisseur.total"
    _rec_name = 'raison_social'
    
    raison_social = fields.Char(string='Nom ou Raison Sociale du prestataire', required=True, size=100)
    code_sap = fields.Char(string='Code SAP', size=10, required=True)
    #nif = fields.Integer(string='NIF', size=10, required=True)
    #num_stat = fields.Integer(string='N° STAT', size=18, required=True)
    
    nif = fields.Char(string='NIF', size=20)
    num_stat = fields.Char(string='N° STAT', size=20)
    
    adresse = fields.Char(string='Adresse', size=100, required=True)
    # pays = fields.Char(string='Pays')
    pays = fields.Many2one('res.country', string='Pays', required=True)
    
    #delai_paiement = fields.Many2one('delai_paiement.total', string='Délai de paiement', help="", required=True) 
    delai_paiement = fields.Many2one(comodel_name='account.payment.term', string='Délai de paiement', required=True) 
     
    bvf_ids = fields.One2many(comodel_name='bvf.total', inverse_name='fournisseur', string='BVF')
    
    bvf_liaison = fields.Boolean(string='Fournisseur lié à un BVF', compute='_compute_bvf_liaison')
    
    _sql_constraints = [
        ('codesap_uniq', 'unique(code_sap)', 'Ce code SAP existe déjà. Veuillez vérifier!'),
    ]
            
    @api.depends('bvf_ids')                
    def _compute_bvf_liaison(self):
        for record in self:
            if record.bvf_ids :
                record.bvf_liaison = True
            else:
                record.bvf_liaison = False

    @api.multi
    def unlink(self): 
        list_bvfs = []
        for record in self:
            if record.bvf_ids:
                list_bvfs.append(record.raison_social)
            
                
        if list_bvfs:
            raise exceptions.UserError('Suppression impossible: Le(s) fournisseur(s) %s est(sont) déjà rattaché(s) à un BVF' %str(', '.join(list_bvfs))) 
        else:
            return super(Fournisseur_total, self).unlink()  
