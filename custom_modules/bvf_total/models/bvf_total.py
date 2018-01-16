# -*- coding: utf-8 -*-

from datetime import date
from datetime import datetime
from datetime import timedelta
from time import strptime

from odoo import api, models, fields, exceptions
from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT
from odoo.workflow.instance import create


class BVF_total(models.Model):
    _name = "bvf.total"
    _description = "BVF"
    _rec_name = 'numero_facture'
    _order = 'date_reception DESC'
    _inherit = ['mail.thread']
    
    numero = fields.Char(string='Num du BVF', readonly=True)    

    responsable_id = fields.Many2one(string='Responsable', comodel_name='res.users')
    responsable_ids = fields.Many2many(string='Responsables bvf', comodel_name='res.users')
    
    prescripteur_resp = fields.Char(string='Prescripteur responsable')
    date_approbation_dir = fields.Char('JJ/MM/AAAA', readonly=True)
    
    comptable_resp = fields.Char(string='Comptable responsable')
    date_reception_compte = fields.Char('JJ/MM/AAAA', readonly=True)
    
    tresorier_resp = fields.Char(string='Tresorier responsable')
    date_reception_compte_banque = fields.Char('JJ/MM/AAAA', readonly=True)
    # employee_id = fields.Many2one('hr.employee', string='Demandeur', required=True)
    
    nature = fields.Selection([('acompte','Acompte'),('definitive','Definitive'),('avoir','Avoir')], string="Nature", default='acompte')
    
    acompte = fields.Boolean(string='Acompte')
    definitive = fields.Boolean(string=u'Définitive')
    avoir = fields.Boolean(string='Avoir')
    
    fournisseur = fields.Many2one('fournisseur.total', string='Fournisseur', required=True)
    
    numero_facture = fields.Many2one('facture.total', size=20 , string=u'Numéro Facture', required=True, domain=[('state','=','verified')])    
    
    agentadmin_resp_id = fields.Many2one(string='Agent Administratif', comodel_name='res.users')
    loginIgg = fields.Char(compute='_compute_loginIgg', string='IGG', store=True)
    date_reception = fields.Date(string=u'Date de réception')
    
    # calcul de l'echeance
    #date_reception_facture = fields.Date(related='date_reception', string='Date de réception')
    date_reception_facture = fields.Char(compute='_compute_date_reception', string=u'Date de réception de la facture', readonly=True)
        
    #date_facture = fields.Date(string='Date Facture', default=date.today().strftime('%Y-%m-%d'), required=True)
    date_facture = fields.Date(string='Date de facturation', required=True)
    
    echeance = fields.Date(compute='_compute_echeance', string=u"Date d'échéance", store=True)
    date_echeance = fields.Char(compute='_compute_echeance')
        
    montant_ttc = fields.Float(string='Montant TTC', required=True)     
    #devise = fields.Char(string='Devise')
    #devise = fields.Selection([('ariary','MGA'),('dollar','USD'),('euro','EUR')], string="Devise", required=True)
    devise = fields.Many2one('res.currency', string='Devise', required=True, domain=[('active','=', True)])   
    observation = fields.Text(string='Observation', size = 250)
    a_refacturer = fields.Char(string='A refacturer')
    compensation = fields.Char(string='Compensation', size=100)
    
    statut_label = fields.Char(compute='_compute_statut', string="Statut", store=True)
    
    numero_commande = fields.Char(string='Commande', size=50)
    numero_ded = fields.Char(string='AFE', size=50)
    numero_fiche_immo = fields.Char(string='Fiche Immo', size=50)
    numero_em = fields.Char(string='EM', size=50)    
    numero_ef = fields.Char(string='NÂ° EF', size=50)
    numero_nd = fields.Char(string='ND NÂ°', size=100)    
    
    date_bon_a_payer = fields.Date(string=u'Date bon à  payer')
    date_reglement = fields.Date(string=u'Date de règlement')
    # banque_reglement = fields.Selection([('bni','BNI'),('boa','BOA'),('bfv','BFV'),('bmoi','BMOI')], string="Banque")
    banque_reglement = fields.Many2one('account.journal', string='Banque')
    numero_cheque = fields.Char(string=u'NÂ° Chèque')
    date_virement = fields.Date(string='Virement du')
    numero_piece_reglement = fields.Char(string=u'NÂ° pièce de règlement')  
    space = fields.Char('\n', readonly=True)
    space_reglement = fields.Char('REGLEMENT', readonly=True)
        
    state = fields.Selection([
        ('recu_verifiee', u'Reçue et vérifiée'),
        ('irreguliere', u'Irrégulières'),
        ('envoi_presc', 'Envoi aux prescripteurs'),
        ('ok_paimt_normal', 'OK pour paiement normal'),
        ('ok_paimt_immediat', u'OK pour paiement immédiat'),
        ('retour_bvf_compta', 'Retour modification BVF Compta'),
        ('retour_bvf_treso', u'Retour modification BVF Tréso'),
        ('retour_prescr_treso', u'Retour au prescripteur Tréso'),
        ('bon_a_payer', u'Bon à  payer'),
        ('refacturer', 'Refacturer'),
        ('compta_gen_nd', 'Compta Gen pour ND'),
        ('recu_treso', u'Reçue Tréso'),
        ('payee', u'Payée'),
        ], string='Etat', readonly=True, default='recu_verifiee', track_visibility='onchange')
    
    @api.constrains('acompte', 'definitive', 'avoir')
    def _validate_nature(self):      
        if (not self.acompte and not self.definitive and not self.avoir):
            raise exceptions.ValidationError(u"La nature du BVF doit àªtre renseignée!")
        
    @api.model
    def create(self, vals):
        vals['numero'] = self.env['ir.sequence'].next_by_code('num.bvf')
        
        vals['loginIgg'] = self.env.user.login
        vals['responsable_id'] = self.env.user.id
        
        print '_compute_loginIgg----------'
        print vals['loginIgg']
        
        if  vals['montant_ttc'] == 0.0:
            raise exceptions.UserError(u'Le montant de la facture doit àªtre supérieur à  zéro.') 
        else:
            if vals['acompte'] == True:
                vals['nature'] = 'acompte'
            elif vals['definitive'] == True:
                vals['nature'] = 'definitive'
            elif vals['avoir'] == True:
                vals['nature'] = 'avoir'
            res = super(BVF_total, self).create(vals)
            res.numero_facture.write({'state': 'createdbvf'})
            return res
        
    @api.multi
    def unlink(self): 
        for record in self:
            record.numero_facture.write({'state': 'verified'})
        return super(BVF_total, self).unlink()  
                       
    def _compute_numero_bvf(self):
        self.numero = self.env['ir.sequence'].next_by_code('num.bvf')
        print 'self.numero----------'
        print self.numero      
        
        
    def _compute_loginIgg(self):
        for record in self:
            if record.create_uid:
                record.loginIgg = record.create_uid.login
                record.agentadmin_resp_id = record.create_uid
            else :
                record.loginIgg = record.env.user.login
                record.agentadmin_resp_id = record.env.user
            print '_compute_loginIgg----------'
            print record.loginIgg
                
    @api.depends('date_facture')    
    def _compute_echeance(self):
        for record in self:
            delai_paiement = record.fournisseur.delai_paiement.line_ids.filtered(lambda line:line.value == 'balance')
            if (record.date_facture and delai_paiement):
                record.echeance = record.date_facture and datetime.strptime(record.date_facture,"%Y-%m-%d") + timedelta(days=delai_paiement.days)
                record.date_echeance = record.echeance and datetime.strptime(record.echeance, DEFAULT_SERVER_DATE_FORMAT).strftime('%d/%m/%Y')
                
    @api.depends('date_reception')    
    def _compute_date_reception(self):
        for record in self:
            if (record.date_reception != False):
                record.date_reception_facture = record.date_reception and datetime.strptime(record.date_reception, DEFAULT_SERVER_DATE_FORMAT).strftime('%d/%m/%Y')
            else:
                print''
                #record.date_reception_facture = "JJ/MM/AAAA"
                #record.date_approbation_dir = "JJ/MM/AAAA"
                #record.date_reception_compte = "JJ/MM/AAAA"
                #record.date_reception_compte_banque = "JJ/MM/AAAA"
                
    def _compute_date(self):
        print ''
        #for record in self:
                #record.date_approbation_dir = "JJ/MM/AAAA"
                #record.date_reception_compte = "JJ/MM/AAAA"
                #record.date_reception_compte_banque = "JJ/MM/AAAA"
    
    @api.depends('echeance')             
    def _compute_statut(self):
        for record in self:            
            #diff_day = record.echeance - datetime.date   
            diff_day = 0   
            date_format = "%Y-%m-%d"
            a = record.echeance and datetime.strptime(record.echeance, date_format)
            b = datetime.strptime(date.today().strftime('%Y-%m-%d'), date_format)
            if a != False:
                diff_day = abs((b - a).days)
                #print '------------------------> _compute_statut'
                #print diff_day
                
            if (diff_day <=7):
                record.statut_label = u'Très urgent'
            else:
                if(diff_day <=15):
                    record.statut_label = 'Urgent'
                else:
                    record.statut_label = 'Normal'
                    
    """def _compute_login_igg(self):
        for record in self:  
            record.loginIgg = self.env.user.login"""
  
    """@api.onchange('numero_cheque')                
    def onchange_acompte(self):
        for record in self:
            if record.acompte :
                record.definitive = False
                record.avoir = False
            else:
                record.definitive = True
                record.avoir = True"""
                
    @api.onchange('numero_cheque')                
    def onchange_numero_cheque(self):
        for record in self:
            if record.numero_cheque :
                record.date_virement = False
                
    @api.onchange('date_virement')                
    def onchange_date_virement(self):
        for record in self:
            if record.date_virement :
                record.numero_cheque = False
                
    @api.onchange('numero_facture')                
    def onchange_numero_facture(self):
        for record in self:
            if record.numero_facture :
                record.date_reception = record.numero_facture.date_reception
                
    @api.onchange('acompte')                
    def onchange_nature(self):
        for record in self:
            if record.acompte :
                record.definitive = False
                record.avoir = False
                record.nature = 'acompte'
                
    @api.onchange('definitive')                
    def onchange_definitive(self):
        for record in self:
            if record.definitive :
                record.acompte = False
                record.avoir = False
                record.nature = 'definitive'
                
    @api.onchange('avoir')                
    def onchange_avoir(self):
        for record in self:
            if record.avoir :
                record.acompte = False
                record.definitive = False
                record.nature = 'avoir'
    
    @api.multi            
    def action_to_do(self):
        return self.env['report'].get_action(self, 'bvf_total.report_bvf_total')
        
    def action_reattribuer(self):
        return {
            'type': 'ir.actions.act_window',
                'name': 'Confirmation de changement de statut',
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'change.status',
                'target': 'new',
                'context':{'state': 'envoi_presc', 'default_bfv_total_id':self.id, 'default_status':'Envoi au prescripteur'}
                }
        
    def action_envoi_presc(self):
        return {
            'type': 'ir.actions.act_window',
                'name': 'Confirmation de changement de statut',
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'change.status',
                'target': 'new',
                'context':{'state': 'envoi_presc', 'default_bfv_total_id':self.id, 'default_status':'Envoi au prescripteur'}
                }
        
    def action_irreguliere(self):
        #self.write({'state': 'recu_verifiee'})
        return {
            'type': 'ir.actions.act_window',
                'name': 'Confirmation de changement de statut',
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'change.status',
                'target': 'new',
                'context':{'state': 'recu_verifiee', 'default_bfv_total_id':self.id, 'default_status':'Retourner au fournisseur pour correction'}
                }
        
    def action_retour_frnsr(self):
        #self.write({'state': 'irreguliere'})
        return {
            'type': 'ir.actions.act_window',
                'name': 'Confirmation de changement de statut',
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'change.status',
                'target': 'new',
                'context':{'state': 'irreguliere', 'default_bfv_total_id':self.id, 'default_status':u'Irrégulière'}
                }
        
    def action_ok_paimt_normal(self):
        #self.write({'state': 'ok_paimt_normal'})   
        return {
            'type': 'ir.actions.act_window',
                'name': 'Confirmation de changement de statut',
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'change.status',
                'target': 'new',
                'context':{'state': 'ok_paimt_normal', 'default_bfv_total_id':self.id, 'default_status':'OK pour paiement normal'}
                }     
        
    def action_refacturer(self):
        #self.write({'state': 'refacturer'})
        null_fields = []
        if not self.numero_ef:
            null_fields.append(u'NÂ° EF')
        if not self.compensation and self.acompte and self.state in ['ok_paimt_normal', 'ok_paimt_immediat']:
            null_fields.append(u'EM')
        if null_fields:
            raise exceptions.UserError("Veuillez renseigner les champs suivants: %s" %', '.join(null_fields))
        return {
            'type': 'ir.actions.act_window',
                'name': 'Confirmation de changement de statut',
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'change.status',
                'target': 'new',
                'context':{'state': 'refacturer', 'default_bfv_total_id':self.id, 'default_status':'A Refacturer'}
                }
        
    def action_compta_gen_pour_nd(self):
        #self.write({'state': 'compta_gen_nd'})
        return {
            'type': 'ir.actions.act_window',
                'name': 'Confirmation de changement de statut',
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'change.status',
                'target': 'new',
                'context':{'state': 'compta_gen_nd', 'default_bfv_total_id':self.id, 'default_status':u'Compta Gén pour ND'}
                }
        
    def action_retour_prescr_compta(self):
        #self.write({'state': 'envoi_presc'}) 
        return {
            'type': 'ir.actions.act_window',
                'name': 'Confirmation de changement de statut',
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'change.status',
                'target': 'new',
                'context':{'state': 'envoi_presc', 'default_bfv_total_id':self.id, 'default_status':'Retour aux prescripteurs compta'}
                }       
        
    def action_retour_modif_compta(self):
        #self.write({'state': 'recu_verifiee'})
        return {
            'type': 'ir.actions.act_window',
                'name': 'Confirmation de changement de statut',
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'change.status',
                'target': 'new',
                'context':{'state': 'recu_verifiee', 'default_bfv_total_id':self.id, 'default_status':'Retour aux agents admin pour modification BVF compta'}
                }
        
    def action_ok_paimt_immediat(self):
        #self.write({'state': 'ok_paimt_immediat'})
        return {
            'type': 'ir.actions.act_window',
                'name': 'Confirmation de changement de statut',
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'change.status',
                'target': 'new',
                'context':{'state': 'ok_paimt_immediat', 'default_bfv_total_id':self.id, 'default_status':u'OK pour paiement immédiat'}
                }
        
    def action_bon_a_payer(self):
        #self.write({'state': 'bon_a_payer'})
        if not self.numero_ef:
            raise exceptions.UserError("Veuillez renseigner le N° EF")
        else:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Confirmation de changement de statut',
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'change.status',
                'target': 'new',
                'context':{'state': 'bon_a_payer', 'default_bfv_total_id':self.id, 'default_status':u'Bon à  Payer'}
                }
        
    def action_retour_compta(self):
        #self.write({'state': 'ok_paimt_normal'})
        return {
            'type': 'ir.actions.act_window',
                'name': 'Confirmation de changement de statut',
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'change.status',
                'target': 'new',
                'context':{'state': 'ok_paimt_normal', 'default_bfv_total_id':self.id, 'default_status':u'Retour à  la compta'}
                }
        
    def action_retour_modif_treso(self):
        #self.write({'state': 'recu_verifiee'})
        return {
            'type': 'ir.actions.act_window',
                'name': 'Confirmation de changement de statut',
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'change.status',
                'target': 'new',
                'context':{'state': 'recu_verifiee', 'default_bfv_total_id':self.id, 'default_status':'Retour aux agents admin pour modification BVF treso'}
                }
        
    def action_retour_prescr_treso(self):
        #self.write({'state': 'envoi_presc'})
        return {
            'type': 'ir.actions.act_window',
                'name': 'Confirmation de changement de statut',
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'change.status',
                'target': 'new',
                'context':{'state': 'envoi_presc', 'default_bfv_total_id':self.id, 'default_status':'Retour aux Prescripteurs Treso'}
                }
        
    def action_recu_treso(self):
        #self.write({'state': 'recu_treso'})
        return {
            'type': 'ir.actions.act_window',
                'name': 'Confirmation de changement de statut',
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'change.status',
                'target': 'new',
                'context':{'state': 'recu_treso', 'default_bfv_total_id':self.id, 'default_status':u'Reçue Tréso'}
                }
        
    def action_payee(self):
        #self.write({'state': 'payee'})
        fields = {u'Date de règlement': self.date_reglement,
                  u'Date bon à  payer': self.date_bon_a_payer, 
                  u'NÂ° pièce de règlement': self.numero_piece_reglement}
        null_fields = ', '.join([item[0] for item in fields.iteritems() if not item[1]])
        if null_fields:
            raise exceptions.UserError("Veuillez renseigner les champs suivants: %s" % null_fields)
        else:
            return {
                'type': 'ir.actions.act_window',
                    'name': 'Confirmation de changement de statut',
                    'view_mode': 'form',
                    'view_type': 'form',
                    'res_model': 'change.status',
                    'target': 'new',
                    'context':{'state': 'payee', 'default_bfv_total_id':self.id, 'default_status':u'Payée'}
                    }
