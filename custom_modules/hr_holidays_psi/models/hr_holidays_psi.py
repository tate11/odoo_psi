# -*- coding: utf-8 -*-


from datetime import date, datetime
from datetime import timedelta

import dateutil.parser
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.translate import _


HOURS_PER_DAY = 8

class hr_holidays_psi(models.Model):
    
    _inherit = "hr.holidays"
    
    psi_category_id = fields.Many2one('hr.psi.category.details','Catégorie professionnelle')
    
    color_name_holiday_status_conge_maladie = fields.Selection(related='holiday_status_id.color_name', string=u'Couleur du congé maladie')
    color_name_holiday_status_conge_permission = fields.Selection(related='holiday_status_id.color_name', string=u'Couleur du congé permission')
    
    attachment_number           = fields.Integer(compute='_get_attachment_number', string="Number of Attachments")
    attachment_ids              = fields.One2many('ir.attachment', 'res_id', domain=[('res_model', '=', 'hr.holidays')], string='Attachments', track_visibility='always')

    @api.model
    def create(self, values):
        got_droit = self.check_droit(values)
        if got_droit == False:
            raise ValidationError(u'Vous ne pouvez pas encore faire une demande de congé.')
        else:
            holidays = super(hr_holidays_psi, self).create(values)
            return holidays
          
#        print str(color_name_holiday_status_conge_maladie)
        #holidays = super(hr_holidays_psi, self).create()
        #return holidays
        
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
            if holiday.state not in ['confirm', 'validate1']:
                raise UserError(_('Leave request must be confirmed in order to approve it.'))
            if holiday.state == 'validate1' and not holiday.env.user.has_group('hr_holidays.group_hr_holidays_manager'):
                raise UserError(_('Only an HR Manager can apply the second approval on leave requests.'))

            holiday.write({'state': 'validate'})
            if holiday.double_validation:
                holiday.write({'manager_id2': manager.id})
            else:
                holiday.write({'manager_id': manager.id})
            if holiday.holiday_type == 'employee' and holiday.type == 'remove':
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
            if holiday.user_id and holiday.user_id.partner_id:
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
                    # TODO is it necessary to interleave the calls?
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
            
    
