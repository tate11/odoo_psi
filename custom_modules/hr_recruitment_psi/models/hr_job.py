# -*- coding: utf-8 -*-

import datetime

from pychart.arrow import default

from odoo import fields, models, api, netsvc
from odoo.exceptions import ValidationError, Warning


class hr_job(models.Model):
    
    _inherit = "hr.job"
    
    name = fields.Char(size=60, required=True)
    
    psi_contract_type = fields.Selection([
        ('cdd', 'CDD'),
        ('cdi', 'CDI'),
        ('prestataire','Prestataire'),
        ('convention_stage','Convention de stage')
    ], string='Type de contrat', help="Type de contrat")
    
    tdr_file = fields.Many2one('ir.attachment',string='Termes de Références (TDR)')
    file = fields.Binary("your_file", model='tdr_file.datas')
    
    name_of_claimant = fields.Many2one('res.users', string=u"Nom du demandeur") 
    
    no_of_recruitment = fields.Integer(string=u'Nombre de poste(s) à pouvoir', help=u'Nombre de poste(s) à pouvoir.')

    website_published = fields.Boolean(default=False)
    
    psi_contract_duration = fields.Integer(string=u"Durée du contrat (en mois)")
    psi_motif = fields.Char(string="Motif du recrutement")
    poste_description = fields.Text(string=u"Mission")
      
    state = fields.Selection([
        ('open', '1- Demande d\'embauche'),
        ('validation_finance','2- Validation Finance'),
        ('analyse', '3- Analyse de la demande'),
        ('rr_validation', '4- Approbation par RR'), 
        ('refused', '5- Refusé'),
        ('recruit', '6- Appel aux candidatures')
    ], string='Status', readonly=True, track_visibility='onchange', copy=False, default='open', help="Set whether the recruitment process is open or closed for this job position.")
    
    recrutement_type_id = fields.Many2one('hr.recruitment.type', string='Type de recrutement', required=True)
    recrutement_type = fields.Selection(related='recrutement_type_id.recrutement_type', string=u'Type de recrutement sélection')
    tdr_file = fields.Binary(string=u'Termes de Références (TDR)')
    #tdr_file = fields.One2many('ir.attachment', 'res_id', domain=[('res_model', '=', 'hr.job')], string='Termes de Références (TDR)')
    level_of_education_id = fields.Many2one('hr.recruitment.degree', string='Niveau de formation')
    psi_budget_code_distribution = fields.Many2one('account.analytic.account', string=u'Code(s) budgétaire(s)')
    place_of_work = fields.Many2many('hr.recruitment.working.state', string='Lieu de travail')
    place_of_employment = fields.Many2one('hr.recruitment.lieu.embauche',string="Lieu d'embauche", default=lambda self: self.env['hr.recruitment.lieu.embauche'].search([('embauche_id','=','1')]))
