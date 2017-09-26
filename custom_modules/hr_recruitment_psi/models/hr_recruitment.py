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
    
    def _default_stage_id(self):
        return self.env.ref('hr_recruitment_psi.draft2').id
    
    recrutement_type_id = fields.Many2one('hr.recruitment.type',related='job_id.recrutement_type_id',string='Type de recrutement')
    recrutement_type = fields.Selection(related='job_id.recrutement_type_id.recrutement_type',string='Type de recrutement selection')
    
    stage_id = fields.Many2one('hr.recruitment.stage', 'Stage', track_visibility='onchange',
                               domain="['|',('recrutement_type_ids', '=', False),('recrutement_type_ids', '=', recrutement_type_id)]",
                               copy=False, index=True,
                               group_expand='_read_group_stage_ids',
                               default=_default_stage_id)
    #champ relie au champ stage_id pour utilisation dans les domaines des views
    stage = fields.Char(related='stage_id.stage',string='Stage')
    
    
    job_name = fields.Char(String='Job title',related='job_id.name')
    type_name = fields.Char(String='Titre du poste',related='type_id.name')
    formation_requise = fields.Text(String='Formation Requise', related='job_id.formation_requise')
    domaine_name = fields.Char(String='Domaine', related='job_id.domaine_id.name')
    job_description = fields.Text(String='Description', related='job_id.description')
    
    age = fields.Char(String='Age')
    number_of_years_of_experience = fields.Integer(string='Nombre d’année d’expérience') 
    correspondance = fields.Text(string='Correspondance', required=True)
    
    def action_cv_received(self):
        self.write({'stage_id': self.env.ref('hr_recruitment_psi.cv_received').id})
    def action_cv_saved(self):
        self.write({'stage_id': self.env.ref('hr_recruitment_psi.cv_saved').id})
    def action_can_do_test(self):
        self.write({'stage_id': self.env.ref('hr_recruitment_psi.can_do_test').id})
    def action_first_interview(self):
        self.write({'stage_id': self.env.ref('hr_recruitment_psi.first_interview').id})
    def action_in_deliberation(self):
        self.write({'stage_id': self.env.ref('hr_recruitment_psi.in_deliberation').id})
    def action_second_interview(self):
        self.write({'stage_id': self.env.ref('hr_recruitment_psi.second_interview').id})
    def action_bi(self):
        self.write({'stage_id': self.env.ref('hr_recruitment_psi.bi').id})
    def action_verification_ref(self):
        self.write({'stage_id': self.env.ref('hr_recruitment_psi.verification_ref').id})
    def action_wage_proposal(self):
        if not self.salary_expected or not self.salary_proposed:
            raise ValidationError('Erreur! Le salaire demandé et/ou le salaire proposé sont nuls.')
        self.write({'stage_id': self.env.ref('hr_recruitment_psi.wage_proposal').id})
    def action_salary_validated(self):
        self.write({'stage_id': self.env.ref('hr_recruitment_psi.salary_validated').id})
    def action_candidat_notified(self):
        self.write({'stage_id': self.env.ref('hr_recruitment_psi.candidat_notified').id})
    def action_final_decision(self):
        self.write({'stage_id': self.env.ref('hr_recruitment_psi.final_decision').id})
    def action_contract(self):
        self.write({'stage_id': self.env.ref('hr_recruitment_psi.contract').id})
    def action_contract_signed(self):
        self.create_employee_from_applicant()
        self.write({'stage_id': self.env.ref('hr_recruitment_psi.contract_signed').id})
    def action_drh_validation(self):
        self.write({'stage_id': self.env.ref('hr_recruitment_psi.drh_validation').id})
    def action_drh_allocation_stage(self):
        self.write({'stage_id': self.env.ref('hr_recruitment_psi.drh_allocation_stage').id})    
        
        
        