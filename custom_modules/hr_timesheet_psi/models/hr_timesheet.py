# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from datetime import datetime
from odoo.exceptions import Warning
from __builtin__ import False

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'
    
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
            current_timesheets=self.env['account.analytic.line'].search([['project_id','=',self.project_id.id],['task_id','=',self.task_id.id]])
            for current_timesheet in current_timesheets:
                total_planned_hours+=float(current_timesheet.unit_amount)
            if (total_planned_hours+unit_amount-self.unit_amount)>self.task_id.planned_hours:
                raise Warning(u'Il ne reste plus que {} de travail dans cette tâche'.format(self.float_time_to_time(self.task_id.planned_hours-total_planned_hours)))   
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