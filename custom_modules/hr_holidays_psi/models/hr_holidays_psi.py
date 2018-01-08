# -*- coding: utf-8 -*-

from datetime import date, timedelta

import calendar
import datetime


from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, AccessError, Warning
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF
from odoo.tools import float_compare
from calendar import monthrange

HOURS_PER_DAY = 8

class HrPublicHolidaysLine(models.Model):
    _inherit = 'hr.holidays.public.line'
    variable = fields.Boolean(string=u'La date peut changer')
    
class hr_holidays_type_psi(models.Model):
    
    _inherit = "hr.holidays.status"
        
    type_permission = fields.Many2one('hr.holidays.type.permission', string="Type de permission")
    holidays_status_id_psi = fields.Integer(string=u"id type de congé psi")
    limit = fields.Boolean(string=u'Dépassement de limite autorisé ', readonly=True)
    is_not_limited_j3 = fields.Boolean(string=u'is_not_limited_j3')
    @api.multi
    def get_days(self, employee_id):
        # need to use `dict` constructor to create a dict per id
        result = dict((id, dict(max_leaves=0, leaves_taken=0, remaining_leaves=0, virtual_remaining_leaves=0)) for id in self.ids)

        holidays = self.env['hr.holidays'].search([
            ('employee_id', '=', employee_id),
            ('state', 'in', ['confirm', 'validate1', 'validate']),
            ('holiday_status_id', 'in', self.ids)
        ])

        for holiday in holidays:
            status_dict = result[holiday.holiday_status_id.id]
            if holiday.type == 'add':
                if holiday.state == 'validate':
                    # note: add only validated allocation even for the virtual
                    # count; otherwise pending then refused allocation allow
                    # the employee to create more leaves than possible
                    status_dict['virtual_remaining_leaves'] += holiday.number_of_days_temp
                    status_dict['max_leaves'] += holiday.employee_id.nombre_conge
                    status_dict['remaining_leaves'] += holiday.nombre_conge
            elif holiday.type == 'remove':  # number of days is negative
                status_dict['virtual_remaining_leaves'] -= holiday.number_of_days_temp
                if holiday.state == 'validate':
                    status_dict['leaves_taken'] += holiday.number_of_days_temp
                    status_dict['remaining_leaves'] -= holiday.nombre_conge
        return result

   
    
    
    
class hr_holidays_type_permission(models.Model):
    
    _name = "hr.holidays.type.permission"
    _description = "Type de permission"
    
    name = fields.Char('Type de permission', required=True)
    number_of_day = fields.Float('Jours autorisés', required=True)
    cosomme = fields.Char(string='Consommés ?',compute='_compute_cosomme')

    @api.multi
    def _compute_cosomme(self):
        print "_compute_consomme"
        if 'employee_id' in self._context:
            employee_id = self._context['employee_id']
        else:
            employee_id = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1).id

        if employee_id:
            holidays_status_id = self.env['hr.holidays.status'].search([('holidays_status_id_psi','=',1)])
            holidays = self.env['hr.holidays'].search([
                                                       ('employee_id', '=', employee_id),
                                                       ('state', 'in', ['validate']),
                                                       ('holiday_status_id', '=', holidays_status_id[0].id)
                                                       ])
            for holiday_status in self:
                holiday_status.cosomme = 'Non'
            for holiday in holidays :
                for holiday_status in self:
                    if holiday_status.name == holiday.holiday_status_id.type_permission.name : 
                        holiday_status.cosomme = 'Oui'
            

    
