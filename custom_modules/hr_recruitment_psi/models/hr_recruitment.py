# -*- coding: utf-8 -*-

from datetime import date, datetime
from datetime import timedelta
from operator import truediv

from dateutil.relativedelta import relativedelta

from odoo import fields, models, api
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


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
    
    def _default_stage_id(self):
        return self.env.ref('hr_recruitment_psi.applicant_selected').id
    
    attachment_file_ids = fields.Many2one('ir.attachment',string='Attachments')
    devise_proposed = fields.Many2one('res.currency',string='Devise')
    devise_extra = fields.Many2one('res.currency',string='Devise')
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
        ('honorary_proposal', '5- Proposition d\'honoraire'),
        ('benefits', '5- Indemnités'), 
        ('notification_of_employment', '6- Notification d\'embauche'),
         ('internship_contract', u'7- Contrat de stage à faire'),
        ('contract_established', u'7- Contrat à faire'),
         ('contract_established_consultant', u'7- Contrat à faire'),
         ('refused', '8- Refusé')
    ], string='Status', readonly=True, required=True, track_visibility='onchange', copy=False, default='applicant_selected', help="Set whether the recruitment process is open or closed for this job position.")
     

   
    job_name = fields.Char(String='Job title',related='job_id.name')
    
    type_name = fields.Char(string='Titre du poste',related='type_id.name')
    job_description = fields.Text(string='Description', related='job_id.poste_description')
    application_deadline_date = fields.Date(string=u"Délai de candidature", related="job_id.application_deadline_date")
    
    age = fields.Integer(compute="_calcul_age", String='Age')
    sexe = fields.Selection([
        ('masculin', 'Masculin'),
        ('feminin', u'Féminin')
     ], string='Sexe') 
    experiences = fields.Text(String='Expériences', size=250)
    number_of_years_of_experience = fields.Integer(string=u'Nombre d’années d’expérience') 
    birthday = fields.Date('Date de naissance')
    
    #Note ShortList
    psi_note_hr = fields.Selection([
        (1, '1'),
         (2, '2'),
          (3, '3'),
           (4, '4')
        ], string="Note RH")
    psi_note_candidate = fields.Selection([
        (1, '1'),
         (2, '2'),
          (3, '3'),
           (4, '4')
        ], string="Note Demandeur")
    psi_average_note = fields.Float(string="Moyenne Short List", readonly=True)
    
    #Note test
    psi_allowance = fields.Float(string='Indemnité de stage', digits=(16, 2),help="Basic Salary of the employee")
    psi_note_test_rh = fields.Integer(string="Note Test RH")
    psi_note_test_candidate = fields.Integer(string="Note Test Demandeur")
    psi_average_note_test = fields.Float(string="Moyenne Test", readonly=True)
    
    #Note Entretien
    psi_note_interview = fields.Float(string="Note Entretien")
    
    psi_total_note = fields.Float(compute="_calcul_total_note", string="Total des notes", readonly=True)
    
    correspondance_profil = fields.Selection([
        ('oui', 'Oui'),
        ('non', 'Non'),
        ('disqualifie', u'Disqualifié')
    ], string='Correspondance au profil')
       
    psi_salary_type = fields.Selection([
        ('net', 'Net'),
        ('brut', 'Brut')
    ], string='Type de salaire')
    
    psi_salary_negotiable = fields.Selection([
        ('negotiable', 'Négociable'),
        ('not_negotiable', 'Non négociable')
    ], string='Salaire Négociable')
    
    psi_maiden_name = fields.Char(string="Nom de jeune fille s'il y a lieu")
    
    country_id = fields.Many2one('res.country', string='Nationalité (Pays)')
    
    marital = fields.Selection([
        ('single', u'Célibataire'),
        ('married', u'Marié(e)'),
        ('separated', u'Séparé(e)'),
        ('widower', 'Veuf(ve)'),
        ('divorced', u'Divorcé(e)')
    ], string='Situation de famille')
    
    number_of_dependent_children = fields.Integer(string="Nombre d'enfant à charge (moins de 21 ans)")
    
    parents_employed_in_psi = fields.Boolean(string='Avez-vous des parents employés au sein de PSI Madagascar ?')
    
    parent_information_employees = fields.Many2many('hr.recruitement.parent.information', 'hr_recruitement_parent_information_id', string=u'Dans l\'affirmatif, donnez les renseignements suivants')
     
    already_answered_application = fields.Boolean(string="Avez-vous déjà répondu à un appel à candidature de PSI ?")
    
    description_already_answered_application = fields.One2many('hr.recruitment.already.answered.applicant', 'hr_recruitment_already_answered_applicant_id',"Dans l'affirmatif, à quel moment ? Pour quel poste et à quelle période ?")
    
    linguistic_knowledge = fields.One2many('hr.recruitment.linguistic.knowledge', 'psi_applicant_id',string="Connaissance linguistique")
    
    book_publish = fields.Text(string="Indiquez les ouvrages importants que vous avez publiés (thèses, essai, etc...)")
    
    university_studies = fields.One2many('hr.recruitment.university.study','psi_applicant_university_id',string='')
    university_studies_degree = fields.Char(related="university_studies.degree")
    
    secondary_studies = fields.One2many('hr.recruitment.university.study','psi_applicant_secondary_id',string='')
    
    current_employer_report = fields.Boolean(string='Accepteriez-vous que nous mettions en rapport avec votre employeur actuel ?')
    
    professional_references = fields.One2many('hr.recruitment.professional.reference', 'psi_applicant_id', string='')
     
    bridger_insight = fields.Boolean(string="")
    
    affirmative_bridger_insight = fields.Text(string=u"Dans l'affirmative, faites un résumé du (des) cas")
    
    previous_functions = fields.One2many('hr.recruitment.previous.functions','psi_applicant_id', string='')
    
    b_liste_restreinte = fields.Boolean(string='Dans la liste restreinte', default=False)
    
    date_verification_bridger_insight = fields.Date(string="date verification bridger insight")
   
    def action_briger_insight(self):
        self.write({'state':'bridger_insight','date_verification_bridger_insight': fields.Date().today()})
   
   
    @api.multi
    def create_employee_from_applicant(self):
        """ Create an hr.employee from the hr.applicants """
        employee = False
        for applicant in self:
            address_id = contact_name = False
            if applicant.partner_id:
                address_id = applicant.partner_id.address_get(['contact'])['contact']
                contact_name = applicant.partner_id.name_get()[0][1]
            if applicant.job_id and (applicant.partner_name or contact_name):
                applicant.job_id.write({'no_of_hired_employee': applicant.job_id.no_of_hired_employee + 1})
                vals = {'name': applicant.partner_name or contact_name,
                                                'psi_bridger_insight' : [(0, 0,{'date':applicant.date_verification_bridger_insight,'result':'oui'})],
                                                'children' : applicant.number_of_dependent_children,
                                                'country_id' : applicant.country_id.id,
                                                'birthday': applicant.birthday,
                                                'sexe': applicant.sexe,
                                               'job_id': applicant.job_id.id,
                                               'marital':applicant.marital,
                                               'address_home_id': address_id,
                                               'department_id': applicant.department_id.id or False,
                                               'address_id': applicant.company_id and applicant.company_id.partner_id and applicant.company_id.partner_id.id or False,
                                               'work_email': applicant.email_from,
                                               'work_phone': applicant.department_id and applicant.department_id.company_id and applicant.department_id.company_id.phone or False}
                employee = self.env['hr.employee'].create(vals)
                applicant.write({'emp_id': employee.id})
                print "Employee ID : ",employee.id
                date_start = applicant.job_id.psi_date_start
                date_start_trial = datetime.strptime(date_start,"%Y-%m-%d")
                date_start_trial_time = datetime(
                                                     year=date_start_trial.year, 
                                                     month=date_start_trial.month,
                                                     day=date_start_trial.day,
                       )
                
                month_to_notif = date_start_trial_time + relativedelta(months=applicant.job_id.psi_category.test_duration)
                    
                vals_contract = {'name': applicant.partner_name or contact_name,
                                                'psi_contract_type' : applicant.job_id.psi_contract_type,
                                                'employee_id': employee.id,
                                               'job_id': applicant.job_id.id,
                                               'date_start': applicant.job_id.psi_date_start,
                                               'trial_date_start':applicant.job_id.psi_date_start,
                                               'trial_date_end': month_to_notif,
                                               'wage': applicant.psi_allowance if applicant.recrutement_type == 'stagiaire' else applicant.salary_proposed,
                                               'department_id': applicant.department_id.id or False}
                print "vals_contract : ",vals_contract
                contract = self.env['hr.contract'].create(vals_contract)
                applicant.job_id.message_post(
                    body=_('New Employee %s Hired') % applicant.partner_name if applicant.partner_name else applicant.name,
                    subtype="hr_recruitment.mt_job_applicant_hired")
                employee._broadcast_welcome()
            else:
                raise UserError(_('You must define an Applied Job and a Contact Name for this applicant.'))

        employee_action = self.env.ref('hr.open_view_employee_list')
        dict_act_window = employee_action.read([])[0]
        if employee:
            dict_act_window['res_id'] = employee.id
        dict_act_window['view_mode'] = 'form,tree'
        return dict_act_window
    
    @api.model
    def _calcul_total_note(self):
        for record in self:
            record.psi_total_note = record.psi_average_note_test + record.psi_average_note + record.psi_note_interview
    
    @api.model
    def create(self, vals):
        res = super(Applicant, self).create(vals)
        res['psi_average_note'] = ((res['psi_note_hr'] + res['psi_note_candidate']) / 2)
        return res
    
    @api.multi
    def write(self, vals):
        data = self.browse(self.id)
        # calcul note short list
        vals['psi_note_hr'] = vals['psi_note_hr'] if vals.has_key('psi_note_hr') else data.psi_note_hr
        vals['psi_note_candidate'] = vals['psi_note_candidate'] if vals.has_key('psi_note_candidate') else data.psi_note_candidate
        vals['psi_average_note'] = truediv((vals['psi_note_hr'] + vals['psi_note_candidate']), 2)
        
        # calcul note test
        vals['psi_note_test_rh'] = vals['psi_note_test_rh'] if vals.has_key('psi_note_test_rh') else data.psi_note_test_rh
        vals['psi_note_test_candidate'] = vals['psi_note_test_candidate'] if vals.has_key('psi_note_test_candidate') else data.psi_note_test_candidate
        vals['psi_average_note_test'] = truediv((vals['psi_note_test_rh'] + vals['psi_note_test_candidate']), 2)
        
        vals['psi_note_interview'] = vals['psi_note_interview'] if vals.has_key('psi_note_interview') else data.psi_note_interview
        
        res = super(Applicant, self).write(vals)       
        return res
    
    def action_contract_established(self) :
        self.create_employee_from_applicant()
        self.write({ 'state': 'contract_established'})
    
    def action_internship_contract(self):
        self.create_employee_from_applicant()
        self.write({ 'state': 'internship_contract'})
    
    @api.multi
    def mail_refuse_applicant(self):
        if self.id != False :
            self.write({'state':'applicant_selected'})
            template = self.env.ref('hr_recruitment_psi.custom_template_refus')
            msg_id = self.env['mail.template'].browse(template.id).send_mail(self.id, force_send=True)
    
    def action_notification_of_employment(self):
        '''
        This function opens a window to compose an email
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('hr_recruitment_psi', 'email_template_notification_employment')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict()
        ctx.update({
            'default_model': 'hr.applicant',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
        })
        self.write({'state':'notification_of_employment'})
    @api.multi
    def button_notification_of_employment(self):
        '''
        This function opens a window to compose an email
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('hr_recruitment_psi', 'email_template_notification_employment')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict()
        ctx.update({
            'default_model': 'hr.applicant',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
        })
        self.write({'state':'notification_of_employment'})
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }
    
    @api.multi
    def set_to_liste_restreinte(self, val):
        for obj in self:
            obj.b_liste_restreinte = val
            
    @api.depends('birthday')
    def _calcul_age(self):
        for record in self:
            if record.birthday:
                record.age = datetime.today().year - datetime.strptime(record.birthday, "%Y-%m-%d").year
   

