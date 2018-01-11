# -*- coding: utf-8 -*-

import calendar
from datetime import date, datetime
from datetime import timedelta

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, Warning


class hr_contract(models.Model):
    _inherit = 'hr.contract'
    
    place_of_work   = fields.Selection(related="employee_id.work_location", string='Lieu de travail', track_visibility='onchange', store=True) #lieu d'affectation
    date_start = fields.Date('Start Date', required=True, default=fields.Date.today, track_visibility='onchange')
    date_end = fields.Date('End Date', track_visibility='onchange',default="9999-12-31")
    #job_id = fields.Many2one('hr.job', string='Job Title', track_visibility='onchange')
    #department_id = fields.Many2one('hr.department', string="Department", track_visibility='onchange')
    preavis = fields.Selection([('preste',u'Presté'),('paye',u'Payé')],string='préavis')
    indeminite_de_preavis = fields.Float(string="Indeminité de préavis")
    date_demission = fields.Date(string=u'Date de démission')
    #rupture
    date_rupture = fields.Date(string='Date rupture de contrat')
    devise = fields.Many2one('res.currency',string='Devise')
    motif_rupture = fields.Selection([
                                      ('end_deadline_without_renewal',u"Arrivée de l'échéance sans reconduction"),
                                      ('conventional_break',"Rupture conventionnelle"),
                                      ('resignation',u"Réception d'une lettre de démission"),
                                      ('dismissal',"Licenciement"),
                                      ('death',u"Décès"),
                                      ('retreat',"Retraite")
                                      ], string="Motif de rupture de contrat", track_visibility="onchange")
    
    work_years = fields.Integer(compute="_calculate_work_years", string=u'Année de travail (Ancienneté)')

    
    result_evaluation = fields.Selection([
                                          ('ok','OK'),
                                          ('ko','KO')
                                          ], string="Résultat de l'évaluation", track_visibility="onchange")
    response_evaluation = fields.Selection([
                                            ('accept','Accepter'),
                                            ('decline','Refuser')
                                            ])    
    scan_version_file = fields.Binary(string=u'Attacher le version scanner')

    psi_contract_type = fields.Selection(related="employee_id.psi_contract_type", string="Type de contrat",store=True,track_visibility='onchange')
    
    name_employee = fields.Char(related='employee_id.name')
    job_name = fields.Char(related='employee_id.job_id.name')
    psi_certificat = fields.One2many('psi.contract.historical','contract_id',domain=[('index', '=', 'changement_de_grille_salariale')], string='Certificat')
    state_mail = fields.Selection([
        ('draft', 'RFQ'),
        ('sent', 'RFQ Sent')], default='draft')
    
    anniversary = fields.Date(compute="_get_anniversary")
    
    indetermine = fields.Char(default='Indéterminé', readonly=True)

    debauchage_cnaps = fields.Boolean(string="Débauchage CNAPS", default=False)
    debauchage_ostie = fields.Boolean(string="Débauchage OSTIE", default=False)
    debauchage_assurance = fields.Boolean(string="Débauchage Assurance Santé", default=False)
    
    job_id = fields.Many2one('hr.job', related='employee_id.job_id',string='Job ID', required=True)
    user_id = fields.Many2one('res.users',related='job_id.user_id',string='Users ID')
    psi_professional_category = fields.Many2one(related='job_id.psi_category',string='Catégorie professionnelle')
    psi_category = fields.Selection(related='psi_professional_category.psi_professional_category',string='Catégorie professionnelle')
    
    historical_count = fields.Integer(compute='_historical_count', string='# of Historical')
    department_id = fields.Many2one(related='job_id.department_id', string=u"Département", readonly=True)
    working_hours = fields.Selection(related='employee_id.work_location', string='Horaire de travail')

    def action_report_certificat(self):
        date = fields.Date().today()
        psi_contract_historicals = self.env['psi.contract.historical'].search([('contract_id', '=', self.id)])
        psi_contract_historicals[len(psi_contract_historicals)-1].write({'fin': date})
        return {
               'type': 'ir.actions.report.xml',
               'report_name': 'hr_contract_psi.report_certificat_travail'
           }

    @api.onchange('job_id')
    def _onchange_by_job_id(self):
        self.department_id = self.job_id.department_id
        self.psi_category_details = self.job_id.psi_category
        self.psi_contract_type = self.job_id.psi_contract_type

    @api.onchange('employee_id')
    def _onchange_by_employee_id(self):
        self.working_hours = self.employee_id.work_location

    @api.depends('date_start')
    def _get_anniversary(self):
        
        for rec in self:
            datetime_date_start = datetime.strptime(rec.date_start,"%Y-%m-%d")
            today = datetime.today()
            rec.anniversary = datetime(
                     year=today.year, 
                     month=datetime_date_start.month,
                     day=datetime_date_start.day,
                    )
        
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
                
                if weeks == 2 :
                    print employee.employee_id.name
                    template_collaborator = self.env.ref('hr_contract_psi.template_collaborator_id')
                    self.env['mail.template'].browse(template_collaborator.id).send_mail(employee.id, force_send=True)
                    template_rh = self.env.ref('hr_contract_psi.template_rh_id')
                    self.env['mail.template'].browse(template_rh.id).send_mail(employee.id, force_send=True)
                    
    psi_echelon = fields.Selection([('echelon_1','ECHELON 1'),('echelon_2','ECHELON 2'),('echelon_3','ECHELON 3'),
                                    ('echelon_4','ECHELON 4'),('echelon_5','ECHELON 5'),('echelon_6','ECHELON 6'),
                                    ('echelon_7','ECHELON 7'),('echelon_8','ECHELON 8'),('echelon_9','ECHELON 9'),
                                    ('echelon_10','ECHELON 10'),('echelon_11','ECHELON 11'),('echelon_12','ECHELON 12'),
                                    ('echelon_13','ECHELON 13'),('echelon_14','ECHELON 14'),('echelon_15','ECHELON 15'),
                                    ('echelon_16','ECHELON 16'),('echelon_17','ECHELON 17'),('echelon_18','ECHELON 18'),
                                    ('echelon_19','ECHELON 19'),('echelon_20','ECHELON 20'),('echelon_hc','ECHELON HC')
                                    ],default="echelon_1",string="Echelon",track_visibility="onchange" )

    job_id = fields.Many2one('hr.job', related='employee_id.job_id',string='Job ID', required=True)
    
    psi_category_details = fields.Many2one(related='job_id.psi_category',string='Titre de la Catégorie',store=True)
    psi_category = fields.Selection(related='psi_category_details.psi_professional_category',string='Titre de la Catégorie',store=True)
    psi_cat_cat = fields.Char(related='psi_category_details.psi_cat', string='Catégorie')
    psi_sub_category            = fields.Selection([
                                        ('1','1'),
                                        ('2','2'),
                                        ('3','3'),
                                        ('4','4')
                                ],default="1", string="Sous-catégorie")
    matricule = fields.Char(string='Matricule', related="employee_id.matricule")
    historical_count = fields.Integer(compute='_historical_count', string='# of Historical')
   
    def action_send_email_desactivate_flottes(self):
        template = self.env.ref('hr_contract_psi.template_desactivate_flottes_id')
        self.env['mail.template'].browse(template.id).send_mail(self.id,force_send=True) 
    
    def action_send_email_desactivate_account(self):
        template = self.env.ref('hr_contract_psi.template_desactivate_account_id')
        self.env['mail.template'].browse(template.id).send_mail(self.id,force_send=True)
       

    @api.onchange("psi_sub_category","psi_echelon")
    def onchange_psi_sub_psi_echelon(self):
        if self.psi_sub_category is False:
            self.psi_sub_category="1"
        if self.psi_echelon is False:
            self.psi_echelon="echelon_1"

    @api.model
    def create(self, vals):  
        contract = super(hr_contract, self).create(vals)
        date = fields.Date().today()
        ancien = ''
        nouveau = contract.job_id.name
        debut = fields.Date().today()
        index = "changement_de_grille_salariale"
        historical = "Changement de Grille salariale"
        vals_historical = {'date':date,'historical' : historical,'debut':debut,'index':index,'nouveau':nouveau,'ancien':ancien, 'contract_id':contract.id}
        self.env['psi.contract.historical'].create(vals_historical) 
        return contract
    
    @api.multi
    def write(self, vals):
          #traitement de l'augmentation des salaires
        if vals.has_key('wage') :
            data = self.browse(self.id) 
            date = fields.Date().today()
            ancien = data.wage if data.wage != '' else ''
            nouveau = vals['wage']
            debut = fields.Date().today()
            psi_contract_historicals = self.env['psi.contract.historical'].search([('contract_id', '=', self.id)])
            date_changement_epsilon_last = False
            if ancien != '':
                historical_old_id = 0
                for historical_obj in psi_contract_historicals :
                    historical_old_id = historical_obj.id
                historical_env = self.env['psi.contract.historical']
                historical_obj = historical_env.browse(historical_old_id)
                historical_obj.write({'fin':debut})
            index = "augmentation_salaire"
            historical = "Augmentation générale des salaires "
            vals_historical = {'date':date,'historical' : historical,'debut':debut,'index':index,'nouveau':nouveau,'ancien':ancien, 'contract_id':self.id}
            self.env['psi.contract.historical'].create(vals_historical)
            
        if vals.has_key('psi_echelon') :
            sanction_env = self.env['hr.contract.sanction.data'] 
            sanctions = sanction_env.search([('employee_id', '=', self.employee_id.id)])
            today = datetime.today()
            sanction_type = []
            data = self.browse(self.id) 
            for sanction_obj in sanctions :
                if sanction_obj.sanction_date != False:
                    s_date = datetime.strptime(sanction_obj.sanction_date,"%Y-%m-%d")
                    if today.year == s_date.year : 
                        sanction_type.append(sanction_obj.sanction_type_id.name)
            if len(sanction_type) > 0:
                str_sanct = ''
                for sanction_str in sanction_type :
                    str_sanct += "- "+sanction_str +"\n"
                str = u"L'employé "+data.employee_id.name+u" a eu des sanctions ces 12 derniers mois précédents: \n"+str_sanct+u"\nDonc l'employé ne peut pas changer d'échelon."
                raise ValidationError(str.encode('utf-8'))
                 
            #traitement de historique de changement d'échelon
            
            date = fields.Date().today()
            ancien = data.psi_echelon if data.psi_echelon != '' else ''
            nouveau = vals['psi_echelon']
            debut = fields.Date().today()
            psi_contract_historicals = self.env['psi.contract.historical'].search([('contract_id', '=', self.id)])
            date_changement_epsilon_last = False
            if ancien != '':
                historical_old_id = 0
                for historical_obj in psi_contract_historicals :
                    historical_old_id = historical_obj.id
                historical_env = self.env['psi.contract.historical']
                historical_obj = historical_env.browse(historical_old_id)
                historical_obj.write({'fin':debut})
            index = "changement_echelon"
            historical = "Changement d'echelon"
            vals_historical = {'date':date,'historical' : historical,'debut':debut,'index':index,'nouveau':nouveau,'ancien':ancien, 'contract_id':self.id}
            self.env['psi.contract.historical'].create(vals_historical)
            wage_grids = self.env['hr.wage.grid.details'].search([('psi_professional_category', '=', self.psi_category),('psi_sub_category', '=', self.psi_sub_category)])
            echelon = 0
            for wage_grid in wage_grids :
                if vals['psi_echelon'] != 'echelon_hc' :
                    echelon = wage_grid._get_echelon(vals['psi_echelon'])
            vals['wage'] = echelon if echelon != 0 else data.wage
            
         
         #traitement de changement de statut    
        if vals.has_key('psi_contract_type') :
            data = self.browse(self.id) 
            date = fields.Date().today()
            ancien = data.psi_contract_type if data.psi_contract_type != '' else ''
            nouveau = vals['psi_contract_type']
            debut = fields.Date().today()
            psi_contract_historicals = self.env['psi.contract.historical'].search([('contract_id', '=', self.id)])
            date_changement_epsilon_last = False
            if ancien != '':
                historical_old_id = 0
                for historical_obj in psi_contract_historicals :
                    historical_old_id = historical_obj.id
                historical_env = self.env['psi.contract.historical']
                historical_obj = historical_env.browse(historical_old_id)
                historical_obj.write({'fin':debut})
            index = "changement_de_statut"
            historical = "Changement de statut"
            vals_historical = {'date':date,'historical' : historical,'debut':debut,'index':index,'nouveau':nouveau,'ancien':ancien, 'contract_id':self.id}
            self.env['psi.contract.historical'].create(vals_historical)
            
     
        
        #traitement de l'affectation
        if vals.has_key('place_of_work') :
            data = self.browse(self.id) 
            date = fields.Date().today()
            ancien = data.place_of_work if data.place_of_work != '' else ''
            nouveau = vals['place_of_work']
            debut = fields.Date().today()
            psi_contract_historicals = self.env['psi.contract.historical'].search([('contract_id', '=', self.id)])
            date_changement_epsilon_last = False
            if ancien != '':
                historical_old_id = 0
                for historical_obj in psi_contract_historicals :
                    historical_old_id = historical_obj.id
                historical_env = self.env['psi.contract.historical']
                historical_obj = historical_env.browse(historical_old_id)
                historical_obj.write({'fin':debut})
            index = "affectation"
            historical = "Affectation"
            vals_historical = {'date':date,'historical' : historical,'debut':debut,'index':index,'nouveau':nouveau,'ancien':ancien, 'contract_id':self.id}
            self.env['psi.contract.historical'].create(vals_historical)
              
       
       #traitement de changement de département de rattachement
        if vals.has_key('department_id') :
            data = self.browse(self.id) 
            date = fields.Date().today()
            departement_id = self.env['hr.department'].browse(vals['department_id'])
            ancien = data.department_id.name if data.department_id.name != '' else ''
            nouveau = departement_id.name
            debut = fields.Date().today()
            psi_contract_historicals = self.env['psi.contract.historical'].search([('contract_id', '=', self.id)])
            date_changement_epsilon_last = False
            if ancien != '':
                historical_old_id = 0
                for historical_obj in psi_contract_historicals :
                    historical_old_id = historical_obj.id
                historical_env = self.env['psi.contract.historical']
                historical_obj = historical_env.browse(historical_old_id)
                historical_obj.write({'fin':debut})
            index = "changement_de_departement"
            historical = "Changement de departement"
            vals_historical = {'date':date,'historical' : historical,'debut':debut,'index':index,'nouveau':nouveau,'ancien':ancien, 'contract_id':self.id}
            self.env['psi.contract.historical'].create(vals_historical)
            
         #traitement de changement de grille salariale
        if vals.has_key('job_id') :
            data = self.browse(self.id) 
            date = fields.Date().today()
            job_id = self.env['hr.job'].browse(vals['job_id'])
            ancien = data.job_id.name if data.job_id.name != '' else ''
            nouveau = job_id.name
            debut = fields.Date().today()
            psi_contract_historicals = self.env['psi.contract.historical'].search([('contract_id', '=', self.id)])
            date_changement_epsilon_last = False
            if ancien != '':
                historical_old_id = 0
                for historical_obj in psi_contract_historicals :
                    historical_old_id = historical_obj.id
                historical_env = self.env['psi.contract.historical']
                historical_obj = historical_env.browse(historical_old_id)
                historical_obj.write({'fin':debut})
            index = "changement_de_grille_salariale"
            historical = "Changement de Grille salariale"
            vals_historical = {'date':date,'historical' : historical,'debut':debut,'index':index,'nouveau':nouveau,'ancien':ancien, 'contract_id':self.id}
            self.env['psi.contract.historical'].create(vals_historical)    
            
        contract_obj = super(hr_contract, self).write(vals)
        contract = self.browse(self.id)
        if vals.has_key('wage') :
           template1 = self.env.ref('hr_contract_psi.template_augmentation_salaire_id')
           self.env['mail.template'].browse(template1.id).send_mail(contract.id,force_send=True) 
        if vals.has_key('psi_echelon') :
            template0 = self.env.ref('hr_contract_psi.template_avancement_echelon_id')
            self.env['mail.template'].browse(template0.id).send_mail(contract.id,force_send=True)
        if vals.has_key('psi_contract_type') :
            template2 = self.env.ref('hr_contract_psi.template_changement_statut_id')
            self.env['mail.template'].browse(template2.id).send_mail(contract.id,force_send=True)
        if vals.has_key('place_of_work') : 
             template3 = self.env.ref('hr_contract_psi.template_affectation_id')
             self.env['mail.template'].browse(template3.id).send_mail(contract.id, force_send=True) 
        if vals.has_key('department_id') :
             template4 = self.env.ref('hr_contract_psi.template_changement_de_departement_id')
             self.env['mail.template'].browse(template4.id).send_mail(contract.id,force_send=True)
        if vals.has_key('job_id') :
             template5 = self.env.ref('hr_contract_psi.template_changement_de_grille_salariale_id')
             self.env['mail.template'].browse(template5.id).send_mail(contract.id,force_send=True)
        return contract_obj
    
    @api.depends('date_start')
    def _calculate_work_years(self):
        for record in self:
            if record.date_start:
                record.work_years = datetime.today().year - datetime.strptime(record.date_start, "%Y-%m-%d").year
    
    def generate_certificat_travail(self):
        print "GENERATE CERTIFICAT TRAVAIL"
    
    def set_employee_inactif(self):
        """ Set employee inactif
        """
        print "SET EMPLOYEE INACTIF"
        for record in self:
            contract_obj = self.env['hr.contract']
            employee_obj = self.env['hr.employee']
            employee = record.employee_id
            
            if record.motif_rupture == 'resignation':
                template = self.env.ref('hr_contract_psi.template_separation_demission_id')
                self.env['mail.template'].browse(template.id).send_mail(self.id,force_send=True)
                print "EMAIL SENT"
            
            #employee readonly
            contract = contract_obj.browse([record.id])
            contract.update({
                             'state':'close',
                             'state_mail':'sent'
            })
            employee.update({
                             'state':'close'
                             })
           
    def action_renew_trial_accept(self):