class hr_holidays_psi(models.Model):
    
    _inherit = "hr.holidays"
    
    psi_category_id = fields.Many2one('hr.psi.category.details',u'Catégorie professionnelle')
    
    color_name_holiday_status = fields.Selection(related='holiday_status_id.color_name', string=u'Couleur du type du congé')
    id_psi_holidays_status = fields.Integer(related='holiday_status_id.holidays_status_id_psi')
    holiday_type_permission = fields.Many2one(related='holiday_status_id.type_permission', string='Type de permission')
    
    attachment_number           = fields.Integer(compute='_get_attachment_number', string="Number of Attachments")
    attachment_ids              = fields.One2many('ir.attachment', 'res_id', domain=[('res_model', '=', 'hr.holidays')], string='Attachments', track_visibility='always')
    date_from = fields.Date('Start Date', readonly=True, index=True, copy=False,states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})
    date_to = fields.Date('End Date', readonly=True, index=True, copy=False,states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})
    demi_jour = fields.Boolean(string="Demi-journée")
    deduit = fields.Boolean(string="Déductible")
    matin_soir = fields.Selection([('matin','Matin'),('soir','Soir')], default="matin", string=u'Matin ou Soir')
    
    job_id = fields.Many2one(related='employee_id.job_id', store=True)
    all_employee = fields.Boolean(string="Tous les employés")
    
    number_of_days_psi = fields.Float('Number of Days', compute='_compute_number_of_days_psi', store=True)
    number_of_days_temp = fields.Float(compute='_compute_date_from_to', string='Allocation', default="1.0", copy=False, states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})
    nombre_conge = fields.Float(string="Nombre de conge attribuer")
    
    is_user_rh = fields.Boolean(help="Verifier si utilisateur RH", compute='_is_user_rh')
    is_user_employee_concerned = fields.Boolean(compute="_is_current_user_equal_leave_employee")
    
    state = fields.Selection([
        ('draft', u'A soumettre pour validation'),
        ('cancel', u'Annuler'),
        ('confirm', u'A valider par le Supérieur hiérarchique'),
        ('refuse', u'Refusé'),
        ('validate1', u'A valider par le Chef de Département'),
        ('approbation', u'A valider par le Responsable RH'),
        ('validate2', u'A valider par le DRHA'),
        ('validate', u'Validé par le DRHA')
        ], string='Status', readonly=True, track_visibility='onchange', copy=False, default='draft',
            help="The status is set to 'To Submit', when a holiday request is created." +
            "\nThe status is 'To Approve', when holiday request is confirmed by user." +
            "\nThe status is 'Refused', when holiday request is refused by manager." +
            "\nThe status is 'Approved', when holiday request is approved by manager.")
                
    @api.multi
    def action_confirm(self):
        if self.filtered(lambda holiday: holiday.state != 'draft'):
            raise UserError(_('Leave request must be in Draft state ("To Submit") in order to confirm it.'))
        
        # Send notif Congé
        self._send_mail_validation_conge(self)
        
        return self.write({'state': 'confirm'})
    
    # Contrôle week-end et jours fériés
    def compute_day_off(self, date):
        result = 0
        current_day=datetime.datetime.strptime(date, '%Y-%m-%d').strftime('%w')
        if current_day == "6" or current_day == "0" :
            result += 1
        
        public_holidays_line = self.env['hr.holidays.public.line'].sudo().search([])
        for public_holiday in public_holidays_line:
            if public_holiday.date == date:
                result += 1
        return result
       
    ############### BEGIN Verif if user RH ###############
    @api.one
    def _is_user_rh(self):
        print '_is_user_rh'
        self.is_user_rh = self.env.user.has_group('hr_holidays_psi.group_hr_holidays_rh')
        print self.is_user_rh," ???? RH ????"        
    ############### END Verif if user RH ###############
    
    @api.one 
    def _is_current_user_equal_leave_employee(self):
        print '_is_current_user_equal_leave_employee'
        user_current = self.env.user
        for record in self:
            if record.id:
                if user_current == record.employee_id.user_id:
                    record.is_user_employee_concerned = True
             
    @api.depends('date_from', 'date_to', 'demi_jour', 'holiday_status_id','number_of_days_temp')
    def _compute_date_from_to(self):
        print "_compute_date_from_to" 
                  
        #super(hr_holidays_psi,self)._onchange_date_from()
        public_holidays_line = self.env['hr.holidays.public.line'].sudo().search([])
        for record in self:
            if record.date_from and record.date_to:
                if record.demi_jour == True:
                    record.number_of_days_temp = 0.5
                    record.date_to = record.date_from
                else:
                    record.number_of_days_temp = 1.0
                    
                if record.date_from > record.date_to:
                    record.date_to = record.date_from
                if record.demi_jour == True:
                    record.number_of_days_temp = 0.5
                    record.date_to = record.date_from
                else:
                    day_hours = str(datetime.datetime.strptime(record.date_to, "%Y-%m-%d") - datetime.datetime.strptime(record.date_from, "%Y-%m-%d")).split(" day")
                    if day_hours:
                        if day_hours[0] == "0:00:00":
                            record.number_of_days_temp = 1.0
                        else:
                            record.number_of_days_temp = float(day_hours[0]) + 1.0
                                
                # ENLEVE WEEK END ET JOUR FERIE (sauf CONGE SANS SOLDE)
                date_from = datetime.datetime.strptime(record.date_from, "%Y-%m-%d").date()
                date_to = datetime.datetime.strptime(record.date_to, "%Y-%m-%d").date()

                print date_from,' > date_from'
                print date_to,' > date_to'
                print record.id
                print record.name
                
                # Verification si date_from et date_to W-END ou JOUR FERIE
                self.verif_day_off(str(date_from))
                self.verif_day_off(str(date_to))
                # FIN Verification si date_from et date_to W-END ou JOUR FERIE
        
                holidays_status_maternite = self.env['hr.holidays.status'].search([('holidays_status_id_psi','=',6)])   #  CONGE MATERNITE
                holidays_status_sans_solde = self.env['hr.holidays.status'].search([('holidays_status_id_psi','=',3)])  #  CONGE SANS SOLDE
                
                if record.holiday_status_id.id != holidays_status_maternite[0].id and record.holiday_status_id.id != holidays_status_sans_solde[0].id:
                    print "NO MATERNITE and NO SANS SOLD"
                    delta = date_to - date_from
                    for i in range(delta.days + 1):
                            current_day=datetime.datetime.strptime(str(date_from + timedelta(days=i)), '%Y-%m-%d').strftime('%w')
                            if current_day == "6" or current_day == "0" :                                   # VERIFICATION W-END
