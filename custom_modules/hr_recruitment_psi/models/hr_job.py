# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError

class hr_job(models.Model):
    
    _inherit = "hr.job"
    
    name = fields.Char(size=28, required=True)
    
    psi_contract_type = fields.Selection([
        ('cdd', 'CDD'),
        ('cdi', 'CDI'),
        ('prestataire',u'Préstataire')
    ], string='Type de contrat', help="Type de contrat")
    
    psi_contract_duration = fields.Integer(string=u"Durée du contrat")
    psi_motif = fields.Text(string="Motif du recrutement")
    poste_description = fields.Text(string=u"Déscription des objectifs reliés au travail")
      
    state = fields.Selection([
        ('open', '1- Demande d\'embauche'),
        ('tdr_redaction', '2- Rédaction TDR'),
        ('validation_finance','3- Validation Finance'),
        ('analyse', '4- Analyse de la demande'),
        ('rr_validation', '5- Approbation par RR'), 
        ('refused', '6- Refusé'),
        ('recruit', '7- Appel aux candidatures')
    ], string='Status', readonly=True, track_visibility='onchange', copy=False, default='open', help="Set whether the recruitment process is open or closed for this job position.")
    
    recrutement_type_id = fields.Many2one('hr.recruitment.type', string='Type de recrutement')
    recrutement_type = fields.Selection(related='recrutement_type_id.recrutement_type', string=u'Type de recrutement sélection')
    tdr_file = fields.Binary(string='TDR')
    level_of_education_id = fields.Many2one('hr.recruitment.degree', string='Niveau de formation')
    psi_budget_code_distribution = fields.Many2one('account.analytic.distribution', string='Code budgetaire')
    place_of_employment = fields.Char(string=u'Lieu d\'embauche')
    subordination_link_id = fields.Many2one('hr.subordination.link', string='Lien de Subordination')
    experience_required_ids = fields.One2many('hr.experience.required', 'job_id', string=u'Expériences requises')
    
    nature_recrutement = fields.Selection([
        ('conssideration_dossier', u'Reconsidération de dossier'),
        ('conssideration_dossier_by_cvtheque', u'Reconsidération de dossier par CVThèque'),
        ('interne', u'Appel à candidature interne'),
        ('externe', u'Appel à candidature externe')
        ], string="Nature de recrutement")
    
    application_deadline_date = fields.Date(string=u"Délai de candidature")
    
    @api.one
    @api.constrains('psi_contract_duration')
    def _check_psi_contract_duration(self):
        for record in self:
            if record.psi_contract_type == 'cdd' and record.psi_contract_duration == 0:
                raise ValidationError(u"La durée de contrat ne doit pas être 0")
    
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
