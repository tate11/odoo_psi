# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError
import smtplib

class HrContract(models.Model):
    
    _inherit        = "hr.contract"
    _name           = "hr.contract"
    place_of_work   = fields.Char(string='Lieu d\'affectaction') #lieu d'affectation
    
    state_of_work   = fields.Selection([
        ('cdd', 'CDD'),
        ('cdi', 'CDI')
     ], string='Statut')
     
    @api.model
    def create(self, values):
        res_id = super(hr_contract, self).create(values)
        if values['state_of_work'] == 'cdd' and values['date_end'] == None :
                return
        return res_id           
    
    
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