#                                 print "W-end"
                                record.number_of_days_temp -= 1
                            for public_holiday in public_holidays_line:                                     # VERIFICATION JOUR FERIE
                                if str(public_holiday.date) == str(date_from + timedelta(days=i)):
#                                     print "OUI JF"
                                    record.number_of_days_temp -= 1
            
        
          
    @api.onchange('date_from')
    def _onchange_date_from(self):
        return {}

    @api.onchange('date_to')
    def _onchange_date_to(self):
        return {}
    
    @api.constrains('number_of_days_temp')
    def _verif_leave_date(self):
        print "_verif_leave_date"
        
        holidays_status = self.env['hr.holidays.status'].sudo().search([('holidays_status_id_psi','=',4)])
        year_now = datetime.datetime.today().year
        holidays = self.env["hr.holidays"].search([('employee_id', '=', self.employee_id.id), ('type', '=', 'remove')])
        number_days = 0
        public_holidays_line = self.env['hr.holidays.public.line'].sudo().search([])
        for holiday in holidays :
            
            date_from_ = str(datetime.datetime.strptime(holiday.date_from,"%Y-%m-%d").date())
            date_to_ = str(datetime.datetime.strptime(holiday.date_to,"%Y-%m-%d").date())
            write_date = datetime.datetime.strptime(holiday.write_date,"%Y-%m-%d %H:%M:%S")
            write_date_year = write_date.year
            if write_date_year == year_now and holiday.holiday_status_id.id == holidays_status[0].id:
                number_days += holiday.number_of_days
            
            # Verification public holiday JOUR FERIES
            for public_holidays in public_holidays_line:
                date_from_ = str(datetime.datetime.strptime(holiday.date_from,"%Y-%m-%d").date())
                date_to_ = str(datetime.datetime.strptime(holiday.date_to,"%Y-%m-%d").date())
                date = str(public_holidays.date)
#                 print date_from_," == ",date," or ",date_to_," == ",date 
                
#                 if date_from_ == date or date_to_ == date:
#                     raise ValidationError(u'Vous ne pouvez pas demander du congé durant les jours fériés.')
#                     return False 
            
            
#                 if self.env['hr.holidays.public'].is_public_holiday(date_from_, employee_id=self.employee_id.id) or self.env['hr.holidays.public'].is_public_holiday(date_to_, employee_id=self.employee_id.id):
#                     raise ValidationError(u'Vous ne pouvez pas demander du congé durant les jours fériés.')
#                     return False 
                
#             date_from_w = datetime.datetime.strptime(date_from_, '%Y-%m-%d').strftime('%w')
#             date_to_w = datetime.datetime.strptime(date_to_, '%Y-%m-%d').strftime('%w')
#                  
#             if date_from_w == "6" or date_from_w == "0" or date_to_w == "6" or date_to_w == "0":
#                     raise Warning('Vous ne devez pas travailler le week-end!')   
#                     return False


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
                    elif get_day_difference < permissions.number_of_day:
                        raise UserError(u"Veuillez verifier le date de permission.")
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
    
    # Contrôle week-end et jours fériés
    def verif_day_off(self, date):
        print "Verification +"
        current_day=datetime.datetime.strptime(date, '%Y-%m-%d').strftime('%w')
        if current_day == "6" or current_day == "0" :
            raise Warning('Vous ne pouvez pas demander de congé le week-end.')  
            return False
        
        public_holidays_line = self.env['hr.holidays.public.line'].sudo().search([])
        for public_holiday in public_holidays_line:
            if public_holiday.date == date:

                raise Warning('Vous ne pouvez pas demander de congé pendant les jours fériés.')
            
   
    # Contrôle week-end et jours fériés
    def verif_day_not_working(self, date):
        print "Verification +"
        current_day=datetime.datetime.strptime(date, '%Y-%m-%d').strftime('%w')
        if current_day == "6" or current_day == "0" :
            return True
        
        public_holidays_line = self.env['hr.holidays.public.line'].sudo().search([])
        for public_holiday in public_holidays_line:
            if public_holiday.date == date:
                return True
        return False    

    @api.model
    def create(self, values):
        
        print "create hr.holidays"
        if values.has_key('type') and values.get('type') == 'add' :
            holidays = super(hr_holidays_psi, self).create(values)
            return holidays
        if values.has_key('date_from'):
