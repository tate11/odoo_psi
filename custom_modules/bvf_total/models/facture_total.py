# -*- coding: utf-8 -*-

from odoo import api,models,fields, exceptions
from datetime import date
from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT

class Facture_total(models.Model):
    _name = "facture.total"
    _rec_name = 'numero'
    _order = 'date_reception DESC'
    
    numero = fields.Char(string='Numéro Facture', required=True, size = 20)
    
    
    date_reception = fields.Date(string='Date de réception de la facture', default=fields.Date.today(), required=True)   
    comment = fields.Text(string='Commentaire', size=250)
    fournisseur = fields.Many2one('fournisseur.total', string='Nom Fournisseur', required=True)
    facture_scannee = fields.Binary("Facture Scannée", help="Veuillez joindre la facture scannée")
    filename = fields.Char(string='Filename')
    #attachment_file_ids = fields.Many2one('ir.attachment',string='Attachments')
    
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('resent', 'Retour au fournisseur'),
        ('verified', 'Reçue et verifiéée'),
        ('tobecreated', u'BVF à créer'),
        ('createdbvf', 'BVF créé'),
        ], string='Etat', readonly=True, default='draft', track_visibility='onchange')
    
    _sql_constraints = [
        ('numero_uniq', 'unique(numero, fournisseur)', 'Le numéro de la facture doit être unique par fournisseur !'),
    ]        
    
    def set_to_recue_et_verifiee(self):
        #self.write({'state': 'verified'})  
        return {
            'type': 'ir.actions.act_window',
            'name': 'Confirmation de changement de statut',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'change.status.facture',
            'target': 'new',
            'context':{'state': 'verified', 'default_facture_total_id':self.id, 'default_status':'Reçue et vérifiée'}
            }      
    
    def set_to_resent(self):
        #self.write({'state': 'resent'})        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Confirmation de changement de statut',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'change.status.facture',
            'target': 'new',
            'context':{'state': 'resent', 'default_facture_total_id':self.id, 'default_status':'Retour au Fournisseur'}
            }  
               
    
    def set_to_be_created(self):
        #self.write({'state': 'tobecreated'})
        return {
            'type': 'ir.actions.act_window',
            'name': 'Bordereau de Vérification des factures',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'bvf.total',
            'target': 'current',
            'context' : {'default_numero_facture':self.id, 'default_fournisseur':self.fournisseur.id}
        }

        
    @api.onchange('date_reception')                
    def onchange_date_reception(self):
        for record in self:
            message = ""
            if record.date_reception >  date.today().strftime(DEFAULT_SERVER_DATE_FORMAT):
                record.date_reception = False
                message = u"La date de réception de la facture doit être inférieure ou égale à la date du jour."
                                
            warning = {
                'title': "Contrôle de la date de réception",
                'message': message
                }
            
            if message:
                return {'warning': warning}
            #if message:
                #raise exceptions.UserError(message)
                
    @api.multi
    def unlink(self): 
        list_factures_liees = []
        for record in self:
            if record.state == 'createdbvf':
                list_factures_liees.append(record.numero)
            
                
        if list_factures_liees:
            raise exceptions.UserError(u'Suppression impossible: la/les facture(s) %s est(sont) déjà rattaché(s) à un BVF' %str(', '.join(list_factures_liees))) 
        else:
            return super(Facture_total, self).unlink()  
                
