# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import itertools

from __builtin__ import False
import calendar
from datetime import datetime, date
import datetime as dt
from odoo.addons.grid.models import END_OF

from odoo import api, fields, models
from odoo.exceptions import Warning, UserError

class confirm_relance(models.TransientModel):
    _name = 'confirm.send.validation'
 
    yes_no = fields.Char(default='Votre feuille de temps a bien été enregistrée pour validation.')
     
    def yes(self):
        return {
                'type': 'ir.actions.client',
                'tag': 'reload',
        }
         

class ProjectProject(models.Model):
    _inherit = 'project.project'

    project_timesheet_id = fields.Integer()
    
class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'
    
    hours_prestataire_id = fields.Many2one('hr.employee.provider.schedule',string='Heure')
    
    project_timesheet_id = fields.Integer(store=True)
#     project_id = fields.Many2one('project.project', 'Project', domain=lambda self: 
#                                     [
#                                         '|',
#                                           ('id','in', tuple([x.id for x in (
#                                               self.env['project.project'].search([('parent_id','=',
#                                                                                     self.env['project.project'].search([['parent_id','=',False],['analytic_account_id','=',
#                                                                                       self.env['hr.employee'].search([('user_id','=',
#                                                                                          self.env.user.id)])[0].psi_budget_code_distribution.id]])[0].id
#                                                                                    )
#                                                                                   ]
#                                                                                  )
#                                                                             )
#                                                              ]
#                                                             )
#                                            ),
#                                      
#                                            ('id','in', tuple(
#                                             [x.id for x in (
#                                                 self.env['project.project'].search([['parent_id','=',False],['analytic_account_id','=',
#                                                      self.env['hr.employee'].search([('user_id','=',
#                                                          self.env.user.id)])[0].psi_budget_code_distribution.id]])
#                                                 ,)
#                                             ])
#                                           )
#                                      ])
    
