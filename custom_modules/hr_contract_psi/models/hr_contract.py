# -*- coding: utf-8 -*-

from odoo import fields, models, api

import smtplib

class HrContract(models.Model):
    
    _inherit        = "hr.contract"
    _name           = "hr.contract"
    place_of_work   = fields.Char(string='Lieu d\'affectaction') #lieu d'affectation
    
    state_of_work   = fields.Selection([
        ('cdd', 'CDD'),
        ('cdi', 'CDI')
     ], string='Statut')        
    
    def send_email_collaborator(self):
        template = self.env.ref('hr_contract_psi.custom_template_id')
        self.env['mail.template'].browse(template.id).send_mail(self.id)
    
   # @api.multi
   # def create(self, vals = {}):
   #     cron = self.pool.get('ir.cron')
   #     crons = cron.search([['name', '=', 'send_email_one_collaborator'],['active','=',False]])
   #     res = super(HrContract, self).write(vals)
   #     self.id = res['id']
   #     for cron in crons :
   #         self.sudo(user=1)._callback(cron.model, cron.function, cron.args, cron.id)
   #     return res
    
    def send_email(self):
        sender = 'xxxxx@gmail.com'
        receivers = 'arandriamoravelo@ingenosya.mg'
        
        message = "Bonjour, Veuillez contacter PSI s'il vous plait."
        
        smtpObj = smtplib.SMTP('smtp.gmail.com', 587)
        smtpObj.ehlo()
        smtpObj.starttls()
        smtpObj.ehlo()
        smtpObj.login('xxxxx@gmail.com', password='xxxx')
        smtpObj.sendmail(sender, receivers, message)         
        print "Successfully sent email"