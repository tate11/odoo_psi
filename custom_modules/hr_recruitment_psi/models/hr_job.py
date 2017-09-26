# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError

class hr_job(models.Model):
    
    _inherit = "hr.job"
    
    name = fields.Char(size=28, required=True)
    contract_type = fields.Selection([
        ('cdd', 'CDD'),
        ('cdi', 'CDI')
    ], string='Type de contrat', help="Type contract", required=True)
    
    contract_duration = fields.Integer(string="Durée du contrat", required=True)
    motif = fields.Text(string="Motif du recrutement", required=True)
    poste_description = fields.Text(string="Description des objectifs reliés au travail", required=True)
   # formation_requise = fields.Text(string="Formation requise")
   # duration_minimale = fields.Integer(string="Durées minimales")
    
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
    budget_code = fields.Char(string='Code budgetaire', required=True)
    place_of_employment = fields.Char(string='Lieu d\'embauche', required=True)
    subordination_link_id = fields.Many2one('hr.subordination.link', string='Lien de Subordination', required=True)
    experience_required_ids = fields.One2many('hr.experience.required', 'id', string='Expérience requise')
    nature_recrutement = fields.Selection([
        ('interne', 'Appel à candidature interne'),
        ('externe', 'Appel à candidature externe')
        ], string="Nature de recrutement")
    
    @api.one
    @api.constrains('contract_duration')
    def _check_contract_duration(self):
        for record in self:
            if record.contract_type == 'cdd' and record.contract_duration == 0:
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
      duration = fields.Integer(string='Durées minimales', required=True)
