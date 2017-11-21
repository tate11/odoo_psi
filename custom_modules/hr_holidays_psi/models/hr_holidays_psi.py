# -*- coding: utf-8 -*-

import calendar
import datetime
import logging
import math

import dateutil.parser
from dateutil.relativedelta import relativedelta
from werkzeug import url_encode

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, AccessError
from odoo.exceptions import Warning
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF
from odoo.tools import float_compare
from odoo.tools.translate import _
from openerp.tools import float_compare


#from datetime import  datetime, timedelta
HOURS_PER_DAY = 8

class hr_holidays_type_psi(models.Model):
    
    _inherit = "hr.holidays.status"
    
    type_permission = fields.Many2one('hr.holidays.type.permission', string="Type de permission")
    holidays_status_id_psi = fields.Integer(string=u"id type de congé psi")
    
class hr_holidays_type_permission(models.Model):
    
    _name = "hr.holidays.type.permission"
    _description = "Type de permission"
    
    name = fields.Char('Type de permission', required=True)
    number_of_day = fields.Float('Nombre de jours', required=True)
    
class hr_holidays_psi(models.Model):
    
    _inherit = "hr.holidays"
    
    psi_category_id = fields.Many2one('hr.psi.category.details',u'Catégorie professionnelle')
    
    color_name_holiday_status = fields.Selection(related='holiday_status_id.color_name', string=u'Couleur du type du congé')
    id_psi_holidays_status = fields.Integer(related='holiday_status_id.holidays_status_id_psi')
    holiday_type_permission = fields.Many2one(related='holiday_status_id.type_permission', string='Type de permission')
    
    attachment_number           = fields.Integer(compute='_get_attachment_number', string="Number of Attachments")
    attachment_ids              = fields.One2many('ir.attachment', 'res_id', domain=[('res_model', '=', 'hr.holidays')], string='Attachments', track_visibility='always')
    
    job_id = fields.Many2one(related='employee_id.job_id', store=True)
    employee_type = fields.Selection(related='job_id.recrutement_type', store=True)
    
    all_employee = fields.Boolean(string="Tous les employés")
    
    state = fields.Selection([
        ('draft', 'To Submit'),
        ('cancel', 'Cancelled'),
        ('confirm', 'To Approve'),
        ('refuse', 'Refused'),
        ('validate1', u'Validation par Supérieur hiérarchique'),
        ('approbation','Approbation du chef de département de rattachement'),
        ('validate2', 'Validation par RH'),
        ('validate', 'Validation par DRHA')
        ], string='Status', readonly=True, track_visibility='onchange', copy=False, default='confirm',
            help="The status is set to 'To Submit', when a holiday request is created." +
            "\nThe status is 'To Approve', when holiday request is confirmed by user." +
            "\nThe status is 'Refused', when holiday request is refused by manager." +
            "\nThe status is 'Approved', when holiday request is approved by manager.")

     
    @api.constrains('number_of_days_temp')
    def _verif_leave_date(self):
        holidays = self.env["hr.holidays"].search([('employee_id','=',self.employee_id.name)])
#        holiday.holiday_status_id.max_leaves = 10
#        if count holiday.id_psi_holidays_status remaining_leaves > 10 > erreur
        for record in self:
            get_day_difference = record.number_of_days_temp
            type_permissions = self.env['hr.holidays.type.permission'].search([])            
            for permissions in type_permissions:
                if self.holiday_type_permission.id == permissions.id:
                    if get_day_difference > permissions.number_of_day:
                        raise Warning(_(u"Vous avez depassé le nombre de jours permi pour ce type de permission."))
            

    
    last_business_day = fields.Date(compute="_get_last_business_day", string="Dernier jour ouvrable du mois")

    def _get_last_business_day(self):
        date = datetime.datetime.now()
        day_last_month = self.get_last_month(date)
        lastBusDay = datetime.datetime.today()
        new_lastBusDay = lastBusDay.replace(day=int(day_last_month))
        if new_lastBusDay.weekday() == 5:
            new_lastBusDay = new_lastBusDay - datetime.timedelta(days=1)
        elif new_lastBusDay.weekday() == 6: 
            new_lastBusDay = new_lastBusDay - datetime.timedelta(days=2)
        for record in self:
            record.last_business_day = new_lastBusDay.date()
        
    def get_last_month(self,date):  
        result = calendar.monthrange(date.year,date.month)[1]
        return result
        
    @api.model
    def create(self, values):
        self._verif_leave_date()
        #got_droit = self.check_droit(values)
        got_droit = True
        if got_droit == False:
            raise ValidationError(u'Vous ne pouvez pas encore faire une demande de congé.')
        else:
            holidays = super(hr_holidays_psi, self).create(values)
            return holidays

          
    @api.multi
    def write(self, values):
        employee_id = values.get('employee_id', False)
        self._send_email_rappel_absences_to_assist_and_coord(False)
        self._verif_leave_date()
