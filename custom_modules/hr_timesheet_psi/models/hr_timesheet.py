# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from datetime import datetime, date
from odoo.exceptions import Warning
import calendar
from __builtin__ import False


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'
    

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
        unit_amount=vals.get('unit_amount');
        
        if unit_amount>self.task_id.planned_hours:
            raise Warning('La durée du Timesheet entrée est supérieure à celle mentionnée dans la tâche actuelle qui est {}!'.format(self.float_time_to_time(self.task_id.planned_hours)))   
            return False
        
        if unit_amount>self.unit_amount:
            total_planned_hours=0
            current_timesheets=self.env['account.analytic.line'].search([('project_id','=',self.project_id),('task_id','=',self.task_id)])
            for current_timesheet in current_timesheets:
                total_planned_hours+=float(current_timesheet.unit_amount)
            if (total_planned_hours+unit_amount-self.unit_amount)>self.task_id.planned_hours:
                raise Warning(u'Il ne reste plus que {} de travail dans cette tâche'.format(self.float_time_to_time(self.task_id.planned_hours-total_planned_hours)))   
                return False
        
        if unit_amount>=8.5:
            raise Warning('Veuillez entrer une durée inférieure à 8h30!')   
            return False
        
        if len(str(unit_amount))>2:
            
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
                
    @api.model
    def create(self, vals): 
        if vals.get('project_id'):
            project = self.env['project.project'].browse(vals.get('project_id'))
            vals['account_id'] = project.analytic_account_id.id
        if vals.get('date'):
            current_day=datetime.strptime(vals.get('date'), '%Y-%m-%d').strftime('%w')
            if current_day == "6" or current_day == "0" :
                raise Warning('Vous ne devez pas travailler le week-end!')   
                return False
        
        if vals.get('task_id'):
            unit_amount=self.unit_amount
            tasks=self.env['project.task'].search([('id','=',vals.get('task_id'))])
            for task in tasks:
                if unit_amount>task.planned_hours:
                    raise Warning('La durée du Timesheet entrée est supérieure à celle mentionnée dans cette tâche qui est {}!'.format(self.float_time_to_time(task.planned_hours)))   
                    return False
            
        self.traiter_unit_amount(vals)
        return super(AccountAnalyticLine, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('project_id'):
            project = self.env['project.project'].browse(vals.get('project_id'))
            vals['account_id'] = project.analytic_account_id.id
        
        if vals.get('date'):
            current_day=datetime.strptime(vals.get('date'), '%Y-%m-%d').strftime('%w')
            if current_day == "6" or current_day == "0" :
                raise Warning('Vous ne devez pas travailler le week-end!')   
                return False
            
        if vals.get('task_id'):
            unit_amount=self.unit_amount
            tasks=self.env['project.task'].search([('id','=',vals.get('task_id'))])
            for task in tasks:
                if unit_amount>task.planned_hours:
                    raise Warning('La durée du Timesheet entrée est supérieure à celle mentionnée dans cette tâche qui est {}!'.format(self.float_time_to_time(task.planned_hours)))  
                    return False
            
        if vals.get('unit_amount'):
            employees=self.env['hr.employee'].search([('id','=',self.user_id.id)])
            heure_par_jour=8.5
            print "eto"
            for employee in employees:
                attendance_ids=employee.calendar_id.attendance_ids
                for attendance_id in attendance_ids:
                    attendances=self.env['resource.calendar.attendance'].search([['id','=',attendance_id.id],['dayofweek','=',datetime.strptime(self.date, '%Y-%m-%d').strftime('%w')]])
                    for attendance in attendances:
                        heure_par_jour+=attendance.hour_to-attendance.hour_from
            
            if vals.get('unit_amount')>heure_par_jour:
                raise Warning('Vous ne pouvez pas travailler plus de {} aujourd\'hui!'.format(self.float_time_to_time(heure_par_jour)))
                return False
            
            self.traiter_unit_amount(vals)
        return super(AccountAnalyticLine, self).write(vals)