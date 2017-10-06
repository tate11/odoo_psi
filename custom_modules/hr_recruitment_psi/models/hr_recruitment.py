# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError

class RecruitmentType(models.Model):
    _name = 'hr.recruitment.type'
    
    recrutement_type = fields.Selection([
        ('collaborateur', 'Recrutement d\'un collaborateur permanent'),
        ('consultant', 'Recrutement d\'un consultant'),
        ('stagiaire', 'Recrutement d\'un stagiaire'),
        ('collaborateur_externe', 'Recrutement avec Cabinet de recrutement')
    ], string='Type de recrutement')
    
    name = fields.Char(string='Nom')
    
class RecruitmentStage(models.Model):
    _inherit = "hr.recruitment.stage"
    
    stage = fields.Char("Stage", required=True)
    
    recrutement_type_ids = fields.Many2many('hr.recruitment.type', 'recrutement_stage_type_rel', 'stage_id', 'type_id', string='Stages')
    
class Applicant(models.Model):
    _inherit = "hr.applicant"
    _name = "hr.applicant"
    
    recrutement_type_id = fields.Many2one('hr.recruitment.type',related='job_id.recrutement_type_id',string='Type de recrutement', readonly=True)
    recrutement_type = fields.Selection(related='job_id.recrutement_type_id.recrutement_type',string='Type de recrutement selection')
    
    nature_recrutement_id = fields.Selection(related='job_id.nature_recrutement',string='Nature de recrutement')
    
    state = fields.Selection([
        ('applicant_selected', u'Candidatures selectionnées'),
        ('convoked_for_test', u'1- Convoqués pour les tests'),
        ('interview', '2- Entretiens'),
        ('professional_reference', u'3- Références proféssionnelles'),
        ('bridger_insight', '4- Bridger Insight'),
        ('psi_wage_proposal', '5- Proposition salariale'), 
        ('notification_of_employment', '6- Notification d\'embauche'),
        ('contract_established', u'7- Contrat établi')
    ], string='Status', readonly=True, required=True, track_visibility='onchange', copy=False, default='applicant_selected', help="Set whether the recruitment process is open or closed for this job position.")
    
    job_name = fields.Char(String='Job title',related='job_id.name')
    
    type_name = fields.Char(string='Titre du poste',related='type_id.name')
    job_description = fields.Text(string='Description', related='job_id.poste_description')
    
    age = fields.Char(String='Age')
    sex = fields.Selection([
        ('masculin', 'Masculin'),
        ('feminin', u'Féminin')
     ], string='Sexe', required=True) 
    experiences = fields.Text(String='Expériences', size=250)
    number_of_years_of_experience = fields.Integer(string=u'Nombre d’années d’expérience') 
    
    psi_note_hr = fields.Selection([
        ('1', '1'),
         ('2', '2'),
          ('3', '3'),
           ('4', '4')
        ], string="Note RH")
    
    psi_note_candidate = fields.Selection([
        ('1', '1'),
         ('2', '2'),
          ('3', '3'),
           ('4', '4')
        ], string="Note Candidat")
    
    psi_average_note = fields.Integer(string="Moyenne", readonly=True)
    
    correspondance = fields.Selection([
        ('oui', 'Oui'),
        ('non', 'Non'),
        ('disqualifie', u'Disqualifié')
    ], string='Correspondance', required=True)  
       
    psi_salary_type = fields.Selection([
        ('net', 'Net'),
        ('brut', 'Brut')
    ], string='Type de salaire')
    
    psi_salary_negotiable = fields.Selection([
        ('negotiable', 'Négociale'),
        ('not_negotiable', 'Non négociable')
    ], string='Salaire Négociable')
    
    psi_maiden_name = fields.Char(string="Nom de jeune fille s'il y a lieu")
    
    country_id = fields.Many2one('res.country', string='Nationality (Country)')
    
    marital = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married'),
        ('widower', 'Widower'),
        ('divorced', 'Divorced')
    ], string='Marital Status')
    
    number_of_dependent_children = fields.Integer(string="Nombre d'enfant à charge (moins de 21 ans)")
    
    parents_employed_in_psi = fields.Boolean(string='Avez-vous des parents employés au sein de PSI Madagascar ?')
    
    parent_information_employees = fields.One2many('hr.recruitement.parent.information', 'id', string=u'Dans l\'affirmatif, donnez les renseignements suivants')
    
    already_answered_application = fields.Boolean(string="Avez-vous déjà répondu à un appel à candidature de PSI ?")
    
    description_already_answered_application = fields.One2many('hr.already_answered_application', 'id',"Dans l'affirmatif, à quel moment ? Pour quel poste et à quelle période ?")
    
    linguistic_knowledge = fields.One2many('hr.recruitment.linguistic.knowledge', 'id',string="Connaissance linguistique")
    
    book_publish = fields.Text(string="Indiquez les ouvrages importants que vous avez publiés (thèses, essai, etc...)")
    
    university_studies = fields.One2many('hr.recruitment.university.study','id',string='')
    
    secondary_studies = fields.One2many('hr.recruitment.university.study','id',string='')
    
    current_employer_report = fields.Boolean(string='Accepteriez-vous que nous mettions en rapport avec votre employeur actuel ?')
    
    professional_references = fields.One2many('hr.recruitment.professional.reference','id',string='')
     
    bridger_insight = fields.Boolean(string="")
    
    affirmative_bridger_insight = fields.Text(string="Dans l'affirmative, faites un résumé du (des) cas")
    
    previous_functions = fields.One2many('hr.recruitment.previous.functions','id', string='')
    
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
       
    @api.multi
    def button_mail_refuse(self):
        #template = self.env.ref('hr_recruitment_psi.example_email_template')
        #self.env['mail.template'].browse(template.id).send_mail(self.id)
        self.write({'state':'applicant_selected'})
    