#     def relance(self):
#         
#         ctx = dict()
#         ctx.update({
#             'default_job_id':self.id, 
#             'default_model':'confirm.relance',
#             'default_use_template': True,
#             'default_template_id':self.env['ir.model.data'].get_object_reference('hr_recruitment_psi','action_confirm_relance')[1]
#         })
#         
#         view_id=self.env['ir.model.data'].get_object_reference('hr_recruitment_psi','confirm_relance_form')[1]
#         
#         return {
#             'name': 'Confirmation',
#             'domain': [],
#             'res_model': 'confirm.relance',
#             'type': 'ir.actions.act_window',
#             'view_mode': 'form',
#             'view_type': 'form',
#             'views': [(view_id, 'form')],
#             'view_id': view_id,
#             'context': ctx,
#             'target': 'new',
#         }
        
    project_name = fields.Char(related='project_id.name', store=True)
    
    psi_timesheet_type = fields.Selection([('normal', 'Timesheet Normal'),
                                           ('heure_sup', u'Timesheet Heures Supplémentaires'),
                                            ], string="Type")
    
    state = fields.Selection([
        ('draft', u'A soumettre pour validation'),
        ('confirm', u'A valider par le Supérieur hiérarchique'),
        ('refuse', u'Refusé'),
        ('validate', u'Validé par le le Supérieur hiérarchique')
        ], string='Etat', readonly=True, track_visibility='onchange', copy=False, default='draft')
    
    @api.v8
    @api.onchange('product_id', 'product_uom_id', 'unit_amount', 'currency_id')
    def on_change_unit_amount(self):
        print "on_change_unit_amount"

    def _send_email_rappel_envoie_abscence_membres(self, automatic=False):
        this_year = datetime.now().strftime("%Y")
        this_month = datetime.now().strftime("%m")
        last_day_in_this_month = calendar.monthrange(int(this_year), int(this_month))[1] 
        last_day_of_week_in_this_month = datetime.strptime("{}-{}-{}".format(this_year, this_month, last_day_in_this_month), '%Y-%m-%d').strftime('%w')
        nowday_of_week = datetime.now().strftime('%w')
        nowday = datetime.now().strftime('%d')
        
        self.send_rappel_envoie_abscence()
        if last_day_of_week_in_this_month == 6 or last_day_of_week_in_this_month == 0:
            if nowday_of_week == 5:
                self.send_rappel_envoie_abscence()
        else:
            if nowday == last_day_in_this_month:
                self.send_rappel_envoie_abscence()
        
        # Call the next cron in next day 'ouvrable' of next month
        
        this_year = datetime.now().strftime("%Y")
        this_next_month = datetime.now().strftime("%m")
        if this_month == 12:
            this_next_month = "1"
            this_year = int(this_year) + 1
        
        last_day_in_next_month = calendar.monthrange(int(this_year), int(this_next_month))[1] 
        last_day_of_week_in_next_month = datetime.strptime("{}-{}-{}".format(this_year, this_next_month, last_day_in_next_month), '%Y-%m-%d').strftime('%w')
        
        next_day_call_cron = ""
        if last_day_of_week_in_next_month == 6:
            next_day_call_cron = int(last_day_in_next_month) - 1
        elif last_day_of_week_in_next_month == 0:
            next_day_call_cron = int(last_day_in_next_month) - 2
        else:
            next_day_call_cron = last_day_in_next_month
        
        # date_nextcall=datetime.strptime("{}-{}-{} 08:00:00".format(this_year,this_next_month,next_day_call_cron), '%Y-%m-%d %H:%M:%S')
        
        # cron = self.env.ref('hr_timesheet_psi.ir_cron_send_email_rappel_envoie_abscence_membres', raise_if_not_found=False)
        # cron.write({'nextcall':date_nextcall})
        
        # End call the next cron
        if automatic:
            self._cr.commit()
    
    def send_rappel_envoie_abscence(self):
        all_employees = self.env['hr.employee'].search([])
        for employee in all_employees:
            template = self.env.ref('hr_timesheet_psi.custom_template_rappel_envoie_abscence_membres')
            self.env['mail.template'].browse(template.id).send_mail(employee.id, force_send=True)

        
    def _send_email_rappel_timesheet_collaborator(self, automatic=False):
        date = datetime.now()
        day_last_month = calendar.monthrange(date.year,date.month)[1]
        lastBusDay = datetime.today()
        new_lastBusDay = lastBusDay.replace(day=int(day_last_month))
        if new_lastBusDay.weekday() == 5:
            new_lastBusDay = new_lastBusDay - datetime.timedelta(days=1)
        elif new_lastBusDay.weekday() == 6: 
            new_lastBusDay = new_lastBusDay - datetime.timedelta(days=2)
        
        day_last_month = calendar.monthrange(date.year,date.month)[1]
        new_last_day_date = lastBusDay.replace(day=int(day_last_month))
 
        year_mounth = datetime.now().strftime('%Y-%m')
        dateNow = datetime.strptime('2018-01-31', '%Y-%m-%d')
        timesheets = self.env['account.analytic.line'].sudo().search([])
        print dateNow.date(),' == ',new_lastBusDay.date()
        if date.date() == new_lastBusDay.date():
                template = self.env.ref('hr_timesheet_psi.custom_template_rappel_timesheet_collaborator')
                self.env['mail.template'].browse(template.id).send_mail(timesheets[0].id, force_send=True)   
               
        if automatic:
            self._cr.commit()
            

    def float_time_to_time(self, data):
        time = ""
        if len(str(data)) > 2:
            heure, min = str(data).split(".")
            min = str(6 * int(min) / 10)
            if len(str(min)) > 1:
                min = min[:2]
            else:
                min = "{}0".format(min)
            time = "{}h{}".format(heure, min)
        else:
            time = "{}h00".format(data)
            
        return time

    def traiter_unit_amount(self, vals):
        print "traiter_unit_amount"
        unit_amount = vals.get('unit_amount');
        
        if vals.get('project_id'):
            project = self.env['project.project'].browse(vals.get('project_id'))
            vals['account_id'] = project.analytic_account_id.id
        
        if vals.get('date'):
            current_day = datetime.strptime(vals.get('date'), '%Y-%m-%d').strftime('%w')
            if current_day == "6" or current_day == "0" :
                raise Warning('Vous ne devez pas travailler le week-end!')   
                return False
        