#             if record.date_from and record.date_to:
#                 print '2'
                date_from = datetime.datetime.strptime(values.get('date_from'),"%Y-%m-%d").date()
                date_to = datetime.datetime.strptime(values.get('date_to'),"%Y-%m-%d").date()
                delta = date_to - date_from
                
                self.verif_day_off(str(date_from))
                self.verif_day_off(str(date_to))
                
                for i in range(delta.days + 1):
                    day = datetime.datetime.strptime(str(date_from + timedelta(days=i)), '%Y-%m-%d').strftime('%w')   
                    print day                                             
                    public_holidays_line = self.env['hr.holidays.public.line'].sudo().search([])
                    print public_holidays_line,'  public_holidays_line'
        
        #             for public_holiday in public_holidays_line:
        #                 print  public_holiday.date, u" liste jour ferié == date_from > date_to ",date_from + timedelta(days=i)
        #                 if str(public_holiday.date) == str(date_from + timedelta(days=i)):
        #                     print 'ENTER'
        #                     if day == "6" or day =="0":
        #                         raise Warning('Erreur.')
        
        
                if values.has_key('employee_id'):
                    employee = self.env['hr.employee'].browse(values.get('employee_id'))
                    recrutement_type = self.env['hr.recruitment.type'].sudo().search([('recrutement_type','=','collaborateur')])
                    if employee.job_id.recrutement_type_id.id != recrutement_type[0].id:
                        raise ValidationError(u'Seulement les employés permanents peuvent faire une demande de congé.')
                        return False
                holidays_status_permission = self.env['hr.holidays.status'].search([('holidays_status_id_psi','=',1)])
                if values.get('holiday_status_id') == holidays_status_permission[0].id :
                    date_difference = 0.0
                    date_from = datetime.datetime.strptime(values['date_from'],"%Y-%m-%d")
                    date_to = datetime.datetime.strptime(values['date_to'],"%Y-%m-%d")
                    
                    d1 = date(date_from.year, date_from.month, date_from.day)  # start date
                    d2 = date(date_to.year, date_to.month, date_to.day)  # end date
    
                    delta = d2 - d1
                    for i in range(delta.days + 1):
                        date_str = (d1 + timedelta(days=i))
                        if not self.verif_day_not_working(str(date_str)) :
                            date_difference += 1
                    diff = 0.0
                    if values.has_key('holiday_type_permission') :
                        holidays_permission = self.env['hr.holidays.type.permission'].browse(values.get('holiday_type_permission'))
                        diff = holidays_permission.number_of_day
                    print "date_difference : ",date_difference
                    print "diff : ",diff
                    if str(date_difference) != str(diff) :
                        print "IF"
                        raise Warning(u'Vous devez poser exactement {} jour(s) de congé pour ce type de permission.'.format(diff))
                        #return False
                    else :
                        print "ELSE"
                holidays_status = self.env['hr.holidays.status'].search([('holidays_status_id_psi','=',2)])
               
                if values.get('holiday_status_id') == holidays_status[0].id :
                   nombre_conge = 0
                   number_of_days = 0
                   
                   got_droit = self.check_droit(values)
                   if got_droit == False:
                      raise ValidationError(u'Vous ne pouvez pas encore faire une demande de congé.')
                      return False
                   else:
                      holidays = self.env['hr.holidays'].search([('type','=','add'),('employee_id','=', employee.id)])
                      date_from = datetime.datetime.strptime(values['date_from'],"%Y-%m-%d")
                      date_to = datetime.datetime.strptime(values['date_to'],"%Y-%m-%d")
                    
                      d1 = date(date_from.year, date_from.month, date_from.day)  # start date
                      d2 = date(date_to.year, date_to.month, date_to.day)  # end date
    
                      delta = d2 - d1
                      for i in range(delta.days + 1):
                          number_of_days += i 
                      if len(holidays) > 0 :
                          nombre_conge = holidays[0].nombre_conge - number_of_days
                          if nombre_conge < 0 :
                              raise ValidationError(u'Nombre conge insuiffisant.')
                              return False
                      else:
                          raise ValidationError(u'Nombre conge insuiffisant.')
                          return False
                      values['deduit'] = True
                      holidays = super(hr_holidays_psi, self).create(values)
                      return holidays
                else:
                      values['deduit'] = False
                      print "second print",values
                      holidays = super(hr_holidays_psi, self).create(values)
                      return holidays
        
                  
    @api.multi
    def write(self, values):
        print "write"
        print values
        
        holidays_status_permission = self.env['hr.holidays.status'].search([('holidays_status_id_psi','=',1)])
        if self.holiday_status_id.id == holidays_status_permission[0].id :
            date_difference = 0.0
            diff = 0.0
            delta = 0.0
            d1 = 0.0
            d2 = 0.0
            if values.has_key('date_from') and values.has_key('date_to') :
                date_from = datetime.datetime.strptime(values.get('date_from'),"%Y-%m-%d")
                date_to = datetime.datetime.strptime(values.get('date_to'),"%Y-%m-%d")
                d1 = date(date_from.year, date_from.month, date_from.day)  # start date
                d2 = date(date_to.year, date_to.month, date_to.day)  # start date 
                delta = d2 - d1 
            elif values.has_key('date_from') and not values.has_key('date_to') :
                date_from = datetime.datetime.strptime(values.get('date_from'),"%Y-%m-%d")
                date_to = datetime.datetime.strptime(self.date_to,"%Y-%m-%d")
                d1 = date(date_from.year, date_from.month, date_from.day)  # start date
                d2 = date(date_to.year, date_to.month, date_to.day)  # start date
                delta = d2 - d1
            elif not values.has_key('date_from') and values.has_key('date_to') :
                print "self.date_from ",self.date_from
                print "values.has_key('date_to') ",values.get('date_to')
                date_from = datetime.datetime.strptime(self.date_from,"%Y-%m-%d")
                date_to = datetime.datetime.strptime(values.get('date_to'),"%Y-%m-%d")
                d1 = date(date_from.year, date_from.month, date_from.day)  # start date
                d2 = date(date_to.year, date_to.month, date_to.day)  # start date
                delta = d2 - d1
            else:
                date_from = datetime.datetime.strptime(self.date_from,"%Y-%m-%d")
                date_to = datetime.datetime.strptime(self.date_to,"%Y-%m-%d")
                d1 = date(date_from.year, date_from.month, date_from.day)  # start date
                d2 = date(date_to.year, date_to.month, date_to.day)  # start date
                delta = d2 - d1
            print "delta : ",delta
            print d1
            for i in range(delta.days + 1):
               date_str = (d1 + timedelta(days=i))
               if not self.verif_day_not_working(str(date_str)) :
                  date_difference += 1
            diff = self.holiday_type_permission.number_of_day
            if values.has_key('holiday_type_permission') :
                  print 
                  holidays_permission = self.env['hr.holidays.type.permission'].browse(values.get('holiday_type_permission'))
                  diff = holidays_permission.number_of_day
            print "date_difference write",date_difference
            print "diff write",diff
            if str(date_difference) != str(diff) :
                raise Warning(u'Vous devez poser exactement {} jour(s) pour ce type de permission.'.format(diff))
                return False                         
        