class ParentInformationEmployed(models.Model):
      _name = 'hr.recruitement.parent.information'
      
      name                      = fields.Char(string='NOM ET PRENOM')
      degree_of_relationship    = fields.Selection([
        ('enfant', 'Enfant'),
        ('famille', 'Famille'),
        ('conjoint', 'Conjoint')
       ], string='DEGRE DE PARENTE')
      post_office_title         = fields.Char(string="POSTE/TITRE/BUREAU")
      
      hr_recruitement_parent_information_id = fields.Many2one("hr.applicant")
      
class AlreadyAnsweredApplicant(models.Model):
     _name = 'hr.recruitment.already.answered.applicant'
     
     name           = fields.Char(string='POSTE')
     period         = fields.Char(string='PERIODE')
     
     hr_recruitment_already_answered_applicant_id = fields.Many2one("hr.applicant")
     
class LinguisticKnowledge(models.Model):
    _name = 'hr.recruitment.linguistic.knowledge'
    
    name       = fields.Selection([
       
        ('malagasy', 'Malagasy'),
        ('french', 'Français'),
        ('english', 'Anglais')
       ], string='CONNAISSANCE LINGUISTIQUE')
    written     = fields.Selection([
         ('langue_maternelle', 'Langue maternelle'),                            
        ('basic', 'Basique'),
        ('intermediate', 'Intermédiaire'),
        ('good', 'Bon'),
        ('excellent', 'Excellent'),
        ('Current', 'Courant')
       ], string='Ecrit')
    spoken      = fields.Selection([
                                     ('langue_maternelle', 'Langue maternelle'),
        ('basic', 'Basique'),
        ('intermediate', 'Intermédiaire'),
        ('good', 'Bon'),
        ('excellent', 'Excellent'),
        ('Current', 'Courant')
       ], string=u'Parlé')
    listen      = fields.Selection([
        ('langue_maternelle', 'Langue maternelle'),
        ('basic', 'Basique'),
        ('intermediate', 'Intermédiaire'),
        ('good', 'Bon'),
        ('excellent', 'Excellent'),
        ('Current', 'Courant')
       ], string='Ecoute')
    
    psi_applicant_id = fields.Many2one("hr.applicant")
    