#         if vals.get('task_id'):
#             # unit_amount=self.unit_amount
#             tasks = self.env['project.task'].search([('id', '=', vals.get('task_id'))])
#             for task in tasks:
#                 if unit_amount > task.planned_hours:
#                     raise Warning('La durée du Timesheet entrée est supérieure à celle mentionnée dans cette tâche qui est {}!'.format(self.float_time_to_time(task.planned_hours)))  
#                     return False
                
        if len(str(unit_amount)) > 2 and unit_amount != None:
            
            heure, min = str(unit_amount).split(".")
            
            if len(str(min)) > 1:
                min = float("{}.{}".format(min[0], min[1]))
            else:
                min = float(min)
                
            if min < 2.5:
                min = 0
            elif min >= 2.5 and min < 5:
                min = 25
            elif min >= 5 and min < 7.5:
                min = 5
            elif min >= 7.5:
                min = 75
                
            vals['unit_amount'] = float("{}.{}".format(heure, min))

    def modif_val_unit_amount(self, vals):
        print "modif_val_unit_amount"
        unit_amount = vals.get('unit_amount');
        if len(str(unit_amount)) > 2 and unit_amount != None:
            heure, min = str(unit_amount).split(".")
            
            if len(str(min)) > 1:
                min = float("{}.{}".format(min[0], min[1]))
            else:
                min = float(min)
                
            if min < 2.5:
                min = 0
            elif min >= 2.5 and min < 5:
                min = 25
            elif min >= 5 and min < 7.5:
                min = 5
            elif min >= 7.5:
                min = 75
                
            vals['unit_amount'] = float("{}.{}".format(heure, min))
    
    def get_heure_par_jour(self, employees, vals):
        heure_par_jour = 0.0
        for employee in employees:
            attendance_ids = employee.calendar_id.attendance_ids
            for attendance_id in attendance_ids:
                if vals.get('date') :
                    attendances = self.env['resource.calendar.attendance'].search([['id', '=', attendance_id.id], ['dayofweek', '=', datetime.strptime(vals.get('date'), '%Y-%m-%d').strftime('%w')]])
                    for attendance in attendances:
                        heure_par_jour += attendance.hour_to - attendance.hour_from
        return heure_par_jour
    
    def _refresh_grid(self):
        
        ctx = dict()
        ctx.update({
            'default_model':'confirm.refresh.grid',
            'default_use_template': True,
            'default_template_id':self.env['ir.model.data'].get_object_reference('hr_timesheet_psi','action_confirm_refresh_grid')[1]
        })
        
        view_id=self.env['ir.model.data'].get_object_reference('hr_timesheet_psi','confirm.refresh.grid.form')[1]
        
        return {
            'name': 'Confirmation',
            'domain': [],
            'res_model': 'confirm.refresh.grid',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'views': [(view_id, 'form')],
            'view_id': view_id,
            'context': ctx,
            'target': 'new',
        }
        
     # Contrôle week-end et jours fériés
    def verif_day_off(self, date):
        current_day=datetime.strptime(date, '%Y-%m-%d').strftime('%w')
        if current_day == "6" or current_day == "0" :
            raise Warning('Vous ne pouvez pas saisir le week-end.')  
            return False
        
        public_holidays_line = self.env['hr.holidays.public.line'].sudo().search([])
        for public_holiday in public_holidays_line:
            if public_holiday.date == date:
                raise Warning('Vous ne pouvez pas saisir les jours fériés.')
    
                  
    @api.model
    def create(self, vals):
        print "Create"
        if vals.has_key('hours_prestataire_id') :
            print "hours_prestataire_id"
            account_analytic_line_s = {}
            if vals.has_key('date') :
                print "date : ",vals.get('date')
                account_analytic_line_s = self.env['account.analytic.line'].search([('date', '=', vals['date']), ('user_id','=',self.env.user.id)])
            for account in account_analytic_line_s :
                raise Warning(u'Vous ne pouvez saisir qu\'une seule activité par jour (à mi-temps ou à plein temps).')
            hours_prestataire = self.env['hr.employee.provider.schedule'].browse(vals.get('hours_prestataire_id'))
            vals['unit_amount'] = hours_prestataire.hours
            return super(AccountAnalyticLine, self).create(vals)
        
        project_holidays = self.env['project.project'].sudo().search([('name', '=', 'Absences/Permission/Congés')])
        print project_holidays[0],' project_holidays[0]'
        if project_holidays[0].id != vals.get('project_id'):

            self.verif_day_off(vals['date'])
            print "create one"
            total = 0.0
            print vals
            print "date : ", vals['date']
            employees = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)])
            heure_par_jour = self.get_heure_par_jour(employees, vals)
            print "heure_par_jour", heure_par_jour
            print "date", self.date
            unit_amount_old = 0.0
            account_analytic_line_s = self.env['account.analytic.line'].search([('date', '=', vals['date'])])
            for account in account_analytic_line_s :
                if self.env.user.id == account.user_id.id:
                    if vals.get('account_id') :
                        if account.id == vals['account_id']:
                            unit_amount_old = account.unit_amount
                    total += account.unit_amount
            print "total 1 : ", total
            if vals.get('unit_amount'):
                total = (total - unit_amount_old) + vals.get('unit_amount')
                print "total 2 : ", total
                if total > heure_par_jour :
                    #self._refresh_grid()
                    raise Warning(u'Vous ne pouvez pas saisir plus de {} heures sur cette journée'.format(self.float_time_to_time(heure_par_jour)))
                    
                if vals.get('unit_amount') > heure_par_jour :
                    #self._refresh_grid()
                    raise Warning(u'Vous ne pouvez pas saisir plus de {} heures sur cette journée'.format(self.float_time_to_time(heure_par_jour)))
                     
                    if total > heure_par_jour:
                            print total, ' total_planned_hours'
                            print heure_par_jour, ' heure_par_jour'
                            if heure_par_jour == 0.0:
                                    raise Warning('Vous ne pouvez pas travailler aujourd\'hui ou peut-être que vous n\'êtes pas affecté à un horaire de travail!')
                            else:
                                    raise Warning('Vous ne pouvez pas travailler plus de {} aujourd\'hui!'.format(self.float_time_to_time(heure_par_jour)))
                            return False
            
                    self.modif_val_unit_amount(vals)
        return super(AccountAnalyticLine, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.has_key('hours_prestataire_id') :
            print "hours_prestataire_id write"
            hours_prestataire = self.env['hr.employee.provider.schedule'].browse(vals.get('hours_prestataire_id'))
            vals['unit_amount'] = hours_prestataire.hours
            return super(AccountAnalyticLine, self).write(vals)
        if vals.has_key('state') and vals.get('state') == 'confirm':
            print vals.get('state')
            print vals
            return super(AccountAnalyticLine, self).write(vals)
        self.verif_day_off(self.date)
        print "write  account.analytic.line"
        total = 0.0
        print self.date
        
        vals_emp = { 'date' : self.date}
        employees = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)])
        heure_par_jour = self.get_heure_par_jour(employees, vals_emp)
        print "heure_par_jour", heure_par_jour
        print "date", self.date
        account_analytic_line_s = self.env['account.analytic.line'].search([('date', '=', self.date)])
        for account in account_analytic_line_s :
            if self.env.user.id == account.user_id.id:
                total += account.unit_amount
        print "total 1 : ", total