#         date_from = datetime.datetime.strptime(vals.get('date_from'),"%Y-%m-%d").date()
#         date_to = datetime.datetime.strptime(vals.get('date_to'),"%Y-%m-%d").date()
    
        
#         self.verif_day_off(str(date_from))
#         self.verif_day_off(str(date_to))
        
        #self._send_email_rappel_absences_to_assist_and_coord(False)
        #self._verif_leave_date()
        
#         if self.env.user == self.employee_id.user_id:
#             raise AccessError(u'Vous ne pouvez plus modifier votre demande, veuillez contacter votre supérieur hiérarchique.')

#        if self.state == 'validate1' and self.env.user != self.employee_id.department_id.manager_id.user_id:
#            raise AccessError(u'Vous ne pouvez pas modifier cette demande de congé.')

        
#         if not self._check_state_access_right(values):
#             raise AccessError(_('You cannot set a leave request as \'%s\'. Contact a human resource manager.') % values.get('state'))
#             return False

        result = super(hr_holidays_psi, self).write(values)
        #self.add_follower(employee_id)
        return result
    
    def _check_state_access_right(self, vals):
        return True
    
    def action_report_request_for_absences(self):
        return {
               'type': 'ir.actions.report.xml',
               'report_name': 'hr_holidays_psi.report_request_for_absences'
           }
      
    @api.multi
    def action_approve(self):
        # if double_validation: this method is the first approval approval
        # if not double_validation: this method calls action_validate() below
        
        print "self.env.user.id ",self.env.uid
        print "self.employee_id.coach_id.user_id.id ", self.employee_id.coach_id.user_id.id
        
        if self.env.uid != self.employee_id.coach_id.user_id.id:
            raise AccessError(u'Vous n\'avez pas le droit de valider cette demande sauf le supérieur hiérarchique.')

        # Send notif Congé
        self._send_mail_validation_conge(self)
        
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
        if not self.env.user.has_group('hr_holidays_psi.group_hr_holidays_rh') and not self.env.user.has_group('hr_holidays_psi.group_hr_holidays_spa'):
            raise UserError(_('Only an HR Officer or Manager can approve leave requests.'))

        # Send notif Congé
        self._send_mail_validation_conge(self)
        
        manager = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        for holiday in self:
            if holiday.state != 'approbation':
                raise UserError(_('Leave request must be confirmed ("To Approve") in order to approve it.'))
        return holiday.write({'state': 'validate2', 'manager_id': manager.id if manager else False})
    
    @api.multi
    def action_approbation_departement(self):
        # if double_validation: this method is the first approval approval
        # if not double_validation: this method calls action_validate() below
        if not self.env.user.has_group('hr_holidays_psi.group_hr_holidays_chef_departement'):
            raise UserError(_('Only an HR Officer or Manager can approve leave requests.'))

        # Send notif Congé
        self._send_mail_validation_conge(self)
                
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
        current_employee = self.env['hr.contract'].sudo().search([('employee_id', '=', values['employee_id'])])
        
        if values.has_key('date_from') and current_employee.date_start != False :
            if values['date_from'] != False :
                date_start = datetime.datetime.strptime(current_employee.date_start,"%Y-%m-%d")
                date_from = datetime.datetime.strptime(values['date_from'],"%Y-%m-%d")
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
    
    @api.constrains('date_from','name','holiday_status_id','demi_jour')
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
                  
               date_from_time = datetime.datetime.strptime(record.date_from,"%Y-%m-%d")
               date_now = datetime.datetime.strptime(fields.Date().today(),"%Y-%m-%d")
               between = date_from_time - date_now
              
               holidays_status = self.env['hr.holidays.status'].search([('is_not_limited_j3','=',True)])
               
               temp_not_limited = False
               for holidays_status_not_limited in holidays_status:
                   if record.holiday_status_id.id == holidays_status_not_limited.id: 
                        temp_not_limited = True
               if not temp_not_limited:
                    if between.days < 3 :
                        raise ValidationError(u"Vous devez effectuer votre demande au moins 3 jours avant votre départ en congé.")
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

        if not self.env.user.has_group('hr_holidays_psi.group_hr_holidays_drha'):
            raise UserError(_('Only an HR Officer or Manager can approve leave requests.'))

        manager = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        for holiday in self:
            if holiday.state not in ['confirm', 'validate', 'validate1', 'validate2', 'approbation']:
                raise UserError(u'Une demande de congé ne peut être refusée si elle a déjà été validée par le Responsable RH ou le DRHA')
            if holiday.state == 'validate2' and not holiday.env.user.has_group('hr_holidays_psi.group_hr_holidays_drha'):
                raise UserError('Seul DRHA peut valider la demande.')
           
            holiday.write({'state': 'validate'})
            holidays = self.env['hr.holidays'].search([('type','=','add'),('employee_id','=', holiday.employee_id.id)])
            holidays_status = self.env['hr.holidays.status'].search([('holidays_status_id_psi','=',2)])
            if holiday.holiday_status_id.id == holidays_status[0].id and len(holidays[0]) > 0:
                nombre_conge = holidays[0].nombre_conge - holiday.number_of_days_psi 
                holidays[0].write({'nombre_conge': nombre_conge})
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
                        
