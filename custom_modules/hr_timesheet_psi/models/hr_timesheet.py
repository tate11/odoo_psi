# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from __builtin__ import False
import calendar
from datetime import datetime, date

from odoo import api, fields, models
from odoo.exceptions import Warning


class ProjectProject(models.Model):
    _inherit = 'project.project'

    project_timesheet_id = fields.Integer()
    
class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

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
    
    @api.v8
    @api.onchange('product_id', 'product_uom_id', 'unit_amount', 'currency_id')
    def on_change_unit_amount(self):
        print "on_change_unit_amount"

    def _send_email_rappel_envoie_abscence_membres(self, automatic=False):
        this_year=datetime.now().strftime("%Y")
        this_month=datetime.now().strftime("%m")
        last_day_in_this_month= calendar.monthrange(int(this_year),int(this_month))[1] 
        last_day_of_week_in_this_month= datetime.strptime("{}-{}-{}".format(this_year,this_month,last_day_in_this_month), '%Y-%m-%d').strftime('%w')
        nowday_of_week=datetime.now().strftime('%w')
        nowday=datetime.now().strftime('%d')
        
        self.send_rappel_envoie_abscence()
        if last_day_of_week_in_this_month==6 or last_day_of_week_in_this_month==0:
            if nowday_of_week==5:
                self.send_rappel_envoie_abscence()
        else:
            if nowday==last_day_in_this_month:
                self.send_rappel_envoie_abscence()
        
        #Call the next cron in next day 'ouvrable' of next month
        
        this_year=datetime.now().strftime("%Y")
        this_next_month=datetime.now().strftime("%m")
        if this_month==12:
            this_next_month="1"
            this_year=int(this_year)+1
        
        last_day_in_next_month= calendar.monthrange(int(this_year),int(this_next_month))[1] 
        last_day_of_week_in_next_month= datetime.strptime("{}-{}-{}".format(this_year,this_next_month,last_day_in_next_month), '%Y-%m-%d').strftime('%w')
        
        next_day_call_cron=""
        if last_day_of_week_in_next_month==6:
            next_day_call_cron=int(last_day_in_next_month)-1
        elif last_day_of_week_in_next_month==0:
            next_day_call_cron=int(last_day_in_next_month)-2
        else:
            next_day_call_cron=last_day_in_next_month
        
        #date_nextcall=datetime.strptime("{}-{}-{} 08:00:00".format(this_year,this_next_month,next_day_call_cron), '%Y-%m-%d %H:%M:%S')
        
        #cron = self.env.ref('hr_timesheet_psi.ir_cron_send_email_rappel_envoie_abscence_membres', raise_if_not_found=False)
        #cron.write({'nextcall':date_nextcall})
        
        # End call the next cron
        if automatic:
            self._cr.commit()
    
    def send_rappel_envoie_abscence(self):
        all_employees = self.env['hr.employee'].search([])
        for employee in all_employees:
            template = self.env.ref('hr_timesheet_psi.custom_template_rappel_envoie_abscence_membres')
            self.env['mail.template'].browse(template.id).send_mail(employee.id,force_send=True)
                    
    def _send_email_rappel_timesheet_collaborator(self, automatic=False):
        year_mounth=datetime.now().strftime('%Y-%m')
        all_employees = self.env['hr.employee'].search([('job_id.recrutement_type','=','collaborateur')])
        for employee in all_employees:
            timesheets = self.env['account.analytic.line'].search([['user_id','=',employee.id],['date','like',year_mounth]])
            if not timesheets:
                template = self.env.ref('hr_timesheet_psi.custom_template_rappel_timesheet_collaborator')
                self.env['mail.template'].browse(template.id).send_mail(employee.id,force_send=True)
        
        if automatic:
            self._cr.commit()
            

    def float_time_to_time(self,data):
        time=""
        if len(str(data))>2:
            heure,min=str(data).split(".")
            min=str(6*int(min)/10)
            if len(str(min))>1:
                min=min[:2]
            else:
                min="{}0".format(min)
            time="{}h{}".format(heure,min)
        else:
            time="{}h00".format(data)
            
        return time

    def traiter_unit_amount(self,vals):
        print "traiter_unit_amount"
        unit_amount=vals.get('unit_amount');
        
        if vals.get('project_id'):
            project = self.env['project.project'].browse(vals.get('project_id'))
            vals['account_id'] = project.analytic_account_id.id
        
        if vals.get('date'):
            current_day=datetime.strptime(vals.get('date'), '%Y-%m-%d').strftime('%w')
            if current_day == "6" or current_day == "0" :
                raise Warning('Vous ne devez pas travailler le week-end!')   
                return False
        
        if vals.get('task_id'):
            #unit_amount=self.unit_amount
            tasks = self.env['project.task'].search([('id', '=', vals.get('task_id'))])
            for task in tasks:
                if unit_amount>task.planned_hours:
                    raise Warning('La durée du Timesheet entrée est supérieure à celle mentionnée dans cette tâche qui est {}!'.format(self.float_time_to_time(task.planned_hours)))  
                    return False
                
        if len(str(unit_amount))>2 and unit_amount != None:
            
            heure,min=str(unit_amount).split(".")
            
            if len(str(min))>1:
                min=float("{}.{}".format(min[0],min[1]))
            else:
                min=float(min)
                
            if min<2.5:
                min=0
            elif min>=2.5 and min<5:
                min=25
            elif min>=5 and min<7.5:
                min=5
            elif min>=7.5:
                min=75
                
            vals['unit_amount']=float("{}.{}".format(heure,min))

    def modif_val_unit_amount(self, vals):
        print "modif_val_unit_amount"
        unit_amount=vals.get('unit_amount');
        if len(str(unit_amount))>2 and unit_amount != None:
            heure,min=str(unit_amount).split(".")
            
            if len(str(min))>1:
                min=float("{}.{}".format(min[0],min[1]))
            else:
                min=float(min)
                
            if min<2.5:
                min=0
            elif min>=2.5 and min<5:
                min=25
            elif min>=5 and min<7.5:
                min=5
            elif min>=7.5:
                min=75
                
            vals['unit_amount']=float("{}.{}".format(heure,min))
    
    def get_heure_par_jour(self, employees,vals):
        heure_par_jour = 0.0
        for employee in employees:
            attendance_ids = employee.calendar_id.attendance_ids
            for attendance_id in attendance_ids:
                if vals.get('date') :
                    attendances = self.env['resource.calendar.attendance'].search([['id', '=', attendance_id.id], ['dayofweek', '=', datetime.strptime(vals.get('date'), '%Y-%m-%d').strftime('%w')]])
                    for attendance in attendances:
                        heure_par_jour += attendance.hour_to - attendance.hour_from
        return heure_par_jour

    # Contrôle week-end et four férié
    def verif_day_off(self, date):
        current_day=datetime.strptime(date, '%Y-%m-%d').strftime('%w')
        print current_day,' JOUR'
        if current_day == "6" or current_day == "0" :
            raise Warning('Vous ne pouvez pas saisir le week-end.')   
            return False
        
        public_holidays_line = self.env['hr.holidays.public.line'].sudo().search([])
        for public_holiday in public_holidays_line:
            if public_holiday.date == date:
                raise Warning('Vous ne pouvez pas saisir le jour ferié.') 
                    
    @api.model
    def create(self, vals):
        print "create one"
        total = 0.0
        print vals
        print "date : ",vals['date']
        employees = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)])
        heure_par_jour = self.get_heure_par_jour(employees, vals)
        print "heure_par_jour", heure_par_jour
        print "date", self.date
        unit_amount_old = 0.0
        account_analytic_line_s = self.env['account.analytic.line'].search([('date', '=', vals['date'])])
        for account in account_analytic_line_s :
            if account.id == vals['account_id']:
                unit_amount_old = account.unit_amount
            if self.env.user.id == account.user_id.id:
                total += account.unit_amount
        print "total 1 : ",total
        if vals.get('unit_amount'):
            total = ( total - unit_amount_old ) + vals.get('unit_amount')
            print "total 2 : ",total
            if total > heure_par_jour :
                raise Warning(u'Le nombre d\'heure pour cette tâche dépasse de {}'.format(self.float_time_to_time(heure_par_jour)))
                return False
            if vals.get('unit_amount') > heure_par_jour :
                raise Warning(u'Le nombre d\'heure pour cette tâche dépasse de {}'.format(self.float_time_to_time(heure_par_jour)))
                return False
        project_holidays = self.env['project.project'].sudo().search([('name','=','Absences/Permission/Conges')])
        if project_holidays[0].id != vals.get('project_id'):
            print vals.get('task_id')
            print vals.get('date'),' DATE'
            print vals.get('project_id'),' ID PROJET'
            print vals.get('unit_amount')
            
            if vals.get('date') and vals.get('project_id') and vals.get('unit_amount'):
                print 'IF 1'
                self.verif_day_off(vals.get('date'))
                
                
                current_timesheets = self.env['account.analytic.line'].search([('project_id', '=', vals.get('project_id')),('task_id', '=', vals.get('task_id'))])
                task = self.env['project.task'].search([('id','=',vals.get('task_id'))])[0]
                total_planned_hours = 0
                for current_timesheet in current_timesheets:
                        total_planned_hours += float(current_timesheet.unit_amount)
                    
                total_planned_hours += vals.get('unit_amount')
                        
                    #if total_planned_hours > task.planned_hours:
                    #    raise Warning(u'Le nombre d\'heure pour cette tâche dépasse de {}'.format(self.float_time_to_time(total_planned_hours - task.planned_hours ))) 
                    #    return False
        
                if vals.get('unit_amount') > task.planned_hours:
                        raise Warning('La durée du Timesheet entrée est supérieure à celle mentionnée dans cette tâche qui est {}!'.format(self.float_time_to_time(task.planned_hours)))   
                        return False
        
                current_timesheets = self.env['account.analytic.line'].search([('date', '=', vals.get('date')),('user_id', '=', self.env.user.id)])
                total_planned_hours = 0
                for current_timesheet in current_timesheets:
                        total_planned_hours += float(current_timesheet.unit_amount)
                    
                total_planned_hours += vals.get('unit_amount')
        
                employees = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)])
                    
                heure_par_jour=self.get_heure_par_jour(employees,vals)
                
                if total_planned_hours>heure_par_jour:
                        print total_planned_hours,' total_planned_hours'
                        print heure_par_jour, ' heure_par_jour'
                        if heure_par_jour==0.0:
                                raise Warning('Vous ne pouvez pas travailler aujourd\'hui ou peut-être que vous n\'êtes pas affecté à un horaire de travail!')
                        else:
                                raise Warning('Vous ne pouvez pas travailler plus de {} aujourd\'hui!'.format(self.float_time_to_time(heure_par_jour)))
                        return False
        
                self.modif_val_unit_amount(vals)
                       
                    
            
