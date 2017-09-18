# -*- coding: utf-8 -*-

from odoo import models,fields

class HrAppraisal(models.Model):
    _inherit = "hr.appraisal"

    state = fields.Selection([
        ('new', 'To Start'),
        ('pending', 'Appraisal Sent'),
        ('formation', 'Formation'),
        ('bonus', 'Bonus'),
        ('cancel', "Cancelled"),
        ('done', "Done")
    ], string='Status', track_visibility='onchange', required=True, readonly=True, copy=False, default='new', index=True)
    
    def action_formation(self):
        self.write({'state': 'formation'})
    
    def action_bonus(self):
        self.write({'state': 'bonus'})