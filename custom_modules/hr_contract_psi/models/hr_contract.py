# -*- coding: utf-8 -*-

from datetime import timedelta
from odoo import api, fields, models, _

class hr_contract(models.Model):
    _inherit = 'hr.contract'
    
    place_of_work   = fields.Char(string='Lieu d\'affectaction') #lieu d'affectation
#    contract_id     = 0
    state_of_work   = fields.Selection([
        ('cdd', 'CDD'),
        ('cdi', 'CDI')
     ], string='Statut')
    
    @api.model
    def create(self, vals):
        print "CREATE in CONTRACT -----------------------------------------------------------------------------"   
        contract = super(hr_contract, self).create(vals)
        self._update_cron_rh_1()  
        return contract
    
    @api.multi
    def write(self, vals):
        contract = super(hr_contract, self).write(vals)
        self._update_cron_rh_1()  
        return contract

    @api.multi
    def unlink(self):
        contract = super(hr_contract, self).unlink()
        self._update_cron_rh_1()  
        return contract
    
    def _update_cron_rh_1(self):
        """ Activate the cron First Email RH + Employee.
        """
        print "ACTIVE CRON notification FIRST_RH -----------------------------------------------------------------------------"
        employee = self.employee_id
        pj_not_checked = employee._get_not_checked_files()
        cron = self.env.ref('hr_contract_psi.ir_cron_send_email_rh_1', raise_if_not_found=False)
        return cron and cron.toggle(model=self._name, domain=[('name', '!=', '')])
    
    #(R7.) Rappel - enregistrement du profil du collaborateur / complétude
    def _send_first_email_rh(self):
        print "First rappel RH"
        #si dossier PAS complet > mail à la RH et collab + pieces manquantes
        #date_start < contrat
        print "test "+str(len(self.employee_id._get_not_checked_files()))
        if len(self.employee_id._get_not_checked_files()) > 0:
            template = self.env.ref('hr_contract_psi.custom_template_rappel_rh_collab')
            self.env['mail.template'].browse(template.id).send_mail(self.id)
    
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
    attachment_ids              = fields.One2many('ir.attachment', 'res_id', domain=[('res_model', '=', 'hr.employee')], string='Attachments')
    
    @api.model
    def create(self, vals):
        print "CREATE in EMPLOYEE -----------------------------------------------------------------------------"   
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

    @api.multi
    def unlink(self):
        employee = super(Employee, self).unlink()
        self._update_cron_collab_1() 
        self._update_cron_collab_2()  
        return employee
    
    def _update_cron_collab_1(self):
        """ Activate the cron Premier Email Employee.
        """
        print "ACTIVE CRON notification PREMIER -----------------------------------------------------------------------------"
        cron = self.env.ref('hr_contract_psi.ir_cron_send_email_collab_1', raise_if_not_found=False)
        return cron and cron.toggle(model=self._name, domain=[('name', '!=', '')])
    
    def _update_cron_collab_2(self):
        """ Activate the cron Second Email Employee.
        """
        print "ACTIVE CRON notification SECOND -----------------------------------------------------------------------------"
        cron = self.env.ref('hr_contract_psi.ir_cron_send_email_collab_2', raise_if_not_found=False)
        return cron
    
    def _get_not_checked_files(self):
        list_not_checked = []
        dict ={
               'personal_information'       : self.personal_information,
               'id_photos'                  : self.id_photos,
               'certificate_residence'      : self.certificate_residence,
               'marriage_certificate'       : self.marriage_certificate,
               'cin'                        : self.cin,
               'work_certificate'           : self.work_certificate,
               'qualifications'             : self.qualifications,
               'criminal_records'           : self.criminal_records,
               'card_cnaps'                 : self.card_cnaps,
               'birth_certificate_children' : self.birth_certificate_children,
               'ethics_course_certificate'  : self.ethics_course_certificate  
               }
        list(dict.keys())
        list(dict.values())
        for key, value in dict.items() :
            if value == False:
                list_not_checked.append(key)    
        print "list_not_checked "+str(list_not_checked)
        return list_not_checked
#        pj_checked = []
#        pj_not_checked = []
#        if self.personal_information:
#            pj_checked.append(self.personal_information)
#        else : 
#            pj_not_checked.append(self.personal_information)
#        if self.id_photos:
#            pj_checked.append(self.id_photos)
#        else : 
#            pj_not_checked.append(self.id_photos)
#        if self.certificate_residence:
#            pj_checked.append(self.certificate_residence)
#        else : 
#            pj_not_checked.append(self.certificate_residence)
#        if self.marriage_certificate:
#            pj_checked.append(self.marriage_certificate)
#        else : 
#            pj_not_checked.append(self.marriage_certificate)
#        if self.cin:
#            pj_checked.append(self.cin)
#        else : 
#            pj_not_checked.append(self.cin)
#        if self.work_certificate:
#            pj_checked.append(self.work_certificate)
#        else : 
#            pj_not_checked.append(self.work_certificate)
#        if self.qualifications:
#            pj_checked.append(self.qualifications)
#        else : 
#            pj_not_checked.append(self.qualifications)
#        if self.criminal_records:
#            pj_checked.append(self.criminal_records)
#        else : 
#            pj_not_checked.append(self.criminal_records)
#        if self.card_cnaps:
#            pj_checked.append(self.card_cnaps)
#        else : 
#            pj_not_checked.append(self.card_cnaps)
#        if self.birth_certificate_children:
#            pj_checked.append(self.birth_certificate_children)
#        else : 
#            pj_not_checked.append(self.birth_certificate_children)
#        if self.ethics_course_certificate:
#            pj_checked.append(self.ethics_course_certificate)
#        else : 
#            pj_not_checked.append(self.ethics_course_certificate)
#        return pj_checked_dict

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
    
    #(R6.) First Rappel – cours d’éthique
    def _send_first_email_collaborator(self, automatic=False):
        print "First rappel collaborator -----------------------------------------------------------------------------"  
        print "Nb "+str(len(self._get_not_checked_files()))
        if len(self._get_not_checked_files()) > 0:
            template = self.env.ref('hr_contract_psi.custom_template_rappel_collab_1')
            self.env['mail.template'].browse(template.id).send_mail(self.id)
        if automatic:
            self._cr.commit()
            
    #(R8.) Second Rappel – cours d’éthique
    def _send_second_email_collaborator(self):
        print "Second rappel collaborator"
        #si certificat de complétude du cours NON ENREGISTRER > mail au collab apres 3 semaines d'enregistrement
        template = self.env.ref('hr_contract_psi.custom_template_rappel_collab_2')
        self.env['mail.template'].browse(template.id).send_mail(self.id)
    