# -*- coding: utf-8 -*-

from odoo import api, models

class report_request_for_absences(models.AbstractModel):
    _name = 'report.hr_holidays_psi.report_unwarranted_absences'
   
   
    def _get_all_absences(self, employee_id):
        holidays_status = self.env['hr.holidays.status'].search([('color_name','=','blue')])
        return self.env['hr.holidays'].search([ [('holiday_status_id','=',holidays_status[0].id)] , [('attachment_number','=',0)] ])
    
    @api.multi
    def render_html(self, docids, data=None):
        
        docargs = {
            'doc_ids': docids,
            'doc_model': 'hr.holidays',
            'docs': self.env['hr.holidays'].browse(docids),
            #'absences': self.env['hr_holidays'].search([('employee_id', '=', self.env['hr.holidays'].browse(docids).employee_id.id)]),
            'get_absences': self._get_all_absences,
            'data': data,
        }
        return self.env['report'].render('hr_holidays_psi.report_unwarranted_absences', docargs)