#    place_of_employment = fields.Many2one('hr.recruitment.lieu.embauche',string="Lieu d'embauche")
    subordination_link_id = fields.Many2one('hr.subordination.link', string='Lien de Subordination')
    experience_required_ids = fields.One2many('hr.experience.required', 'job_id', string=u'Expériences requises', required=True)
    superior_hierarchical = fields.Many2one('hr.employee', string=u"Supérieur Hiérarchique")
    nature_recrutement = fields.Selection([
        ('conssideration_dossier', u'Reconsidération de dossier'),
        ('conssideration_dossier_by_cvtheque', u'Reconsidération de dossier par CVThèque'),
        ('interne', u'Appel à candidature interne'),
        ('externe', u'Appel à candidature externe')
        ], string="Nature de recrutement")
    
    application_deadline_date = fields.Date(string=u"Date limite de candidature")
    date_of_demand = fields.Date(string=u"Date de la demande", help="Date de la demande du relance")
    ref_of_demand = fields.Char(compute="_compute_reference_demande", string=u"Référence de la demande")
    num_demande = fields.Integer(string=u'num de demande')
    rr_approbation = fields.Boolean("Approbation par RR", default=True)
    tdr_add = fields.Boolean("TDR")
    psi_memo = fields.Boolean(u"Mémo", default=False)
    psi_date_start = fields.Date(string=u'Date de prise de fonction souhaitée', default=None)
    psi_job_equipment = fields.One2many('hr.job.equipment', 'job_id', string=u'Matériels et équipement(s) demandé(s)')

    psi_professional_category  = fields.Selection([
                                       ('appui','APPUI'),
                                       ('execution','EXECUTION'),
                                       ('superviseur','SUPERVISEUR'),
                                       ('coordinateur','COORDINATEUR'),
                                       ('directeur','DIRECTEUR'),
                                       ('rra','RRA')], string="Catégorie professionnelle")
    
    
    psi_category = fields.Many2one('hr.psi.category.details','Catégorie professionnelle')
    
    @api.model
    def create(self, vals):
        print "Create"
        print self.documents_count
        print vals.get('documents_count'),' documents_count'
        res = super(hr_job, self).create(vals)
        if vals.get('documents_count') == 0:
            raise Warning(u"Vous devez ajouter le fichier TDR.")
        return res
    
    @api.model
    def _compute_reference_demande(self):
        d = datetime.datetime.today()
        for record in self:
            record.ref_of_demand = 'R{:03d}'.format(record.num_demande +1) + "/" + '{:02d}'.format(d.month) + "/" + '{:02d}'.format(d.year)[2:]
    
    @api.one
    @api.constrains('psi_contract_duration')
    def _check_psi_contract_duration(self):
        for record in self:
            if record.psi_contract_type == 'cdd' and record.psi_contract_duration == 0:
                raise ValidationError(u"La durée de contrat ne doit pas être 0")
    
    @api.multi
    def set_to_open(self, cr, uid, ids, *args):
        self.write(cr, uid, ids, {'state': 'open'})
        wf_service = netsvc.LocalService("workflow")
        for id in ids:
            wf_service.trg_create(uid, 'hr.job', id, cr)
            return True
    
    @api.onchange('nature_recrutement')
    def _change_approbation_rr(self):
        if self.nature_recrutement == 'interne':
            self.rr_approbation = False
    
    @api.onchange('recrutement_type')
    def _change_recrutement_type_id(self):
        if self.recrutement_type == 'stagiaire':
            self.psi_contract_type = 'convention_stage'
        
class SubordinationLink(models.Model):
     _name = 'hr.subordination.link'
     
     name = fields.Char(string='Subordination', required=True)

class ExperienceRequise(models.Model):
      _name = 'hr.experience.required'
      
      name = fields.Char(string='Domaines', required=True)
      month = fields.Selection([
        ('1', '1'),
         ('2', '2'),
          ('3', '3'),
           ('4', '4'),
            ('5', '5'),
             ('6', '6'),
              ('7', '7'),
               ('8', '8'),
                ('9', '9'),
                 ('10', '10'),
                  ('11', '11'),
                   ('12', '12')
        ], string="en Mois")
      year = fields.Integer(string='en Année', size=2)
      job_id = fields.Many2one('hr.job')
      
                  
      @api.constrains('year')
      def _check_length_year(self):
          for record in self:
              if record.year > 99:
                  raise ValidationError(u"L'année doit être 2 chiffres au maximum: %s" % record.year)   

class WorkingState(models.Model):
    _name = "hr.recruitment.working.state"
    
    name = fields.Char(string="Lieu")
    
class Equipment(models.Model):
    _name = "hr.equipment"
    
    name = fields.Char(string=u'Désignation')

class JobEquipment(models.Model):
    _name = "hr.job.equipment"
    _description = "Inventaire - demande d\'equipement"
    
    name = fields.Char(string='Nom')
    
    equipment_state = fields.Selection([
        ('existant', 'Existant'),
        ('inexistant', 'Inexistant'),
        ('remplacement', 'Remplacement')
        ], string=u'Etat équipement')
    
    equipment_id = fields.Many2one('hr.equipment', string=u"Désignation")
    job_id = fields.Many2one('hr.job')
    
class LieuEmbauche(models.Model):
    _name = 'hr.recruitment.lieu.embauche'
    
    name = fields.Char(string="Lieu d' embauche")
    embauche_id = fields.Integer()