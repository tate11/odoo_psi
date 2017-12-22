# -*- coding: utf-8 -*-

import calendar
import datetime

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, AccessError, Warning
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF
from odoo.tools import float_compare

HOURS_PER_DAY = 8

class HrPublicHolidaysLine(models.Model):
    _inherit = 'hr.holidays.public.line'
    variable = fields.Boolean(string=u'La date peut changer')
    
class hr_holidays_type_psi(models.Model):
    
    _inherit = "hr.holidays.status"
    
    type_permission = fields.Many2one('hr.holidays.type.permission', string="Type de permission")
    holidays_status_id_psi = fields.Integer(string=u"id type de congé psi")
    limit = fields.Boolean(string=u'Dépassement de limite autorisé ', readonly=True)
    
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
    all_employee = fields.Boolean(string="Tous les employés")
    
    number_of_days_psi = fields.Float('Number of Days', compute='_compute_number_of_days_psi', store=True)
    
    state = fields.Selection([
        ('draft', 'To Submit'),
        ('cancel', 'Cancelled'),
        ('confirm', 'To Approve'),
        ('refuse', 'Refused'),
        ('validate1', u'Validé par Supérieur hiérarchique'),
        ('approbation', u'Approuvé par chef de département'),
        ('validate2', u'Validé par RH'),
        ('validate', u'Validé par DRHA')
        ], string='Status', readonly=True, track_visibility='onchange', copy=False, default='confirm',
            help="The status is set to 'To Submit', when a holiday request is created." +
            "\nThe status is 'To Approve', when holiday request is confirmed by user." +
            "\nThe status is 'Refused', when holiday request is refused by manager." +
            "\nThe status is 'Approved', when holiday request is approved by manager.")

     
    @api.constrains('number_of_days_temp')
    def _verif_leave_date(self):
        print "_verif_leave_date"
        
        holidays_status = self.env['hr.holidays.status'].search([('holidays_status_id_psi','=',4)])
        year_now = datetime.datetime.today().year
        holidays = self.env["hr.holidays"].search([('employee_id','=',self.employee_id.name)])
        number_days = 0
        public_holidays_line = self.env['hr.holidays.public.line'].search([])
        for holiday in holidays :
            
            date_from_ = str(datetime.datetime.strptime(holiday.date_from,"%Y-%m-%d").date())
            date_to_ = str(datetime.datetime.strptime(holiday.date_to,"%Y-%m-%d").date())
            write_date = datetime.datetime.strptime(holiday.write_date,"%Y-%m-%d %H:%M:%S")
            write_date_year = write_date.year
            if write_date_year == year_now and holiday.holiday_status_id.id == holidays_status[0].id:
                number_days += holiday.number_of_days
            
            # Verification public holiday JOUR FERIES
            for public_holidays in public_holidays_line:
                date = str(public_holidays.date)
                if date_from_ == date or date_to_ == date:
                    raise ValidationError(u'Vous ne pouvez pas demander du congé durant les jours fériés.')
                    return False 
            
            date_from_w = datetime.datetime.strptime(date_from_, '%Y-%m-%d').strftime('%w')
            date_to_w = datetime.datetime.strptime(date_to_, '%Y-%m-%d').strftime('%w')
                 
            if date_from_w == "6" or date_from_w == "0" or date_to_w == "6" or date_to_w == "0":
                    raise Warning('Vous ne devez pas travailler le week-end!')   
                    return False


        if number_days > 10 :
            raise UserError(u"Vous avez depassé le nombre de jours maximum de permission.")
            return False
        for record in self:
            get_day_difference = record.number_of_days_temp
            type_permissions = self.env['hr.holidays.type.permission'].sudo().search([])            
            for permissions in type_permissions:
                if self.holiday_type_permission.id == permissions.id:
                    if get_day_difference > permissions.number_of_day:
                        raise UserError(u"Vous avez depassé le nombre de jours permi pour ce type de permission.")
                        return False

    
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
        if values.has_key('employee_id'):
            employee = self.env['hr.employee'].browse(values.get('employee_id'))
            recrutement_type = self.env['hr.recruitment.type'].sudo().search([('recrutement_type','=','collaborateur')])
            if employee.job_id.recrutement_type_id.id != recrutement_type[0].id:
                raise ValidationError(u'Seulement les employés permanents peuvent faire une demande de congé.')
                return False
        holidays_status = self.env['hr.holidays.status'].search([('holidays_status_id_psi','=',2)])
        if values.get('holiday_status_id') == holidays_status[0].id :
           got_droit = self.check_droit(values)
           if got_droit == False:
              raise ValidationError(u'Vous ne pouvez pas encore faire une demande de congé.')
              return False
           else:
              holidays = super(hr_holidays_psi, self).create(values)
              return holidays
        else:
              print "second print",values
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
            return False
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
        
        print "self.env.user.id ",self.env.user.id
        print "self.employee_id.coach_id.user_id.id ", self.employee_id.coach_id.user_id.id
        
        if self.env.user.id != self.employee_id.coach_id.user_id.id:
            raise AccessError(u'Vous n\'avez pas le droit de valider cette demande sauf le supérieur hiérarchique.')

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
            if holiday.state != 'approbation':
                raise UserError(_('Leave request must be confirmed ("To Approve") in order to approve it.'))
        return holiday.write({'state': 'validate2', 'manager_id': manager.id if manager else False})
    
    @api.multi
    def action_approbation_departement(self):
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
                config = self.env['hr.holidays.configuration'].sudo().search([])[0]
                diff = (date_from.year - date_start.year) * 12 + date_from.month - date_start.month
                if diff <= config.droit_conge:
                    return False
        return True     
    
    @api.multi
    @api.depends('number_of_days_temp', 'type')
    def _compute_number_of_days_psi(self):
        for holiday in self:
            if holiday.type == 'remove':
                holiday.number_of_days_psi = holiday.number_of_days_temp
            else:
                holiday.number_of_days_psi = holiday.number_of_days_temp
    
    @api.constrains('date_from')
    def _check_date_from(self):
       print "_check_date_from"
       for record in self :
           if record.date_from != False: 
               holidays_status = self.env['hr.holidays.status'].search([('holidays_status_id_psi','=',3)])
               if record.holiday_status_id.id == holidays_status[0].id:
                   config = self.env['hr.holidays.configuration'].sudo().search([])[0]
                   if record.number_of_days_temp > config.conges_sans_solde :
                      raise ValidationError(u"Votre demande de congés depasse la limite de congés sans soldes.")
                      return False
               date_from_time = datetime.datetime.strptime(record.date_from,"%Y-%m-%d %H:%M:%S")
               date_now = datetime.datetime.strptime(fields.Date().today(),"%Y-%m-%d")
               between = date_from_time - date_now
              
               if between.days < 0: 
                   raise ValidationError(u"La date de début du congé n'est pas valide.")
                   return False
               holidays_status = self.env['hr.holidays.status'].search([('holidays_status_id_psi','=',4)])
              
               if record.holiday_status_id.id != holidays_status[0].id: # a part maladie
                   if between.days >= 0 and between.days < 3 :
                       raise ValidationError(u"Vous devez faire une demande de congés au moins 3 jours avant votre départ pour congé.")
                       return False
               holidays_status_maternite = self.env['hr.holidays.status'].search([('holidays_status_id_psi','=',6)])
               if record.holiday_status_id.id == holidays_status_maternite[0].id :
                   if record.employee_id.sexe == 'masculin':
                       raise ValidationError(u"Le congé maternité est réserve pour les femmes :) .")
                       return False
                   if record.number_of_days_temp > 98 :
                       raise ValidationError(u"Desole, vous avez depassé le nombre de congé maternite.")
                       return False
    @api.multi
    def action_validate(self):
        print "action_validate"

        if not self.env.user.has_group('hr_holidays.group_hr_holidays_user'):
            raise UserError(_('Only an HR Officer or Manager can approve leave requests.'))

        manager = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        for holiday in self:
            if holiday.state not in ['confirm', 'validate', 'validate1', 'validate2']:
                raise UserError(u'La demande ne peut pas être refusée que si elle est déjà validée par un supérieur')
            if holiday.state == 'validate2' and not holiday.env.user.has_group('hr_holidays.group_hr_holidays_manager'):
                raise UserError(_('Only an HR Manager can apply the second approval on leave requests.'))

            holiday.write({'state': 'validate'})
            print "holiday.write({'state': 'validate'})"
            
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
        
                    # Horaire de travail par region
                    heure_par_jour = 0.0
                    attendance_ids = employee.calendar_id.attendance_ids
                    print "attendance_ids ",attendance_ids
                    date_now = datetime.datetime.strptime(fields.Date().today(),'%Y-%m-%d')
                    dayofweek = int(datetime.datetime.strptime(str(date_now.date()), '%Y-%m-%d').strftime('%w'))
                    for attendance_id in attendance_ids:
                        attendances = self.env['resource.calendar.attendance'].search([['id', '=', attendance_id.id], ['dayofweek', '=', dayofweek]])
                        for attendance in attendances:
                            heure_par_jour += attendance.hour_to - attendance.hour_from
                    
                    for timestamp in self.datespan(time_from, time_to):
                        company = employee.company_id
                        date = timestamp.date()
                        hours = heure_par_jour
                        
                        date_str = str(date)
                        self.create_leave_analytic_line(holiday, employee, date_str, hours)
                 
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
    
