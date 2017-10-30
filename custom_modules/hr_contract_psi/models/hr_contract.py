# -*- coding: utf-8 -*-

from datetime import timedelta
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _

class hr_contract(models.Model):
    _inherit = 'hr.contract'
    
    place_of_work   = fields.Char(string='Lieu d\'affectaction') #lieu d'affectation
    
    #rupture
    date_rupture = fields.Date(string='Date rupture de contrat')

    motif_rupture = fields.Selection([
                                      ('end_deadline_without_renewal',"Arrivée de l'échéance sans reconduction"),
                                      ('conventional_break',"Rupture conventionnelle"),
                                      ('resignation',"Lettre de démission"),
                                      ('dismissal',"Licenciement"),
                                      ('death',"Décès"),
                                      ('retreat',"Retraite")
                                      ], string="Motif de rupture de contrat", track_visibility="onchange")
    
    work_years = fields.Integer(compute="_calculate_work_years", string=u'Année de travail')
    
    result_evaluation = fields.Selection([
                                          ('ok','OK'),
                                          ('ko','KO')
                                          ], string="Résultat de l'évaluation", track_visibility="onchange")
    response_evaluation = fields.Selection([
                                            ('accept','Accepter'),
                                            ('decline','Refuser')
                                            ])    
    scan_version_file = fields.Binary(string=u'Attacher le version scanner')

    psi_contract_type = fields.Selection([
        ('cdd', 'CDD'),
        ('cdi', 'CDI'),
        ('convention_stage','Convention de stage')
    ], string='Type de contrat', help="Type de contrat", track_visibility='onchange')

    @api.multi
    def action_result_evaluation_send_ok(self):
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('hr_contract', 'email_template_for_result_evaluation_ok')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict()
        ctx.update({
            'default_model': 'hr.contract',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True
        })
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
    def action_result_evaluation_send_ko(self):
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('hr_contract', 'email_template_for_result_evaluation_ko')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict()
        ctx.update({
            'default_model': 'hr.contract',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True
        })
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
    def _send_email_birthday_date_tracking(self):
        employee_obj = self.env['hr.contract']
        employees = employee_obj.search([])
        
        for employee in employees : 
           
            date_birthday = employee.date_start
            if date_birthday != False :
                datetime_now =  datetime.today()
                date_now = datetime(
                    year=datetime_now.year, 
                    month=datetime_now.month,
                    day=datetime_now.day,
                )
                datetime_birthday = datetime.strptime(date_birthday,"%Y-%m-%d")
                date_birthday_time = datetime(
                    year=datetime_now.year, 
                    month=datetime_birthday.month,
                    day=datetime_birthday.day,
                )
                monday1 = (date_now - timedelta(days=date_now.weekday()))
                monday2 = (date_birthday_time - timedelta(days=date_birthday_time.weekday()))

                weeks = (monday2 - monday1).days / 7
               
                if weeks == 1 :
                    
                    template_collaborator = self.env.ref('hr_contract_psi.template_collaborator_id')
                    self.env['mail.template'].browse(template_collaborator.id).send_mail(employee.id)
                    template_rh = self.env.ref('hr_contract_psi.template_rh_id')
                    self.env['mail.template'].browse(template_rh.id).send_mail(employee.id)
                    
    employment_termination = fields.Selection([
                                             ('end_deadline_without_renewal',"Arrivée de l'échéance sans reconduction"),
                                             ('conventional_break',"Rupture conventionnelle"),
                                             ('resignation',"Lettre de démission"),
                                             ('dismissal',"Licenciement"),
                                             ('death',"Décès"),
                                             ('retreat',"Retraite")
                                             ], string="Séparation événement", track_visibility="onchange")

    
    def _send_email_birthday_date_tracking(self):
        employee_obj = self.env['hr.contract']
        employees = employee_obj.search([])
        
        for employee in employees : 
           
            date_birthday = employee.date_start
            if date_birthday != False :
                datetime_now =  datetime.today()
                date_now = datetime(
                    year=datetime_now.year, 
                    month=datetime_now.month,
                    day=datetime_now.day,
                )
                datetime_birthday = datetime.strptime(date_birthday,"%Y-%m-%d")
                date_birthday_time = datetime(
                    year=datetime_now.year, 
                    month=datetime_birthday.month,
                    day=datetime_birthday.day,
                )
                monday1 = (date_now - timedelta(days=date_now.weekday()))
                monday2 = (date_birthday_time - timedelta(days=date_birthday_time.weekday()))

                weeks = (monday2 - monday1).days / 7
               
                if weeks == 1 :
                    
                    template_collaborator = self.env.ref('hr_contract_psi.template_collaborator_id')
                    self.env['mail.template'].browse(template_collaborator.id).send_mail(employee.id)
                    template_rh = self.env.ref('hr_contract_psi.template_rh_id')
                    self.env['mail.template'].browse(template_rh.id).send_mail(employee.id)
    
    def _send_email_birthday_date_tracking(self):
        employee_obj = self.env['hr.contract']
        employees = employee_obj.search([])
        
        for employee in employees : 
           
            date_birthday = employee.date_start
            if date_birthday != False :
                datetime_now =  datetime.today()
                date_now = datetime(
                    year=datetime_now.year, 
                    month=datetime_now.month,
                    day=datetime_now.day,
                )
                datetime_birthday = datetime.strptime(date_birthday,"%Y-%m-%d")
                date_birthday_time = datetime(
                    year=datetime_now.year, 
                    month=datetime_birthday.month,
                    day=datetime_birthday.day,
                )
                monday1 = (date_now - timedelta(days=date_now.weekday()))
                monday2 = (date_birthday_time - timedelta(days=date_birthday_time.weekday()))

                weeks = (monday2 - monday1).days / 7
               
                if weeks == 1 :
                    
                    template_collaborator = self.env.ref('hr_contract_psi.template_collaborator_id')
                    self.env['mail.template'].browse(template_collaborator.id).send_mail(employee.id)
                    template_rh = self.env.ref('hr_contract_psi.template_rh_id')
                    self.env['mail.template'].browse(template_rh.id).send_mail(employee.id)
    
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
    
    @api.depends('date_start')
    def _calculate_work_years(self):
        for record in self:
            if record.date_start:
                record.work_years = datetime.today().year - datetime.strptime(record.date_start, "%Y-%m-%d").year

    def set_employee_inactif(self):
        """ Set employee inactif
        """
        print "SET EMPLOYEE INACTIF"
        for record in self:
            contract_obj = self.env['hr.contract']
            employee_obj = self.env['hr.employee']
            employee = record.employee_id
            #employee readonly
            contract = contract_obj.browse([record.id])
            contract.update({
                             'state':'close'
            })
            employee.update({
                             'state':'close'
                             })
           
    def action_renew_trial_accept(self):