#         if self.env.user == self.employee_id.user_id:
#             raise AccessError(u'Vous ne pouvez plus modifier votre demande, veuillez contacter votre supérieur hiérarchique.')

#        if self.state == 'validate1' and self.env.user != self.employee_id.department_id.manager_id.user_id:
#            raise AccessError(u'Vous ne pouvez pas modifier cette demande de congé.')

        
        if not self._check_state_access_right(values):
            raise AccessError(_('You cannot set a leave request as \'%s\'. Contact a human resource manager.') % values.get('state'))
        result = super(hr_holidays_psi, self).write(values)
        self.add_follower(employee_id)
        return result

    def action_report_request_for_absences(self):
        return {
               'type': 'ir.actions.report.xml',
               'report_name': 'hr_holidays_psi.report_request_for_absences'
           }
      
    @api.multi
    def action_approve(self):
        # if double_validation: this method is the first approval approval
        # if not double_validation: this method calls action_validate() below
        if not self.env.user.has_group('hr_holidays.group_hr_holidays_user'):
            raise UserError(_('Only an HR Officer or Manager can approve leave requests.'))

        manager = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        for holiday in self:
            print "holiday.state : ",holiday.state
            if holiday.state != 'confirm':
                raise UserError(_('Leave request must be confirmed ("To Approve") in order to approve it.'))
            return holiday.write({'state': 'validate1', 'manager_id': manager.id if manager else False})
    
    @api.multi
    def action_approve_candidate1(self):
        # if double_validation: this method is the first approval approval
        # if not double_validation: this method calls action_validate() below
        if not self.env.user.has_group('hr_holidays.group_hr_holidays_user'):
            raise UserError(_('Only an HR Officer or Manager can approve leave requests.'))

        manager = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        for holiday in self:
            if holiday.state != 'validate1':
                raise UserError(_('Leave request must be confirmed ("To Approve") in order to approve it.'))
        return holiday.write({'state': 'approbation', 'manager_id': manager.id if manager else False})
    
    @api.multi
    def action_approbation_departement(self):
        # if double_validation: this method is the first approval approval
        # if not double_validation: this method calls action_validate() below
        if not self.env.user.has_group('hr_holidays.group_hr_holidays_user'):
            raise UserError(_('Only an HR Officer or Manager can approve leave requests.'))

        manager = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        for holiday in self:
            if holiday.state != 'approbation':
                raise UserError(_('Leave request must be confirmed ("To Approve") in order to approve it.'))
        return holiday.write({'state': 'validate2', 'manager_id': manager.id if manager else False})

    @api.multi
    def _get_attachment_number(self):
        read_group_res = self.env['ir.attachment'].read_group(
            [('res_model', '=', 'hr.holidays'), ('res_id', 'in', self.ids)],
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
        action['search_view_id'] = (self.env.ref('hr_holidays_psi.ir_attachment_view_search_inherit_hr_holidays').id, )
        return action

    
    def check_droit(self, values):
        current_employee = self.env['hr.contract'].search([('employee_id', '=', values['employee_id'])])
        
        if values.has_key('date_from') and current_employee.date_start != False :
            if values['date_from'] != False :
                date_start = datetime.datetime.strptime(current_employee.date_start,"%Y-%m-%d")
                date_from = datetime.datetime.strptime(values['date_from'],"%Y-%m-%d %H:%M:%S")
                config = self.env['hr.holidays.configuration'].search([])[0]
                diff = (date_from.year - date_start.year) * 12 + date_from.month - date_start.month
                if diff <= config.droit_conge:
                    return False
        return True     
    
    @api.constrains('date_from')
    def _check_date_from(self):
       print "_check_date_from"
       
       for record in self :
           if record.date_from != False:
               date_from_time = datetime.datetime.strptime(record.date_from,"%Y-%m-%d %H:%M:%S")
               #date_from = date_from_time.date()
               date_now = datetime.datetime.strptime(fields.Date().today(),"%Y-%m-%d")

               between = date_from_time - date_now
               #between_month = date_now.month - date_from.month
               
               if between.days < 0: #(between_month == 1 and date_from.day >= 3) or between_month < 1:
                   raise ValidationError(u"La date de début du congé n'est pas valide.")
               
               holidays_status = self.env['hr.holidays.status'].search([('holidays_status_id_psi','=',4)])
               if record.holiday_status_id.id != holidays_status[0].id: # a part maladie
                   if between.days >= 0 and between.days < 3 :
                       raise ValidationError(u"Vous devez faire une demande de congés au moins 3 jours avant votre départ pour congé.")
     
    @api.constrains('date_from')
    def _check_date_from_conge_sans_solde(self):
       print "_check_date_from 2"
       for record in self :
           if record.date_from != False and record.holiday_status_id.holidays_status_id_psi == 3:
               config = self.env['hr.holidays.configuration'].search([])[0]
               
               #TODO a modifier
               if record.holiday_status_id == 10:
                   if record.number_of_days_temp > config.conges_sans_solde :
                      raise ValidationError(u"Votre demande de congés depasse la limite de congés sans soldes.")


    @api.multi
    def action_validate(self):
        print "action_validate"

        if not self.env.user.has_group('hr_holidays.group_hr_holidays_user'):
            raise UserError(_('Only an HR Officer or Manager can approve leave requests.'))

        manager = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        for holiday in self:
            if holiday.state not in ['confirm', 'validate1','validate2']:
                raise UserError(_('Leave request must be confirmed in order to approve it.'))
            if holiday.state == 'validate2' and not holiday.env.user.has_group('hr_holidays.group_hr_holidays_manager'):
                raise UserError(_('Only an HR Manager can apply the second approval on leave requests.'))

            holiday.write({'state': 'validate'})
            if holiday.double_validation:
                holiday.write({'manager_id2': manager.id})
            else:
                holiday.write({'manager_id': manager.id})
            if holiday.holiday_type == 'employee' and holiday.type == 'remove' and holiday.all_employee == False:
                meeting_values = {
                    'name': holiday.display_name,
                    'categ_ids': [(6, 0, [holiday.holiday_status_id.categ_id.id])] if holiday.holiday_status_id.categ_id else [],
                    'duration': holiday.number_of_days_temp * HOURS_PER_DAY,
                    'description': holiday.notes,
                    'user_id': holiday.user_id.id,
                    'start': holiday.date_from,
                    'stop': holiday.date_to,
                    'allday': False,
                    'state': 'open',            # bloquer cette date de réunion dans le calendrier
                    'privacy': 'confidential'
                }
                
                for holiday in self.filtered(lambda r: r.state == 'validate'):
                    print holiday.employee_id
                    if not holiday.employee_id:
                        continue        
                    if not holiday.employee_id.user_id:
                        raise ValidationError(_(
                            u'Vous ne pouvez pas valider une permission pour un employé sans utilisateur'))
                    print holiday.number_of_days,' holiday.number_of_days'
                    if holiday.number_of_days > 0:
                        continue
                    if not (holiday.date_from or holiday.date_to):
                        continue
        
                    employee = holiday.employee_id
                    print employee,' employee'
        
                    time_from = self.str_to_timezone(holiday.date_from)
                    time_to = self.str_to_timezone(holiday.date_to)
        
                    for timestamp in self.datespan(time_from, time_to):
                        company = employee.company_id
                        date = timestamp.date()
                        hours = company.hours_per_day
                        
                        self.create_leave_analytic_line(
                                holiday, employee, date, hours)
                 
                #Add the partner_id (if exist) as an attendee
                if holiday.user_id and holiday.user_id.partner_id :
                    meeting_values['partner_ids'] = [(4, holiday.user_id.partner_id.id)]
                
                meeting = self.env['calendar.event'].with_context(no_mail_to_attendees=True).create(meeting_values)
                holiday._create_resource_leave()
                holiday.write({'meeting_id': meeting.id})
                
                
            elif holiday.holiday_type == 'category':
                leaves = self.env['hr.holidays']
                employees = self.env['hr.employee'].search([])
                print '--category--'
                for employee in employees: 
                    if employee.psi_category == holiday.psi_category_id.psi_professional_category :
                        print employee.name
                        values = {
                                'name': holiday.name,
                                'type': holiday.type,
                                'holiday_type': 'employee',
                                'holiday_status_id': holiday.holiday_status_id.id,
                                'date_from': holiday.date_from,
                                'date_to': holiday.date_to,
                                'notes': holiday.notes,
                                'number_of_days_temp': holiday.number_of_days_temp,
                                'parent_id': holiday.id,
                                'employee_id': employee.id
                            }
                        leaves += self.with_context(mail_notify_force_send=False).create(values)
            elif holiday.holiday_type == 'employee' and holiday.all_employee == True:
                leaves = self.env['hr.holidays']
                employees = self.env['hr.employee'].search([])
                print '--all--'
                for employee in employees: 
                    values = {
                        'name': holiday.name,
                        'type': holiday.type,
                        'holiday_type': 'employee',
                        'holiday_status_id': holiday.holiday_status_id.id,
                        'date_from': holiday.date_from,
                        'date_to': holiday.date_to,
                        'notes': holiday.notes,
                        'number_of_days_temp': holiday.number_of_days_temp,
                         'parent_id': holiday.id,
                         'employee_id': employee.id
                    }
                    leaves += self.with_context(mail_notify_force_send=False).create(values)    
                leaves.action_approve()
                if leaves and leaves[0].double_validation:
                    leaves.action_validate()
        return True
    
    _sql_constraints = [
        ('type_value', "CHECK( (holiday_type='employee' AND employee_id IS NOT NULL) or (holiday_type='category' AND psi_category_id IS NOT NULL))",
         "The employee or employee category of this request is missing. Please make sure that your user login is linked to an employee."),
        ('date_check2', "CHECK ( (type='add') OR (date_from <= date_to))", "The start date must be anterior to the end date."),
        ('date_check', "CHECK ( number_of_days_temp >= 0 )", "The number of days must be greater than 0."),
    ]
    
    def datespan(self, start_date, end_date, delta=datetime.timedelta(days=1)):
        current_date = start_date
        while current_date.date() <= end_date.date():
            yield current_date
            current_date += delta
              
    def str_to_timezone(self, time_string):
        time_obj = datetime.datetime.strptime(time_string, DTF)

        return fields.Datetime.context_timestamp(self.env.user, time_obj)
    
    def create_leave_analytic_line(self, holiday, employee, concerned_day, hours):

        account = self.env.ref('hr_holidays_psi.account_leave')
        project = self.env.ref('hr_holidays_psi.project_leave')
        print holiday,' holiday'
        print employee,' employee'
        print concerned_day,' concerned_day'
        print hours, ' hours'
        return self.env['account.analytic.line'].sudo().create({
            'account_id': account.id,
            'project_id': project.id,
            'company_id': employee.company_id.id,
            'amount': 0,
            'date': concerned_day,
            'name': holiday.name,
            'amount_currency': 0,
            'is_timesheet': True,
            'unit_amount': hours,
            'user_id': employee.user_id.id,
            'leave_id': self.id
        })
        
    @api.multi
    def name_get(self):
        res = []
        for leave in self:
            res.append((leave.id, _("%s on %s : %.2f day(s)") % (leave.employee_id.name or leave.psi_category_id.psi_professional_category, leave.holiday_status_id.name, leave.number_of_days_temp)))
        return res
    
    def _increment_doit_conge(self):
        contracts = self.env['hr.contract'].search([])
        dt_now = datetime.datetime.strptime(fields.Date().today(),'%Y-%m-%d')
        
        for contract in contracts :
            holidays = self.env['hr.holidays'].search([('employee_id','=',contract.employee_id.id),('type','=','add')],order='id')
            if len(holidays) > 0:

                dt_write_date = datetime.strptime(holidays[0].write_date,'%Y-%m-%d %H:%M:%S')

                if dt_write_date.month != dt_now.month:
                    number_of_days = holidays[0].number_of_days + 2 
                    holidays[0].write({'number_of_days':number_of_days})
                
            elif contract.date_start != False :
                print contract.employee_id.name
                holidays_status = self.env['hr.holidays.status'].search([('color_name','=','violet')])
                values = {
                                    'name': contract.employee_id.name,
                                    'type': 'add',
                                    'state': 'validate',
                                    'holiday_type': 'employee',
                                    'holiday_status_id': holidays_status[0].id,
                                    'number_of_days_temp': 2,
                                    'employee_id': contract.employee_id.id
                                }
                self.env['hr.holidays'].create(values)

                
    # Send mail - rappel piece justificatif - conge maladie  
    @api.multi
    @api.constrains('holiday_status_id')  
    def _send_email_rappel_justificatif_conge_maladie(self, automatic=False):
        date_debut = self.date_from
        if date_debut != False:
            dt = datetime.datetime.strptime(date_debut,'%Y-%m-%d %H:%M:%S')
            date_y_m_d = datetime(
                                         year=dt.year, 
                                         month=dt.month,
                                         day=dt.day,
                    )   
            date_to_notif = date_y_m_d + relativedelta(hours=48)   
            if self.id != False :
                for record in self:
                    if record.holiday_status_id.color_name == 'blue':
                        #if not record.justificatif_file:
                        if self.attachment_number == 0 and date_to_notif.date() == datetime.today().date() :
                            template = self.env.ref('hr_holidays_psi.custom_template_rappel_justificatif_conge_maladie')
                            self.env['mail.template'].browse(template.id).send_mail(self.id)               
        if automatic:
            self._cr.commit()

    # Mail de rappel aux Assistantes et Coordinateurs
    @api.multi
    def _send_email_rappel_absences_to_assist_and_coord(self, automatic=False):
        print "test cron by send mail rappel"
        today = datetime.today()
        if today.day == 20:
            template = self.env.ref('hr_holidays_psi.custom_template_absences_to_assist_and_coord')
            self.env['mail.template'].browse(template.id).send_mail(self.id)               
        if automatic:
            self._cr.commit()
            
            
    @api.constrains('state', 'number_of_days_temp')
    def _check_holidays(self):
        holidays_status_formation = self.env['hr.holidays.status'].search([('color_name','=','lightpink')])
        holidays_status_annuel = self.env['hr.holidays.status'].search([('color_name','=','violet')])
        for holiday in self:
            
            if holiday.holiday_type != 'employee' or holiday.type != 'remove' or not holiday.employee_id or holiday.holiday_status_id.limit:
                continue
            if holidays_status_formation[0].id == holiday.holiday_status_id and holidays_status_annuel[0].id == holiday.holiday_status_id:
                holidays_attribution = self.env['hr.holidays'].search([('employee_id','',holiday.employee_id.id),('type','=','add')])
                leave_days = holidays_attribution[0].holiday_status_id.get_days(holidays_attribution[0].employee_id.id)[holidays_attribution[0].holiday_status_id.id]
                if float_compare(leave_days['remaining_leaves'], 0, precision_digits=2) == -1 or \
                  float_compare(leave_days['virtual_remaining_leaves'], 0, precision_digits=2) == -1:
                    raise ValidationError(_('The number of remaining leaves is not sufficient for this leave type.\n'
                                            'Please verify also the leaves waiting for validation.'))