#                     time_from = self.str_to_timezone(holiday.date_from)
#                     time_to = self.str_to_timezone(holiday.date_to)
#         
#                     # Horaire de travail par region
#                     heure_par_jour = 0.0
#                     attendance_ids = employee.calendar_id.attendance_ids
#                     print "attendance_ids ",attendance_ids
#                     date_now = datetime.datetime.strptime(fields.Date().today(),'%Y-%m-%d')
#                     dayofweek = int(datetime.datetime.strptime(str(date_now.date()), '%Y-%m-%d').strftime('%w'))
#                     for attendance_id in attendance_ids:
#                         attendances = self.env['resource.calendar.attendance'].search([['id', '=', attendance_id.id], ['dayofweek', '=', dayofweek]])
#                         for attendance in attendances:
#                             heure_par_jour += attendance.hour_to - attendance.hour_from
#                     
#                     for timestamp in self.datespan(time_from, time_to):
#                         company = employee.company_id
#                         date = timestamp.date()
#                         hours = heure_par_jour
#                         
#                         date_str = str(date)
#                         self.create_leave_analytic_line(holiday, employee, date_str, hours)
#               
                attendance_ids = employee.calendar_id.attendance_ids
                date_from = datetime.datetime.strptime(holiday.date_from,"%Y-%m-%d")
                date_to = datetime.datetime.strptime(holiday.date_to,"%Y-%m-%d")
                    
                d1 = date(date_from.year, date_from.month, date_from.day)  # start date
                d2 = date(date_to.year, date_to.month, date_to.day)  # end date
    
                delta = d2 - d1
                nbjour = 0.5 if holiday.demi_jour == True else 1
                for i in range(delta.days + 1):
                    date_str = (d1 + timedelta(days=i))
                    heure_par_jour = 0.0
                    dayofweek = int(datetime.datetime.strptime(str(date_str), '%Y-%m-%d').strftime('%w'))
                    if not self.verif_day_not_working(str(date_str)) :
                        for attendance_id in attendance_ids:
                            attendances = self.env['resource.calendar.attendance'].search([('id', '=', attendance_id.id), ('dayofweek', '=', dayofweek)])
                            for attendance in attendances:
                                heure_par_jour += attendance.hour_to - attendance.hour_from
                        print "heure_par_jour : ",heure_par_jour
                        print "nbjour : ",nbjour
                        heure_par_jour = heure_par_jour * nbjour
                        account_analytic_line_s = self.env['account.analytic.line'].search([('date', '=', date_str)])
                        for account in account_analytic_line_s :
                            if employee.user_id.id == account.user_id.id:
                                account.write({'unit_amount' : 0.0 })
                        self.create_leave_analytic_line(holiday, employee, date_str, heure_par_jour)
                
                            
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
#                         leaves += self.with_context(mail_notify_force_send=False).create(values) #old
                        leaves += self.with_context(no_mail_to_attendees=True).create(values) #new
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
            
        
        # Send notif Congé
        self._send_mail_validation_conge(self)
        
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
        time_obj = datetime.datetime.strptime(time_string, '%Y-%m-%d')

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
            'user_id': employee.user_id.id
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
   
    def monthdelta(self,d1, d2):
        delta = 0
        while True:
            mdays = monthrange(d1.year, d1.month)[1]
            d1 += timedelta(days=mdays)
            if d1 <= d2:
                delta += 1
            else:
                break
        return delta
    def _increment_doit_conge(self):
        contracts = self.env['hr.contract'].sudo().search([])
        dt_now = datetime.datetime.strptime(fields.Date().today(),'%Y-%m-%d')
        
        for contract in contracts :
            holidays = self.env['hr.holidays'].search([('employee_id','=',contract.employee_id.id),('type','=','add')],order='id')
            if len(holidays) > 0:
                
                dt_write_date = datetime.datetime.strptime(holidays[0].write_date,'%Y-%m-%d %H:%M:%S')
              
                if dt_write_date.month != dt_now.month:
                    number_of_days = holidays[0].nombre_conge + 2 
                    holidays[0].write({'nombre_conge':number_of_days})
                    number_of_days_emp = contract.employee_id.nombre_conge + 2
                    contract.employee_id.write({'nombre_conge':number_of_days_emp})
            elif contract.date_start != False :
                date_start = datetime.datetime.strptime(contract.date_start,'%Y-%m-%d')
                print "delta : ",self.monthdelta(date_start, dt_now)
                if self.monthdelta(date_start, dt_now) >= 1:
                    print contract.employee_id.name
                    holidays_status = self.env['hr.holidays.status'].search([('holidays_status_id_psi','=',2)])
                    values = {
                                    'name': contract.employee_id.name,
                                    'type': 'add',
                                    'state': 'validate',
                                    'holiday_type': 'employee',
                                    'holiday_status_id': holidays_status[0].id,
                                    'nombre_conge': 2,
                                    'employee_id': contract.employee_id.id
                                }
                    self.env['hr.holidays'].create(values)
                    number_of_days_emp = contract.employee_id.nombre_conge + 2
                    contract.employee_id.write({'nombre_conge':number_of_days_emp})

                
     # Send mail - rappel piece justificatif - conge maladie  
    @api.multi 
    def _send_email_rappel_justificatif_conge_maladie(self, automatic=False):
        print "_send_email_rappel_justificatif_conge_maladie"
        
        # Find all congé maladie
        all_holidays = self.env['hr.holidays'].search([('id_psi_holidays_status','=',4),('state','=','validate')])
        print all_holidays
        for holidays in all_holidays:
            date_debut_conge_maladie = holidays.date_from
            print date_debut_conge_maladie,' date_debut'
            dt = datetime.datetime.strptime(date_debut_conge_maladie,'%Y-%m-%d')
            date_y_m_d = datetime.datetime(
                                         year=dt.year, 
                                         month=dt.month,
                                         day=dt.day,
                    )
            date_to_notif = date_y_m_d + relativedelta(hours=72)   
            print date_to_notif.date(),' date_to_notif'
            print datetime.datetime.today().date(),' date_now'
            if date_to_notif.date() == datetime.datetime.today().date() :
                print "Send mail PJ"
                template = self.env.ref('hr_holidays_psi.custom_template_rappel_justificatif_conge_maladie')
                self.env['mail.template'].browse(template.id).send_mail(self.id)               
        if automatic:
            self._cr.commit()

    @api.onchange('holiday_status_id')
    def _onchange_holiday_status_id(self):
        print "_onchange_holiday_status_id"
        
        public_holidays_line = self.env['hr.holidays.public.line'].sudo().search([])
        
        holidays_status_maternite = self.env['hr.holidays.status'].search([('holidays_status_id_psi','=',6)])
        holidays_status_sans_solde = self.env['hr.holidays.status'].search([('holidays_status_id_psi','=',3)])
        holidays_status_conge_annuel = self.env['hr.holidays.status'].search([('holidays_status_id_psi','=',2)])
        date_from = self.date_from
        date_to = self.date_to
        if self.holiday_status_id.id == holidays_status_conge_annuel[0].id:
                self.deduit = True
        else :
                self.deduit = False
        if date_from and date_to:
            
            if self.holiday_status_id.id == holidays_status_maternite[0].id:
                print holidays_status_maternite[0].name
               
                date_to_with_delta = fields.Date.from_string(date_from) + datetime.timedelta(days=97)
                self.date_to = str(date_to_with_delta)
            
                
    #             date_from = datetime.datetime.strptime(date_from, "%Y-%m-%d").date()
    #             date_to = datetime.datetime.strptime(date_to, "%Y-%m-%d").date()
    #         
