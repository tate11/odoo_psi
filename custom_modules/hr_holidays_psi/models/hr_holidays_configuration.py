# -*- coding: utf-8 -*-

from odoo import models, fields, api

class hr_holidays_holidays(models.Model):
    
    _name = "hr.holidays.configuration"
    
    droit_conge = fields.Integer(string=u'Droits aux congés (en mois)')
    conges_sans_solde = fields.Integer(string=u'Congés sans soldes')