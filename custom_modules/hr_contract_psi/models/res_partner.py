# -*- encoding: utf-8 -*-
from odoo import models, fields, api

class res_partner(models.Model):
    _inherit = 'res.partner'
    _name    = 'res.partner'

    
    def send_mail_template(self):
        entretien_send_email = self.env.ref('hr_contract_psi.custom_template_id')
        if entretien_send_email:
            entretien_send_email.sudo().with_context().send_mail(3, force_send=True)