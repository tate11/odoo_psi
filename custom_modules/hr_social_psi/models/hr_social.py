# -*- coding: utf-8 -*-

from odoo import models,fields
from datetime import date

class Hr_sinitre_individuel(models.Model):
    _name = "hr.sinitre_individuel"
    
    name = fields.Char(string='Description')
    date = fields.Date(string='Date de la demande', default=date.today().strftime('%Y-%m-%d'), required=True)
    employee_id = fields.Many2one('hr.employee', string='Demandeur', required=True)
    state = fields.Selection([
        ('draft', 'Nouveau'),
        ('controlled', u'Controlé'),
        ('pending', 'Envoyé auprès de l\'assurance'),
        ('waiting', 'En attente de remboursement'),
        ('following', 'Remboursement suivi'),
        ('check_collected', u'Chèques collectés'),
        ('check_handed', u'Chèques remis'),
        ], string='Etat', readonly=True, default='draft', track_visibility='onchange')