#             if vals.get('project_id') and vals.get('unit_amount') and vals.get('unit_amount') != 0.0:
#                 print 'IF 2'
#                 current_timesheets = self.env['account.analytic.line'].search([('user_id', '=', self.env.user.id)])
#                 total_planned_hours = 0
#                 for current_timesheet in current_timesheets:
#                     total_planned_hours += float(current_timesheet.unit_amount)
#                 
#                 total_planned_hours += vals.get('unit_amount')
#                 employees = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)])
#                 heure_par_jour=self.get_heure_par_jour(employees,vals)
#     
#                 if vals.get('unit_amount') > heure_par_jour:
#                         if heure_par_jour==0.0:
#                             raise Warning('Vous ne pouvez pas travailler aujourd\'hui ou peut-être que vous n\'êtes pas affecté à un horaire de travail!')
#                         else:
#                             raise Warning('Vous ne pouvez pas travailler plus de {} aujourd\'hui!'.format(self.float_time_to_time(heure_par_jour)))
#                         return False
#     
#                 self.modif_val_unit_amount(vals)
    
        return super(AccountAnalyticLine, self).create(vals)

    @api.multi
    def write(self, vals):
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
        print "total 1 : ",total
        if vals.get('task_id'):
            unit_amount=self.unit_amount
            tasks=self.env['project.task'].search([('id','=',vals.get('task_id'))])
            for task in tasks:
                if unit_amount>task.planned_hours:
                    raise Warning('La durée du Timesheet entrée est supérieure à celle mentionnée dans cette tâche qui est {}!'.format(self.float_time_to_time(task.planned_hours)))  
                    return False
            
        if vals.get('unit_amount'):
            total = ( total - self.unit_amount ) + vals.get('unit_amount')
            print "total 2 : ",total
            if total > heure_par_jour :
                raise Warning(u'Le nombre d\'heure pour cette tâche dépasse de {}'.format(self.float_time_to_time(heure_par_jour)))
                return False
            if vals.get('unit_amount') > heure_par_jour :
                raise Warning(u'Le nombre d\'heure pour cette tâche dépasse de {}'.format(self.float_time_to_time(heure_par_jour)))
                return False
            print "UNIT AMOUNT : ",vals.get('unit_amount')
            employees = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)])
            heure_par_jour = 0.0
            for employee in employees:
                attendance_ids = employee.calendar_id.attendance_ids
                for attendance_id in attendance_ids:
                    attendances = self.env['resource.calendar.attendance'].search([['id', '=', attendance_id.id], ['dayofweek', '=', datetime.strptime(self.date, '%Y-%m-%d').strftime('%w')]])
                    for attendance in attendances:
                        heure_par_jour += attendance.hour_to - attendance.hour_from
            
            print "heure_par_jour", heure_par_jour
            
            if vals.get('unit_amount')>heure_par_jour :
                raise Warning('Vous ne pouvez pas travailler plus de {} aujourd\'hui!'.format(self.float_time_to_time(heure_par_jour)))
                return False
          
#             if vals.get('unit_amount') > self.unit_amount:
#                     print "self.task_id.planned_hours : ",self.task_id.planned_hours
#                     total_planned_hours = 0
#                     current_timesheets = self.env['account.analytic.line'].search([['project_id', '=', self.project_id.id], ['task_id', '=', self.task_id.id]])
#                     for current_timesheet in current_timesheets:
#                         total_planned_hours += float(current_timesheet.unit_amount)
#                         
#                     if (total_planned_hours + vals.get('unit_amount') - self.unit_amount) > self.task_id.planned_hours:
#                         raise Warning(u'Le nombre d\'heure pour cette tâche dépasse de {}'.format(self.float_time_to_time((total_planned_hours + vals.get('unit_amount') - self.unit_amount) - self.task_id.planned_hours)))
#                         return False
                    
        self.traiter_unit_amount(vals)
        
        return super(AccountAnalyticLine, self).write(vals)
