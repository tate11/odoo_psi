# -*- coding: utf-8 -*-

from odoo import fields, models

class hr_job(models.Model):
    
    _inherit = "hr.job"
    
    name = fields.Char(size=28, required=True)
    contract_type = fields.Selection([
        ('cdd', 'CDD'),
        ('cdi', 'CDI')
    ], string='Type de contrat', help="Type contract", required=True)
    
    contract_duration = fields.Integer(string="Durée du contrat")
    motif = fields.Text(string="Motif du recrutement", required=True)
    poste_description = fields.Text(string="Description des objectifs reliés au travail", required=True)
    formation_requise = fields.Text(string="Formation requise")
    duration_minimale = fields.Integer(string="Durées minimales")
    
    state = fields.Selection([
        ('open', '1- Demande d\'embauche'),
        ('analyse', '2- Analyse de la demande'),
        ('rr_validation', '3- Approbation par RR'),
        ('tdr_redaction', '4- Rédaction TDR'),
        ('refused', '5- Refusé'),
        ('recruit', '6- Appel aux candidatures')
    ], string='Status', readonly=True, required=True, track_visibility='always', copy=False, default='open', help="Set whether the recruitment process is open or closed for this job position.")
    
    domaine_id = fields.Many2one('hr.job.domaine', string='Domaines')
    recrutement_type_id = fields.Many2one('hr.recruitment.type', string='Type de recrutement')
    recrutement_type = fields.Selection(related='recrutement_type_id.recrutement_type',string='Type de recrutement selection')
    
#     def set_recruit(self):
#         for record in self:
#             no_of_recruitment = 1 if record.no_of_recruitment == 0 else record.no_of_recruitment
#             record.signal_workflow('button_relance')
#             record.write({'state': 'open', 'no_of_recruitment': no_of_recruitment})
#         return True

class Domaine(models.Model):
    _name = 'hr.job.domaine'
    
    name = fields.Char(string="Domaine", required=True)