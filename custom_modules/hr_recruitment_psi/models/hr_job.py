# -*- coding: utf-8 -*-

from odoo import fields, models

class hr_job(models.Model):
    
    _inherit = "hr.job"
    name = fields.Char(size=28)
    
    state = fields.Selection([
        ('open', 'Demande d\'embauche'),
        ('analyse', 'Analyse de la demande'),
        ('rr_validation', 'Approbation par RR'),
        ('tdr_redaction', 'Rédaction TDR'),
        ('refused', 'Refusé'),
        ('recruit', 'Appel aux candidatures')
    ], string='Status', readonly=True, required=True, track_visibility='always', copy=False, default='open', help="Set whether the recruitment process is open or closed for this job position.")
    
    recrutement_type_id = fields.Many2one('hr.recruitment.type', string='Type de recrutement',required=True)
    recrutement_type = fields.Selection(related='recrutement_type_id.recrutement_type',string='Type de recrutement selection')
    
#     def set_recruit(self):
#         for record in self:
#             no_of_recruitment = 1 if record.no_of_recruitment == 0 else record.no_of_recruitment
#             record.signal_workflow('button_relance')
#             record.write({'state': 'open', 'no_of_recruitment': no_of_recruitment})
#         return True