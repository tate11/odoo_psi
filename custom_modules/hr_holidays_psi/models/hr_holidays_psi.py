# -*- coding: utf-8 -*-


from datetime import date, datetime
from datetime import timedelta

import dateutil.parser
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, AccessError
from odoo.tools.translate import _

HOURS_PER_DAY = 8

class hr_holidays_type_psi(models.Model):
    
    _inherit = "hr.holidays.status"
    
    type_permission = fields.Many2one('hr.holidays.type.permission', string="Type de permission")
#    categ_permission = fields.Selection()
    
class hr_holidays_type_permission(models.Model):
    
    _name = "hr.holidays.type.permission"
    _description = "Type de permission"
    
    name = fields.Char('Type de permission', required=True)
    number_of_day = fields.Float('Nombre de jours', required=True)
    
class hr_holidays_psi(models.Model):
    
    _inherit = "hr.holidays"
    
    psi_category_id = fields.Many2one('hr.psi.category.details','Catégorie professionnelle')
    
    color_name_holiday_status = fields.Selection(related='holiday_status_id.color_name', string=u'Couleur du type du congé')
    holiday_type_permission = fields.Many2one(related='holiday_status_id.type_permission', string='Type de permission')
    
    attachment_number           = fields.Integer(compute='_get_attachment_number', string="Number of Attachments")
    attachment_ids              = fields.One2many('ir.attachment', 'res_id', domain=[('res_model', '=', 'hr.holidays')], string='Attachments', track_visibility='always')
    
    all_employee = fields.Boolean(string="Tous les employés")

    state = fields.Selection([
        ('draft', 'To Submit'),
        ('cancel', 'Cancelled'),
        ('confirm', 'To Approve'),
        ('refuse', 'Refused'),
        ('validate1', 'Valider par Supérieur hiérarchique'),
        ('validate2', 'Valider par Responsable RH'),
        ('validate', 'Valider par DRHA')
        ], string='Status', readonly=True, track_visibility='onchange', copy=False, default='confirm',
            help="The status is set to 'To Submit', when a holiday request is created." +
            "\nThe status is 'To Approve', when holiday request is confirmed by user." +
            "\nThe status is 'Refused', when holiday request is refused by manager." +
            "\nThe status is 'Approved', when holiday request is approved by manager.")
        
    @api.model
    def create(self, values):
        got_droit = self.check_droit(values)
        if got_droit == False:
            raise ValidationError(u'Vous ne pouvez pas encore faire une demande de congé.')
        else:
            holidays = super(hr_holidays_psi, self).create(values)
            return holidays
          
    @api.multi
    def write(self, values):
        employee_id = values.get('employee_id', False)
        
        if self.env.user == self.employee_id.user_id:
            raise AccessError(u'Vous ne pouvez plus modifier votre demande, veuillez contacter votre supérieur hiérarchique.')
        
        if self.state == 'confirm' and self.env.user != self.employee_id.department_id.manager_id.user_id:
            raise AccessError(u'Vous ne pouvez pas modifier cette demande de congé.')
        
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
                date_start = datetime.strptime(current_employee.date_start,"%Y-%m-%d")
                date_from = datetime.strptime(values['date_from'],"%Y-%m-%d %H:%M:%S")
                config = self.env['hr.holidays.configuration'].search([])[0]
                diff = (date_from.year - date_start.year) * 12 + date_from.month - date_start.month
                if diff <= config.droit_conge:
                    return False
        return True     
    
    @api.constrains('date_from')
    def _check_date_from(self):
       print "_check_date_from"
       for record in self :
           if record.date_from != False :
               date_from_time = datetime.strptime(record.date_from,"%Y-%m-%d %H:%M:%S")
               date_from = date_from_time.date()
               date_now = datetime.strptime(fields.Date().today(),"%Y-%m-%d")
               between = date_from.day - date_now.day
               between_month = date_now.month - date_from.month
               if (between_month == 1 and date_from.day >= 3) or between_month > 1:
                   raise ValidationError(u"La date du début du congé n'est pas valide.")
               if between < 3 :
                   raise ValidationError(u"Vous devez faire le demande de congés avant 3jours de depart")  
     
    @api.constrains('date_from')
    def _check_date_from_conge_sans_solde(self):
       print "_check_date_from"
       for record in self :
           if record.date_from != False and record.holiday_status_id.color_name == 'red':
               config = self.env['hr.holidays.configuration'].search([])[0]

               if record.number_of_days_temp > config.conges_sans_solde :
                  raise ValidationError(u"Votre demande de congés depaasse le limite de conges sans soldes")

     
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
                    'state': 'open',            # to block that meeting date in the calendar
                    'privacy': 'confidential'
                }
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
    
    @api.multi
    def name_get(self):
        res = []
        for leave in self:
            res.append((leave.id, _("%s on %s : %.2f day(s)") % (leave.employee_id.name or leave.psi_category_id.psi_professional_category, leave.holiday_status_id.name, leave.number_of_days_temp)))
        return res
    
    def _increment_doit_conge(self):
        contracts = self.env['hr.contract'].search([])
        dt_now = datetime.strptime(fields.Date().today(),'%Y-%m-%d')
        
        for contract in contracts :
            print contract.date_start
            holidays = self.env['hr.holidays'].search([('employee_id','=',contract.employee_id.id),('type','=','add')],order='id')
            if len(holidays) > 0:
                if holidays[0].write_date != holidays[0].create_date:
                    dt_write_date = datetime.strptime(holidays[0].write_date,'%Y-%m-%d %H:%M:%S')
                if dt_write_date.year == dt_now.year and dt_write_date.month != dt_now.month :
                    number_of_days = holidays[0].number_of_days + 2 
                    holidays[0].write({'number_of_days':number_of_days})
                elif dt_write_date.year != dt_now.year :
                                    number_of_days = holidays[0].number_of_days + 2 
                                    holidays[0].write({'number_of_days':number_of_days})
            elif contract.date_start != False :
                   # print contract.employee_id.name
                    dt = datetime.strptime(contract.date_start,'%Y-%m-%d')
                    holidays_status = self.env['hr.holidays.status'].search([('color_name','=','violet')])
                    if dt_now.year == dt.year and dt.month != dt_now.month:
                        
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
                    if dt_now.year != dt.year:
                        values = {
                                    'name': contract.employee_id.name,
                                    'type': 'add',
                                    'holiday_type': 'employee',
                                    'holiday_status_id': holidays_status[0].id,
                                    'number_of_days_temp': 2,
                                    'employee_id': contract.employee_id.id,
                                    'state': 'validate',
                                }
                        self.env['hr.holidays'].create(values)
                
    # Send mail - rappel piece justificatif - conge maladie  
    @api.multi
    @api.constrains('holiday_status_id')  
    def _send_email_rappel_justificatif_conge_maladie(self, automatic=False):
        print "test cron by send mail"
        date_debut = self.date_from
        if date_debut != False:
            dt = datetime.strptime(date_debut,'%Y-%m-%d %H:%M:%S')
            date_y_m_d = datetime(
                                         year=dt.year, 
                                         month=dt.month,
                                         day=dt.day,
                    )   
            print "1"
            date_to_notif = date_y_m_d + relativedelta(hours=48)   
            if self.id != False :
                for record in self:
                    if record.holiday_status_id.color_name == 'blue':
                        #if not record.justificatif_file:
                        if not self.justificatif_file and date_to_notif.date() == datetime.today().date() :
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

