# -*- coding: utf-8 -*-

from datetime import timedelta
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _

class hr_contract(models.Model):
    _inherit = 'hr.contract'
    
    place_of_work   = fields.Char(string='Lieu d\'affectaction') #lieu d'affectation
#    contract_id     = 0
    state_of_work   = fields.Selection([
        ('cdd', 'CDD'),
        ('cdi', 'CDI')
     ], string='Statut', track_visibility='onchange')
    
    @api.model
    def create(self, vals):  
        contract = super(hr_contract, self).create(vals)
        self._update_cron_rh_1()  
        return contract
    
    @api.multi
    def write(self, vals):
        contract = super(hr_contract, self).write(vals)
        self._update_cron_rh_1()  
        return contract

    def _update_cron_rh_1(self):
        """ Activate the cron First Email RH + Employee.
        """
        employee = self.employee_id
        cron = self.env.ref('hr_contract_psi.ir_cron_send_email_rh_1', raise_if_not_found=False)
        return cron and cron.toggle(model=self._name, domain=[('name', '!=', '')])
    
    #(R7.) Rappel - enregistrement du profil du collaborateur / complétude
    @api.one
    @api.constrains('name')
    def _send_first_email_rh(self, automatic=False):
        if len(self.employee_id._get_not_checked_files()) > 0:
            template0 = self.env.ref('hr_contract_psi.custom_template_rappel_hr_missing_pieces')
            self.env['mail.template'].browse(template0.id).send_mail(self.id)
            template1 = self.env.ref('hr_contract_psi.custom_template_rappel_collab_missing_pieces')
            self.env['mail.template'].browse(template1.id).send_mail(self.id)
        if automatic:
            self._cr.commit()
     
    @api.multi    
    @api.one
    @api.constrains('name')
    def _send_email_trial_date_end(self, automatic=False):
        for record in self:
            if record.trial_date_start:
                date_start = record.trial_date_start
                date_start_trial = datetime.strptime(date_start,"%Y-%m-%d")
                date_start_trial_time = datetime(
                    year=date_start_trial.year, 
                    month=date_start_trial.month,
                    day=date_start_trial.day,
                )
                # Verification selection
                if record.job_id.name == 'Chief Executive Officer':
                    month_to_notif = date_start_trial_time + relativedelta(months=5)  
                    if month_to_notif.date() == datetime.today().date():
                         template = self.env.ref('hr_contract_psi.custom_template_trial_date_end')
                         self.env['mail.template'].browse(template.id).send_mail(self.id)
                elif record.job_id.name == 'Consultant':
                    month_to_notif = date_start_trial_time + relativedelta(months=3)  
                    if month_to_notif.date() == datetime.today().date():
                         template = self.env.ref('hr_contract_psi.custom_template_trial_date_end')
                         self.env['mail.template'].browse(template.id).send_mail(self.id)
                elif record.job_id.name == 'Human Resources Manager':
                    month_to_notif = date_start_trial_time + relativedelta(months=2)  
                    if month_to_notif.date() == datetime.today().date():
                         template = self.env.ref('hr_contract_psi.custom_template_trial_date_end')
                         self.env['mail.template'].browse(template.id).send_mail(self.id)
        if automatic:
            self._cr.commit()

    def send_email_collaborator(self):
        print "The id contract is : ",self.contract_id
        template = self.env.ref('hr_contract_psi.custom_template_id')
        self.env['mail.template'].browse(template.id).send_mail(self.id)

    @api.one
    @api.constrains('state_of_work')
    def _check_state_of_work(self):
        for record in self:
            self.contract_id = record.id
       
        cron = self.env['ir.cron'].browse(9)
        cron.write({'active':True})
        cron.active = True
        cron.sudo(user=1)._callback(cron.model, cron.function, cron.args, cron.id)        
        cron.write({'active':False})
        
    def send_email(self):
        sender = 'xxxxx@gmail.com'
        receivers = 'arandriamoravelo@ingenosya.mg'
        
        message = "Bonjour, Veuillez contacter PSI s'il vous plait."
        
        smtpObj = smtplib.SMTP('smtp.gmail.com', 587)
        smtpObj.ehlo()
        smtpObj.starttls()
        smtpObj.ehlo()
        smtpObj.login('xxxxx@gmail.com', password='xxxx')
        smtpObj.sendmail(sender, receivers, message)         
        print "Successfully sent email"
        
