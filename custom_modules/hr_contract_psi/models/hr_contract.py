# -*- coding: utf-8 -*-

from odoo import fields, models, api

import smtplib

class HrContract(models.Model):
    
    _inherit        = "hr.contract"
    _name           = "hr.contract"
    place_of_work   = fields.Char(string='Lieu d\'affectaction') #lieu d'affectation
    contract_id     = 0
    state_of_work   = fields.Selection([
        ('cdd', 'CDD'),
        ('cdi', 'CDI')
     ], string='Statut')        
    
    def send_email_collaborator(self):
        print "The id contract is : ",self.contract_id
        template = self.env.ref('hr_contract_psi.custom_template_id')
        self.env['mail.template'].browse(template.id).send_mail(11)
    
    @api.one
    @api.constrains('state_of_work')
    def _check_state_of_work(self):
        for record in self:
            self.contract_id = record.id
       
        cron = self.env['ir.cron'].browse(9)
        cron.write({'active':True})
        cron.active = True
        cron.sudo(user=1)._callback(cron.model, cron.function, cron.args, cron.id)        
        cron.write({'active':False})
        
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