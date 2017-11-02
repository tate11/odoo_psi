# -*- coding: utf-8 -*-

from odoo import api, models

class report_certificat_travail(models.AbstractModel):
    _name = 'hr.contract_psi.report_certificat_travail'
   
    @api.multi
    def render_html(self, docids, data=None):
        #=======================================================================
        # self.model = self.env.context.get('active_model')
        # docs = self.env[self.model].browse(self.env.context.get('active_ids', []))
        #=======================================================================
        
        docargs = {
            'doc_ids': docids,
            'doc_model': 'hr.contract',
            'docs': self.env['hr.contract'].browse(docids),
            'data': data,
        }
        return self.env['report'].render('hr.contract_psi.report_certificat_travail', docargs)