class Employee(models.Model):
    _inherit = "hr.employee"

    personal_information        = fields.Boolean(default=False, string="Fiche de renseignements personnels")
    id_photos                   = fields.Boolean(default=False, string="Photos d'identité")
    certificate_residence       = fields.Boolean(default=False, string="Certificat de résidence")
    marriage_certificate        = fields.Boolean(default=False, string="Acte de mariage ou copie de livret de famille")
    cin                         = fields.Boolean(default=False, string="Copie CIN")
    work_certificate            = fields.Boolean(default=False, string="Copies Certificats de travail")
    qualifications              = fields.Boolean(default=False, string="Copies Diplômes ")
    criminal_records            = fields.Boolean(default=False, string="Casier judiciaires")
    card_cnaps                  = fields.Boolean(default=False, string="Copie Cartes CNAPS ")
    birth_certificate_children  = fields.Boolean(default=False, string="Acte de naissances des enfants ")
    ethics_course_certificate   = fields.Boolean(default=False, string="Certificat du cours d'éthique")
    attachment_number           = fields.Integer(compute='_get_attachment_number', string="Number of Attachments")
    attachment_ids              = fields.One2many('ir.attachment', 'res_id', domain=[('res_model', '=', 'hr.employee')], string='Attachments', track_visibility='always')
    
    sanctions_data = fields.One2many('hr.contract.sanction.data', 'sanction_type_id', string='', track_visibility='always')
    
    
    @api.model
    def create(self, vals):
        employee = super(Employee, self).create(vals)
        self._update_cron_collab_1()    
        self._update_cron_collab_2()    
        return employee
    
    @api.multi
    def write(self, vals):
        employee = super(Employee, self).write(vals)
        self._update_cron_collab_1()
        self._update_cron_collab_2()
        return employee

    def _update_cron_collab_1(self):
        """ Activate the cron Premier Email Employee.
        """
        cron = self.env.ref('hr_contract_psi.ir_cron_send_email_collab_1', raise_if_not_found=False)
        return cron and cron.toggle(model=self._name, domain=[('name', '!=', '')])
    
    def _update_cron_collab_2(self):
        """ Activate the cron Second Email Employee.
        """
        cron = self.env.ref('hr_contract_psi.ir_cron_send_email_collab_2', raise_if_not_found=False)
        return cron
    
    @api.one
    @api.constrains('personal_information')   
    def _get_not_checked_files(self):      
        list_not_checked = []
        for record in self:     
            dict ={
                       'personal_information'       : record.personal_information,
                       'id_photos'                  : record.id_photos,
                       'certificate_residence'      : record.certificate_residence,
                       'marriage_certificate'       : record.marriage_certificate,
                       'cin'                        : record.cin,
                       'work_certificate'           : record.work_certificate,
                       'qualifications'             : record.qualifications,
                       'criminal_records'           : record.criminal_records,
                       'card_cnaps'                 : record.card_cnaps,
                       'birth_certificate_children' : record.birth_certificate_children,
                       'ethics_course_certificate'  : record.ethics_course_certificate 
                   }
            list(dict.keys())
            list(dict.values())
            for key, value in dict.items() :
                if value == False:
                    list_not_checked.append(key)    
        return list_not_checked

    @api.multi
    def _get_attachment_number(self):
        read_group_res = self.env['ir.attachment'].read_group(
            [('res_model', '=', 'hr.employee'), ('res_id', 'in', self.ids)],
            ['res_id'], ['res_id'])
        attach_data = dict((res['res_id'], res['res_id_count']) for res in read_group_res)
        for record in self:
            record.attachment_number = attach_data.get(record.id, 0)
 
    @api.multi 
    def action_get_attachment_tree_view(self):    
        attachment_action = self.env.ref('base.action_attachment')
        action = attachment_action.read()[0]
        action['context'] = {'default_res_model': self._name, 'default_res_id': self.ids[0]}
        action['domain'] = str(['&', ('res_model', '=', self._name), ('res_id', 'in', self.ids)])
        action['search_view_id'] = (self.env.ref('hr_contract.ir_attachment_view_search_inherit_hr_employee').id, )
        return action
    
    #(R6.) First Rappel au cours d'éthique  
    @api.one
    @api.constrains('personal_information')  
    def _send_first_email_collaborator(self, automatic=False):
        list_not_checked = self._get_not_checked_files()
        if len(list_not_checked) > 0:
            template = self.env.ref('hr_contract_psi.custom_template_rappel_collab_1')
            self.env['mail.template'].browse(template.id).send_mail(self.id)
        if automatic:
            self._cr.commit()

    #(R8.) Second Rappel au cours d'éthique
    def _send_second_email_collaborator(self, automatic=False):
        #si certificat de complétude du cours NON ENREGISTRER > mail au collab apres 3 semaines d'enregistrement
        template = self.env.ref('hr_contract_psi.custom_template_rappel_collab_2')
        self.env['mail.template'].browse(template.id).send_mail(self.id)
        if automatic:
            self._cr.commit()

class ContractTypeSanction(models.Model):

    _name = 'hr.contract.type.sanction'
    _description = 'Liste des sanctions'

    name = fields.Char(string='Nom de la sanction')
    
class SanctionData(models.Model):

    _name = 'hr.contract.sanction.data'

    name = fields.Char(string='Nom de la sanction')
    sanction_date = fields.Date(string='Date de la sanction')
    sanction_type_id = fields.Many2one('hr.contract.type.sanction', string='Sanction')
    sanction_objet = fields.Char(string='Objet')
    sanction_date_effacement = fields.Date(string='Date d\'effacement')
    sanction_commentaire = fields.Text(string='Commentaires')
        