class ParentInformationEmployed(models.Model):
      _name = 'hr.recruitement.parent.employed.information'
      
      name                      = fields.Char(string='NOM ET PRENOM', required=True)
      degree_of_relationship    = fields.Selection([
        ('enfant', 'Enfant'),
        ('famille', 'Famille'),
        ('conjoint', 'Conjoint')
       ], string='DEGRE DE PARENTE')
      post_office_title         = fields.Char(string="POSTE/TITRE/BUREAU")
      
class AlreadyAnsweredApplicant(models.Model):
     _name = 'hr.recruitment.already.answered.applicant'
     
     name           = fields.Char(string='POSTE')
     period         = fields.Date(string='PERIODE')
     
class LinguisticKnowledge(models.Model):
    _name = 'hr.recruitment.linguistic.knowledge'
    
    name        = fields.Char(string="CONNAISSANCE LINGUISTIQUE")
    written     = fields.Selection([
        ('basic', 'Basique'),
        ('intermediate', 'Intermédiaire'),
        ('good', 'Bon'),
        ('excellent', 'Excellent'),
        ('Current', 'Courant')
       ], string='Ecrit')
    spoken      = fields.Selection([
        ('basic', 'Basique'),
        ('intermediate', 'Intermédiaire'),
        ('good', 'Bon'),
        ('excellent', 'Excellent'),
        ('Current', 'Courant')
       ], string='Ecrit')
    listen      = fields.Selection([
        ('basic', 'Basique'),
        ('intermediate', 'Intermédiaire'),
        ('good', 'Bon'),
        ('excellent', 'Excellent'),
        ('Current', 'Courant')
       ], string='Ecrit') 
    
class UniversityStudy(models.Model):
    _name = "hr.recruitment.university.study"
    
    name            = fields.Char(string="Nom de l'établissement")
    city            = fields.Char(string='Ville')
    country_id      = fields.Many2one('res.country', string='Nationality (Country)')
    from_date       = fields.Date(string="Debut")
    end_date        = fields.Date(string="Fin")
    degree          = fields.Char(string="Diplômes/certificats obtenus")
    study_domain    = fields.Char(string="Principal domaine d'étude") 
   
class ProfessionalReference(models.Model):
    _name = "hr.recruitment.professional.reference"
    
    name            = fields.Char(string="NOM ET PRENOM")
    function_title  = fields.Char(string="TITRE ET FONCTION")
    company         = fields.Char(string="SOCIETES")
    mobile_phone    = fields.Char('Work Mobile')
    work_email      = fields.Char('Work Email')
   
class PreviousFunctions(models.Model):
    _name = "hr.recruitment.previous.functions"
    
    begin_date              = fields.Date()
    end_date                = fields.Date()
    last_basic_salary       = fields.Float(string="Dernier salaire de base")
    title_function          = fields.Char(string="Titre et fonction")
    employer                = fields.Char(string="Employeur")
    type_of_activity        = fields.Char(string="Type d'activité")
    address                 = fields.Char(string="Adresse")
    name_of_supervisor      = fields.Char(string="Nom du supérieur hiérarchique")
    number_of_supervised    = fields.Char(string="Nombre de supervisé")
    reason_for_leaving      = fields.Char(string="Motif de votre départ")
    mobile_phone            = fields.Char('Work Mobile')
    work_email              = fields.Char('Work Email')
    description             = fields.Text(string="BREVE DESCRIPTIONS DES TACHES ET RESPONSABILITES")