#         if vals.get('task_id'):
#             unit_amount = self.unit_amount
#             tasks = self.env['project.task'].search([('id', '=', vals.get('task_id'))])
#             for task in tasks:
#                 if unit_amount > task.planned_hours:
#                     raise Warning('La durée du Timesheet entrée est supérieure à celle mentionnée dans cette tâche qui est {}!'.format(self.float_time_to_time(task.planned_hours)))  
#                     return False
            
        if vals.get('unit_amount'):
            total = (total - self.unit_amount) + vals.get('unit_amount')
            print "total 2 : ", total
            if total > heure_par_jour :
                raise Warning(u'Le nombre d\'heure pour cette tâche dépasse de {}'.format(self.float_time_to_time(heure_par_jour)))
                return False
            if vals.get('unit_amount') > heure_par_jour :
                raise Warning(u'Le nombre d\'heure pour cette tâche dépasse de {}'.format(self.float_time_to_time(heure_par_jour)))
                return False
            print "UNIT AMOUNT : ", vals.get('unit_amount')
            employees = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)])
            heure_par_jour = 0.0
            for employee in employees:
                attendance_ids = employee.calendar_id.attendance_ids
                for attendance_id in attendance_ids:
                    attendances = self.env['resource.calendar.attendance'].search([['id', '=', attendance_id.id], ['dayofweek', '=', datetime.strptime(self.date, '%Y-%m-%d').strftime('%w')]])
                    for attendance in attendances:
                        heure_par_jour += attendance.hour_to - attendance.hour_from
            
            print "heure_par_jour", heure_par_jour
            
            if vals.get('unit_amount') > heure_par_jour :
                raise Warning('Vous ne pouvez pas travailler plus de {} aujourd\'hui!'.format(self.float_time_to_time(heure_par_jour)))
                return False

                    
       # self.traiter_unit_amount(vals)
        
        return super(AccountAnalyticLine, self).write(vals)
    
    def send_to_validate(self):
       for record in self:
         if record.date != False :
            timesheets = self.env['account.analytic.line'].search([('date', '=', record.date),('user_id', '=', self.env.user.id)])
            if len(timesheets) > 0 and timesheets[0].state == 'confirm':
                raise Warning("Votre feuille de temps a déjà été enregistrée pour validation.")
                return False
                
            date = datetime.strptime(record.date,'%Y-%m-%d')
            year = date.year
            month = date.month
            day = date.day
            num_days = calendar.monthrange(year, month)[1]
            days = [dt.date(year, month, day) for day in range(1, num_days+1)]
            employees = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)])
            attendance_ids = {}
            if len(employees) > 0 :
                attendance_ids = employees[0].calendar_id.attendance_ids
            for day in days :
                if not self.verif_day_not_working(str(day)) :
                    print day
                    heure_par_jour = 0.0
                    dayofweek = int(datetime.strptime(str(day), '%Y-%m-%d').strftime('%w'))
                    for attendance_id in attendance_ids:
                            attendances = self.env['resource.calendar.attendance'].search([('id', '=', attendance_id.id), ('dayofweek', '=', dayofweek)])
                            for attendance in attendances:
                                heure_par_jour += attendance.hour_to - attendance.hour_from
                    timesheets = self.env['account.analytic.line'].search([('date', '=', day),('user_id', '=', self.env.user.id)])
                    if len(timesheets) == 0 :
                        raise Warning('Veuillez vous assurer que votre feuille de temps est rempli correctement avant d\'enregistrer pour validation.')
                        return False
                    unit_amount_total = 0.0 
                    for account in timesheets :
                        unit_amount_total += account.unit_amount
                    
                    if unit_amount_total != heure_par_jour :
                        raise Warning('Veuillez vous assurer que votre feuille de temps est rempli correctement avant d\'enregistrer pour validation.')
                        return False
                    for timesheet in timesheets :
                        timesheet.sudo().write({'state' : 'confirm'})
                    
                timesheets_update = self.env['account.analytic.line'].search([('date', '=', date),('user_id', '=', self.env.user.id)])
                if len(timesheets_update) > 0 and timesheets_update[0].state == 'confirm' :
                   template = self.env.ref('hr_timesheet_psi.email_for_timesheet_to_validate')
                   self.env['mail.template'].browse(template.id).send_mail(employees[0].id, force_send=True)
                   ctx = dict()
                   ctx.update({
                               'default_model':'confirm.send.validation',
                               'default_use_template': True,
                                'default_template_id':self.env['ir.model.data'].get_object_reference('hr_timesheet_psi','action_confirm_send_validation')[1]
                                })
         
                   view_id=self.env['ir.model.data'].get_object_reference('hr_timesheet_psi','confirm_send_validation')[1]
         
                   return {
                                'name': 'Confirmation',
                                'domain': [],
                                'res_model': 'confirm.send.validation',
                                'type': 'ir.actions.act_window',
                                'view_mode': 'form',
                                'view_type': 'form',
                                'views': [(view_id, 'form')],
                                'view_id': view_id,
                                'context': ctx,
                                'target': 'new',
                                }
       else :
            raise Warning('Veuillez vous assurer que votre feuille de temps est rempli correctement avant d\'enregistrer pour validation.')
            return False      
        
                
    def verif_day_not_working(self, date):
        print "Verification +"
        current_day = datetime.strptime(date, '%Y-%m-%d').strftime('%w')
        if current_day == "6" or current_day == "0" :
            return True
        
        public_holidays_line = self.env['hr.holidays.public.line'].sudo().search([])
        for public_holiday in public_holidays_line:
            if public_holiday.date == date:
                return True
        return False
       
    @api.multi
    def validate(self):
        print 'Validate'
        if not self:
            raise Warning("Il n'y a pas de feuilles de temps à valider.")

        employees = self.mapped('user_id.employee_ids')
        analytic_ids = self.mapped('id')

        for employee in employees:
            for analytic_id in analytic_ids:
                timesheets = self.env['account.analytic.line'].sudo().search([('id','=',analytic_id)])
                for timesheet in timesheets :
                    timesheet.sudo().write({'state' : 'validate'})
        
          
     