#     Creation timesheet
    def create_leave_analytic_line(self, holiday, employee, concerned_day, hours):

        account = self.env.ref('hr_holidays_psi.account_leave')
        project = self.env.ref('hr_holidays_psi.project_leave')

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
        leave_display_name = ''
        for leave in self:
            if (leave.employee_id.name or leave.psi_category_id.psi_professional_category) and leave.holiday_status_id.name and leave.number_of_days_temp:
                leave_display_name = _("%s on %s : %.2f day(s)") % (leave.employee_id.name or leave.psi_category_id.psi_professional_category, leave.holiday_status_id.name, leave.number_of_days_temp)
            res.append((leave.id, leave_display_name))
        return res
    
    def _increment_doit_conge(self):
        contracts = self.env['hr.contract'].search([])
        dt_now = datetime.datetime.strptime(fields.Date().today(),'%Y-%m-%d')
        
        for contract in contracts :
            holidays = self.env['hr.holidays'].search([('employee_id','=',contract.employee_id.id),('type','=','add')],order='id')
            if len(holidays) > 0:

                dt_write_date = datetime.datetime.strptime(holidays[0].write_date,'%Y-%m-%d %H:%M:%S')

                if dt_write_date.month != dt_now.month:
                    number_of_days = holidays[0].number_of_days + 2 
                    holidays[0].write({'number_of_days':number_of_days})
                
            elif contract.date_start != False :
                print contract.employee_id.name
                holidays_status = self.env['hr.holidays.status'].search([('holidays_status_id_psi','=',2)])
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
        print "_send_email_rappel_justificatif_conge_maladie"
        
        date_debut = self.date_from
        if date_debut != False:
            dt = datetime.datetime.strptime(date_debut,'%Y-%m-%d %H:%M:%S')
            date_y_m_d = datetime.datetime(
                                         year=dt.year, 
                                         month=dt.month,
                                         day=dt.day,
                    )
            date_to_notif = date_y_m_d + relativedelta(hours=48)   
            if self.id != False :
                for record in self:
                    holidays_status = self.env['hr.holidays.status'].search([('holidays_status_id_psi','=',4)])
                    if record.holiday_status_id.id == holidays_status[0].id:
                        #if not record.justificatif_file:
                        if self.attachment_number == 0 and date_to_notif.date() == datetime.datetime.today().date() :
                            template = self.env.ref('hr_holidays_psi.custom_template_rappel_justificatif_conge_maladie')
                            self.env['mail.template'].browse(template.id).send_mail(self.id)               
        if automatic:
            self._cr.commit()

    
    @api.onchange('date_from')
    def _onchange_date_from(self):
        print "_onchange_date_from"
        holidays_status = self.env['hr.holidays.status'].search([('holidays_status_id_psi','=',6)])
        
        date_from = self.date_from
        date_to = self.date_to
        if self.holiday_status_id.id == holidays_status[0].id:
            print holidays_status[0].name
           
            date_to_with_delta = fields.Datetime.from_string(date_from) + datetime.timedelta(days=98)
            self.date_to = str(date_to_with_delta)
        # No date_to set so far: automatically compute one 8 hours later
        if date_from and not date_to:
            date_to_with_delta = fields.Datetime.from_string(date_from) + datetime.timedelta(hours=HOURS_PER_DAY)
            self.date_to = str(date_to_with_delta)

        # Compute and update the number of days
        if (date_to and date_from) and (date_from <= date_to):
            self.number_of_days_temp = self._get_number_of_days(date_from, date_to, self.employee_id.id)
        else:
            self.number_of_days_temp = 0
            
    @api.onchange('holiday_status_id')
    def _onchange_holiday_status_id(self):
        print "_onchange_holiday_status_id"
        holidays_status = self.env['hr.holidays.status'].search([('holidays_status_id_psi','=',6)])
        
        date_from = self.date_from
        date_to = self.date_to
        if self.holiday_status_id.id == holidays_status[0].id:
            print holidays_status[0].name
           
            date_to_with_delta = fields.Datetime.from_string(date_from) + datetime.timedelta(days=98)
            self.date_to = str(date_to_with_delta)
        # No date_to set so far: automatically compute one 8 hours later
        if date_from and not date_to:
            date_to_with_delta = fields.Datetime.from_string(date_from) + datetime.timedelta(hours=HOURS_PER_DAY)
            self.date_to = str(date_to_with_delta)

        # Compute and update the number of days
        if (date_to and date_from) and (date_from <= date_to):
            self.number_of_days_temp = self._get_number_of_days(date_from, date_to, self.employee_id.id)
        else:
            self.number_of_days_temp = 0
    
    # Mail de rappel aux Assistantes et Coordinateurs
    @api.multi
    def _send_email_rappel_absences_to_assist_and_coord(self, automatic=False):
        print "test cron by send mail rappel"
        today = datetime.datetime.today()
        if today.day == 20:
            template = self.env.ref('hr_holidays_psi.custom_template_absences_to_assist_and_coord')
            self.env['mail.template'].browse(template.id).send_mail(self.id)               
        if automatic:
            self._cr.commit()
            
            
    @api.constrains('state', 'number_of_days_temp')
    def _check_holidays(self):
        print "_check_holidays"
        holidays_status_formation = self.env['hr.holidays.status'].search([('holidays_status_id_psi','=',5)])
        holidays_status_annuel = self.env['hr.holidays.status'].search([('holidays_status_id_psi','=',2)])
        for holiday in self:
            if holiday.holiday_type != 'employee' or holiday.type != 'remove' or not holiday.employee_id or holiday.holiday_status_id.limit:
                print "not continue"
                continue
            if holidays_status_formation[0].id == holiday.holiday_status_id.id and holidays_status_annuel[0].id == holiday.holiday_status_id.id:
                print "not continue"
                holidays_attribution = self.env['hr.holidays'].search([('employee_id','',holiday.employee_id.id),('type','=','add')])
                leave_days = holidays_attribution[0].holiday_status_id.get_days(holidays_attribution[0].employee_id.id)[holidays_attribution[0].holiday_status_id.id]
                if float_compare(leave_days['remaining_leaves'], 0, precision_digits=2) == -1 or \
                  float_compare(leave_days['virtual_remaining_leaves'], 0, precision_digits=2) == -1:
                    raise ValidationError(_('The number of remaining leaves is not sufficient for this leave type.\n'
                                            'Please verify also the leaves waiting for validation.'))
    
    @api.multi
    def action_refuse(self):
        if not self.env.user.has_group('hr_holidays.group_hr_holidays_user'):
            raise UserError(_('Only an HR Officer or Manager can refuse leave requests.'))

        manager = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        for holiday in self:
            if holiday.state not in ['confirm', 'validate', 'validate1', 'validate2']:
                raise UserError(u'La demande ne peut pas être refusée que si elle est déjà validée par un supérieur')

            if holiday.state == 'validate1':
                holiday.write({'state': 'refuse', 'manager_id': manager.id})
            else:
                holiday.write({'state': 'refuse', 'manager_id2': manager.id})
            # Delete the meeting
            if holiday.meeting_id:
                holiday.meeting_id.unlink()
            # If a category that created several holidays, cancel all related
            holiday.linked_request_ids.action_refuse()
        self._remove_resource_leave()
        return True