#             delta = date_to - date_from
#             print delta,' delta'
#             for i in range(delta.days + 1):
#                             current_day=datetime.datetime.strptime(str(date_from + timedelta(days=i)), '%Y-%m-%d').strftime('%w')
#                             print date_from + timedelta(days=i)
#                             print current_day,' JOUR SEMAINE'
#                             if current_day == "6" or current_day == "0" :                                   # VERIFICATION W-END
#                                 print "W-end"
#                                 self.number_of_days_temp += 1
#                             for public_holiday in public_holidays_line:                                     # VERIFICATION JOUR FERIE
#                                 print "JOUR FERIE ",public_holiday.date
#                                 if str(public_holiday.date) == str(date_from + timedelta(days=i)):
#                                     print "OUI JF"
#                                     self.number_of_days_temp += 1
#             print self.number_of_days_temp,' self.number_of_days_temp'
            
            
        # No date_to set so far: automatically compute one 8 hours later
        #if date_from and not date_to:
        #    date_to_with_delta = fields.Date.from_string(date_from) + datetime.timedelta(hours=HOURS_PER_DAY)
        #    self.date_to = str(date_to_with_delta)

        # Compute and update the number of days
        #if (date_to and date_from) and (date_from <= date_to):
        #    self.number_of_days_temp = self._get_number_of_days(date_from, date_to, self.employee_id.id)
        #else:
        #    self.number_of_days_temp = 0
    
    # Mail de rappel aux Assistantes et Coordinateurs
    @api.multi
    def _send_email_rappel_absences_to_assist_and_coord(self, automatic=False):
        print "test cron by send mail rappel"
        today = datetime.datetime.today()
        if today.day == 20:
            template = self.env.ref('hr_holidays_psi.custom_template_absences_to_assist_and_coord')
            self.env['mail.template'].browse(template.id).send_mail(self.id, force_send=force_send)            
        if automatic:
            self._cr.commit()
            
    #@api.constrains('state', 'number_of_days_temp')
    def _check_holidays(self):
        print "_check_holidays"
        holidays_status_formation = self.env['hr.holidays.status'].search([('holidays_status_id_psi','=',5)])
        holidays_status_annuel = self.env['hr.holidays.status'].search([('holidays_status_id_psi','=',2)])
        for holiday in self:
            if holiday.holiday_type != 'employee' or holiday.type != 'remove' or not holiday.employee_id or holiday.holiday_status_id.limit:
              
                continue
            if holidays_status_formation[0].id == holiday.holiday_status_id.id and holidays_status_annuel[0].id == holiday.holiday_status_id.id:
           
                holidays_attribution = self.env['hr.holidays'].search([('employee_id','',holiday.employee_id.id),('type','=','add')])
                leave_days = holidays_attribution[0].holiday_status_id.get_days(holidays_attribution[0].employee_id.id)[holidays_attribution[0].holiday_status_id.id]
                if float_compare(leave_days['nombre_conge'], 0, precision_digits=2) == -1 or \
                  float_compare(leave_days['virtual_remaining_leaves'], 0, precision_digits=2) == -1:
                    raise ValidationError(_('The number of remaining leaves is not sufficient for this leave type.\n'
                                            'Please verify also the leaves waiting for validation.'))
    
    @api.multi
    def action_refuse(self):
        if not self.env.user.has_group('hr_holidays_psi.group_hr_holidays_rh') and not self.env.user.has_group('hr_holidays_psi.group_hr_holidays_spa') and not self.env.user.has_group('hr_holidays_psi.group_hr_holidays_crh') and not self.env.user.has_group('hr_holidays_psi.group_hr_holidays_drha'):
            raise UserError(_('Only an HR Officer or Manager can refuse leave requests.'))
        
        # Send notif Congé
        self._send_mail_refuse_conge(self)
        
        manager = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        for holiday in self:
            if holiday.state not in ['confirm', 'validate', 'validate1', 'validate2', 'approbation']:
                raise UserError(u'Une demande de congé ne peut être refusée si elle a déjà été validée par le Responsable RH ou le DRHA')

            if holiday.state == 'validate1':