#        reprise processus
        print "reprise processus"
        for record in self:
            contract_obj = self.env['hr.contract']
            contract = contract_obj.browse([record.id])
            contract.update({
                             'response_evaluation':'accept'
            })
            
    def action_renew_trial_decline(self):
        print "Séparation"
        self.set_employee_inactif()    
    
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
                if record.job_id.psi_professional_category == 'directeur':
                    month_to_notif = date_start_trial_time + relativedelta(months=5)
                    if month_to_notif.date() == datetime.today().date():
                        template = self.env.ref('hr_contract_psi.custom_template_trial_date_end')
                        self.env['mail.template'].browse(template.id).send_mail(self.id)
                elif record.job_id.psi_professional_category == 'coordinateur':
                    month_to_notif = date_start_trial_time + relativedelta(months=3)  
                    if month_to_notif.date() == datetime.today().date():
                        template = self.env.ref('hr_contract_psi.custom_template_trial_date_end')
                        self.env['mail.template'].browse(template.id).send_mail(self.id)
                else:
                    month_to_notif = date_start_trial_time + relativedelta(months=2)  
                    if month_to_notif.date() == datetime.today().date():
                        template = self.env.ref('hr_contract_psi.custom_template_trial_date_end')
                        self.env['mail.template'].browse(template.id).send_mail(self.id)
        if automatic:
            self._cr.commit()

    @api.one
    @api.constrains('name')
    def _send_email_end_contract(self, automatic=False):
        print "Send email to mentor - fin contrat"
        for record in self:
            if record.date_end:
                date_end = record.date_end
                date_end_contract = datetime.strptime(date_end,"%Y-%m-%d")
                date_end_contract_time = datetime(
                    year=date_end_contract.year, 
                    month=date_end_contract.month,
                    day=date_end_contract.day,
                )
                month_to_notif = date_end_contract_time - relativedelta(months=1)  
                if month_to_notif.date() == datetime.today().date():
                    template = self.env.ref('hr_contract_psi.custom_template_end_contract')
                    self.env['mail.template'].browse(template.id).send_mail(self.id)
        if automatic:
            self._cr.commit()

    @api.one
    @api.constrains('name')
    def _close_collabo_end_contract(self, automatic=False):
        for record in self:
            if record.date_end:
                date_end = record.date_end
                date_end_contract = datetime.strptime(date_end,"%Y-%m-%d")
                date_end_contract_time = datetime(
                    year=date_end_contract.year, 
                    month=date_end_contract.month,
                    day=date_end_contract.day,
                )
                month_to_notif = date_end_contract_time - relativedelta(months=1)  
                if month_to_notif.date() == datetime.today().date():
                    record.set_employee_inactif()
            elif record.date_rupture:
                date_rupture = record.date_rupture
                date_rupture_contract = datetime.strptime(date_rupture,"%Y-%m-%d")
                date_rupture_contract_time = datetime(
                    year=date_rupture_contract.year, 
                    month=date_rupture_contract.month,
                    day=date_rupture_contract.day,
                )
                if date_rupture_contract_time.date() == datetime.today().date():
                    record.set_employee_inactif()                  
        if automatic:
            self._cr.commit()
            
    def send_email_collaborator(self):
        print "The id contract is : ",self.contract_id
        template = self.env.ref('hr_contract_psi.custom_template_id')
        self.env['mail.template'].browse(template.id).send_mail(self.id)
