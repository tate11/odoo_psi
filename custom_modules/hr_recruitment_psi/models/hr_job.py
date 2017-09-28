# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError

class hr_job(models.Model):
    
    _inherit = "hr.job"
    
    name = fields.Char(size=28, required=True)
    psi_contract_type = fields.Selection([
        ('cdd', 'CDD'),
        ('cdi', 'CDI'),
        ('prestataire','Prestataire')
    ], string='Type de contrat', help="Type contract", required=True)
    
    psi_contract_duration = fields.Integer(string="Durée du contrat", required=True)
    psi_motif = fields.Text(string="Motif du recrutement", required=True)
    poste_description = fields.Text(string="Description des objectifs reliés au travail", required=True)
    
      
    state = fields.Selection([
        ('open', '1- Demande d\'embauche'),
        ('analyse', '2- Analyse de la demande'),
        ('rr_validation', '3- Approbation par RR'),
        ('tdr_redaction', '4- Rédaction TDR'),
        ('refused', '5- Refusé'),
        ('recruit', '6- Appel aux candidatures')
    ], string='Status', readonly=True, required=True, track_visibility='always', copy=False, default='open', help="Set whether the recruitment process is open or closed for this job position.")
    
    recrutement_type_id = fields.Many2one('hr.recruitment.type', string='Type de recrutement')
    recrutement_type = fields.Selection(related='recrutement_type_id.recrutement_type',string='Type de recrutement selection')
    level_of_education_id = fields.Many2one('hr.recruitment.degree', string='Niveau de formations', required=True)
    psi_budget_code = fields.Many2one('account.analytic.account',string='Code budgetaire',  required=True)
    place_of_employment = fields.Char(string='Lieu d\'embauche', required=True)
    subordination_link_id = fields.Many2one('hr.subordination.link', string='Lien de Subordination')
    experience_required_ids = fields.One2many('hr.experience.required', 'job_id', string='Expérience requise', required=True)
    nature_recrutement = fields.Selection([
        ('conssideration_dossier', 'Conssideration de dossier'),
        ('interne', 'Appel à candidature interne'),
        ('externe', 'Appel à candidature externe'),
        ('externe_interne', 'Appel à candidature externe et interne')
        ], string="Nature de recrutement", required=True)
    
    application_deadline_date = fields.Date(string="Delai de candidature", required=True)
    
    @api.one
    @api.constrains('psi_contract_duration')
    def _check_psi_contract_duration(self):
        for record in self:
            if record.psi_contract_type == 'cdd' and record.psi_contract_duration == 0:
                raise ValidationError("Le durée de contrat ne doit pas etre 0")
    
#     def set_recruit(self):
#         for record in self:
#             no_of_recruitment = 1 if record.no_of_recruitment == 0 else record.no_of_recruitment
#             record.signal_workflow('button_relance')
#             record.write({'state': 'open', 'no_of_recruitment': no_of_recruitment})
#         return True

   
class SubordinationLink(models.Model):
     _name = 'hr.subordination.link'
     
     name = fields.Char(string='Subordination', required=True)

class ExperienceRequise(models.Model):
      _name ='hr.experience.required'
      
      name = fields.Char(string='Domaines', required=True)
      month = fields.Integer(string='Mois')
      year = fields.Integer(string='Années')
      job_id = fields.Many2one('hr.job')
