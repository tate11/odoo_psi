# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from datetime import datetime
from odoo.exceptions import Warning

class hr_timesheet(models.Model):
    _inherit = 'account.analytic.line'
    
    type = fields.Selection([('normal','Timesheet Normal'),
                              ('heure_supp','Timesheet heure supp')
                              ], string="Type de Timesheet", required=True, default='normal')
    
    def traiter_unit_amount(self,vals):
        unit_amount=vals.get('unit_amount');
        if unit_amount>self.task_id.planned_hours:
            raise Warning('Cette durée est supérieure à celle qu\'on a prévue!')   
            return False
        if unit_amount:
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
        self.traiter_unit_amount(vals)
        return super(hr_timesheet, self).create(vals)

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
            total_planned_hours=0
            for task in self.env['project.task'].browse(vals.get('task_id')):
                total_planned_hours+=float(task.planned_hours)
            raise Warning(total_planned_hours)
            
        self.traiter_unit_amount(vals)
        return super(hr_timesheet, self).write(vals)