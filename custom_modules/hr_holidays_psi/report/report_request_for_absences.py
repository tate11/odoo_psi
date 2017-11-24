# -*- coding: utf-8 -*-

from odoo import api, models

class report_request_for_absences(models.AbstractModel):
    _name = 'report.hr_holidays_psi.report_request_for_absences'
   
   
    def _get_all_absences(self, employee_id):
        return self.env['hr.holidays'].search([('employee_id', '=', employee_id),('type','=','remove')])
    
    @api.multi
    def render_html(self, docids, data=None):
        
        docargs = {
            'doc_ids': docids,
            'doc_model': 'hr.holidays',
            'docs': self.env['hr.holidays'].browse(docids),
            'get_absences': self._get_all_absences,
            'data': data,
        }
        return self.env['report'].render('hr_holidays_psi.report_request_for_absences', docargs)