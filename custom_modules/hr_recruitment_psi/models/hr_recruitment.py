# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError

class RecruitmentType(models.Model):
    _name = 'hr.recruitment.type'
    
    recrutement_type = fields.Selection([
        ('collaborateur', 'Recrutement d\'un collaborateur permanent'),
        ('consultant', 'Recrutement d\'un consultant'),
        ('stagiaire', 'Recrutement d\'un stagiaire'),
        ('collaborateur_externe', 'Recrutement d\'un collaborateur permanent avec un Cabinet Externe')
    ], string='Type de recrutement')
    
    name = fields.Char(string='Nom')
    
class RecruitmentStage(models.Model):
    _inherit = "hr.recruitment.stage"
    
    stage = fields.Char("Stage", required=True)
    
    recrutement_type_ids = fields.Many2many('hr.recruitment.type', 'recrutement_stage_type_rel', 'stage_id', 'type_id', string='Stages')
    
class Applicant(models.Model):
    _inherit = "hr.applicant"
    _name = "hr.applicant"
    
    recrutement_type_id = fields.Many2one('hr.recruitment.type',related='job_id.recrutement_type_id',string='Type de recrutement')
    recrutement_type = fields.Selection(related='job_id.recrutement_type_id.recrutement_type',string='Type de recrutement selection')
    
    nature_recrutement_id = fields.Selection(related='job_id.nature_recrutement',string='Nature de recrutement')
    
    state = fields.Selection([
        ('applicant_selected','Candidature selectionnées'),
        ('convoked_for_test', '1- Convoqué pour les tests'),
        ('interview', '2- Entretients'),
        ('professional_reference','3- Références professionnelles'),
        ('bridger_insight', '4- Bridger Insight'),
        ('psi_wage_proposal', '5- Proposition salariale'), 
        ('notification_of_employment', '6- Notification d\'embauche'),
        ('contract_established', '7- Contrat établi')
    ], string='Status', readonly=True, required=True, track_visibility='always', copy=False, default='applicant_selected', help="Set whether the recruitment process is open or closed for this job position.")
    
    
    job_name = fields.Char(String='Job title',related='job_id.name')

    
    type_name = fields.Char(string='Titre du poste',related='type_id.name')
    job_description = fields.Text(string='Description', related='job_id.poste_description')
    
    age = fields.Char(String='Age')
    number_of_years_of_experience = fields.Integer(string='Nombre d’année d’expérience') 
    
    psi_note_hr = fields.Integer(string="Note RH")
    psi_note_candidate = fields.Integer(string="Note Candidature")
    
    psi_average_note = fields.Integer(string="Moyenne")
    
    correspondance = fields.Selection([
        ('oui', 'Oui'),
        ('non', 'Non'),
        ('disqualifie', 'Disqualifié')
    ], string='Correspondance', required=True)  
       
    @api.model
    def create(self, vals):
        res = super(Applicant, self).create(vals)
        res['psi_average_note'] = ((res['psi_note_hr'] + res['psi_note_candidate']) / 2)
        return res
    
    @api.multi
    def write(self, vals):
        if vals.has_key('psi_note_hr') and vals.has_key('psi_note_candidate') : 
            vals['psi_average_note'] = ((vals['psi_note_hr'] + vals['psi_note_candidate']) / 2) 
        res = super(Applicant, self).write(vals)       
        return res
    
    def action_contract_established(self) :
        self.create_employee_from_applicant()
        self.write({ 'state': 'contract_established'})
        
    
   