#        reprise processus
        print "reprise processus"
        for record in self:
            
            if self.job_id.psi_category.test_duration == 0:
                raise Warning('La période d\'essai pour la catégorie "{}" n\'est pas encore définie.'.format(self.job_id.psi_category.psi_professional_category.upper()))
            
            contract_obj = self.env['hr.contract']
            contract = contract_obj.browse([record.id])
            
            fin = datetime.strptime(contract.trial_date_end,"%Y-%m-%d")
            if fin.weekday() == calendar.FRIDAY:
                fin = fin + timedelta(days=3)
            
            new_date_start = fin
            new_date_end = new_date_start + relativedelta(months=contract.job_id.psi_category.test_duration)
            
            contract.update({
                             'response_evaluation' : 'accept',
                             'trial_date_start': new_date_start,
                             'trial_date_end' : new_date_end,
            })
            
    def action_renew_trial_decline(self):
        print "Séparation"
        self.set_employee_inactif()    
    
    #(R7.) Rappel - enregistrement du profil du collaborateur / complétude
    def _send_first_email_rh(self, automatic=False):
        contracts = self.env['hr.contract'].search([])
        print "Verification premier email RH"
        for contract in contracts:
            date_create = contract.create_date
            date_create_contract = datetime.strptime(date_create,"%Y-%m-%d %H:%M:%S")
            date_create_contract_time = datetime(
                    year=date_create_contract.year, 
                    month=date_create_contract.month,
                    day=date_create_contract.day,
                )
            date_to_notif = date_create_contract_time - relativedelta(days=0)  #days=15
            if date_to_notif.date() == datetime.today().date():
                files_not_checked = contract.employee_id._get_not_checked_files()
                for list_not_check in files_not_checked:
                    if len(list_not_check) > 0:
                        template0 = self.env.ref('hr_contract_psi.custom_template_rappel_hr_missing_pieces')
                        self.env['mail.template'].browse(template0.id).send_mail(contract.id, force_send=True)
                        template1 = self.env.ref('hr_contract_psi.custom_template_rappel_collab_missing_pieces')
                        self.env['mail.template'].browse(template1.id).send_mail(contract.id, force_send=True)
        if automatic:
            self._cr.commit()

    def _send_email_trial_date_end(self, automatic=False):
        contracts = self.env['hr.contract'].search([])
        print "Verification un mois apres fin essai"
        for record in contracts:
            if record.trial_date_start:
                date_start = record.trial_date_start
                date_start_trial = datetime.strptime(date_start,"%Y-%m-%d")
                date_start_trial_time = datetime(
                    year=date_start_trial.year,
                    month=date_start_trial.month,
                    day=date_start_trial.day,
                )
                # Verification selection                
                month_to_notif = date_start_trial_time + relativedelta(months=record.job_id.psi_category.test_duration-1)
                if month_to_notif.date() == datetime.today().date():
                    template = self.env.ref('hr_contract_psi.custom_template_trial_date_end')
                    self.env['mail.template'].browse(template.id).send_mail(self.id, force_send=True)
        if automatic:
            self._cr.commit()

    def _send_email_end_contract(self, automatic=False):
        contracts = self.env['hr.contract'].search([])
        for record in contracts:
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
                    print record.employee_id.name
                    template = self.env.ref('hr_contract_psi.template_end_contract_id')
                    self.env['mail.template'].browse(template.id).send_mail(record.id,force_send=True)
        if automatic:
            self._cr.commit()

    def _close_collabo_end_contract(self, automatic=False):
        contracts = self.env['hr.contract'].search([])
        for record in contracts:
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
        
    @api.one
    def _historical_count(self):
        historicals = self.env['psi.contract.historical'].search([('contract_id', '=', self.id)])
        self.historical_count = len(historicals)  

class ContractHistorical(models.Model):
     _name = 'psi.contract.historical'
     contract_id = fields.Many2one('hr.contract',string="Contrat")
     date = fields.Date();
     index = fields.Char("index")
     historical = fields.Char("historique");
     debut = fields.Char("Debut")
     fin = fields.Char("Fin")
     ancien  = fields.Char('Ancien')
     nouveau = fields.Char('Nouveau')
     
     contract_id = fields.Many2one('hr.contract')
     
class HrDureePreavis(models.Model):
    
    _name = 'hr.duree.preavis'
    
    preavis_id = fields.Integer()
    name = fields.Char(string=u"Ancienneté")
    preavis = fields.Integer(string=u"Préavis (en jour(s))")
    categorie = fields.Char(string=u"Cat")
    sous_cat = fields.Char(string=u"Sous-catégorie")
    sous_cat_cat = fields.Char(compute='_concat_sous_cat_cat', store=True, string=u"Catégorie")
    
    @api.depends('categorie','sous_cat')
    def _concat_sous_cat_cat(self):
        for record in self:
            record.sous_cat_cat = record.sous_cat + record.categorie

    