#                 holiday.write({'state': 'refuse', 'manager_id': manager.id}) #old
                holiday.write({'state': 'draft', 'manager_id': manager.id}) #new
            else:
#                 holiday.write({'state': 'refuse', 'manager_id2': manager.id}) #old
                holiday.write({'state': 'draft', 'manager_id2': manager.id}) #new
            # Delete the meeting
            if holiday.meeting_id:
                holiday.meeting_id.unlink()
            # If a category that created several holidays, cancel all related
            holiday.linked_request_ids.action_refuse()
        
        self._remove_resource_leave()
        
        
        return True

    # Mail state draft to confirm
    def _send_mail_validation_conge(self, automatic=False):
        template = self.env.ref('hr_holidays_psi.custom_template_validation_conge')
        self.env['mail.template'].browse(template.id).send_mail(self.id, force_send=True)            
        if automatic:
            self._cr.commit()
            
    # Mail refuse congé
    def _send_mail_refuse_conge(self, automatic=False):
        print ' _send_mail_refuse_conge'
        for record in self:
            if record.id:
                template = self.env.ref('hr_holidays_psi.custom_template_refuse_conge')
                self.env['mail.template'].browse(template.id).send_mail(self.id, force_send=True)            
        if automatic:
            self._cr.commit()
        print "end _send_mail_refuse_conge"
            