class UniversityStudy(models.Model):
    _name = "hr.recruitment.university.study"
    
    name            = fields.Char(string="Nom de l'établissement")
    city            = fields.Char(string='Ville')
    country_id      = fields.Many2one('res.country', string=u'Nationalité (Pays)')
    from_date       = fields.Date(string=u"Début")
    end_date        = fields.Date(string="Fin")
    degree          = fields.Char(string=u"Diplômes/certificats obtenus")
    study_domain    = fields.Char(string="Principal domaine d'étude") 
    
    psi_applicant_secondary_id = fields.Many2one("hr.applicant")
    psi_applicant_university_id = fields.Many2one("hr.applicant")
   
class ProfessionalReference(models.Model):
    _name = "hr.recruitment.professional.reference"
    
    name            = fields.Char(string="Nom et prenom", required=True)
    function_title  = fields.Char(string="Titre et fonction", required=True)
    company         = fields.Char(string="Sociétés", required=True)
    mobile_phone    = fields.Char('Mobile', required=True)
    work_email      = fields.Char('Email', required=True)
    
    psi_applicant_id = fields.Many2one("hr.applicant")


   
class PreviousFunctions(models.Model):
    _name = "hr.recruitment.previous.functions"
    
    begin_date              = fields.Date()
    end_date                = fields.Date()
    last_basic_salary       = fields.Integer(string=u"Dérnier salaire de base")
    title_function          = fields.Char(string="Titre et fonction", required=True)
    employer                = fields.Char(string="Employeur", required=True)
    type_of_activity        = fields.Char(string=u"Type d'activité")
    address                 = fields.Char(string="Adresse", required=True)
    name_of_supervisor      = fields.Char(string=u"Nom du supérieur hiérarchique")
    number_of_supervised    = fields.Char(string=u"Nombre de supervisé")
    reason_for_leaving      = fields.Char(string=u"Motif de votre départ")
    mobile_phone            = fields.Char('Mobile', required=True)
    work_email              = fields.Char('Email')
    description             = fields.Text(string=u"Brève Déscriptions Des Tâches et Résponsabilités")
    
    psi_applicant_id = fields.Many2one("hr.applicant")
