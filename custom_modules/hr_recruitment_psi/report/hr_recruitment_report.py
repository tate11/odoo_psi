# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools
from odoo.addons.hr_recruitment.models import hr_recruitment


class HrRecruitmentReportPsi(models.Model):
    
    _inherit = 'hr.recruitment.report'
    _order = 'date_create desc'

    sexe = fields.Selection([
        ('masculin', 'Masculin'),
        ('feminin', u'Féminin')
     ], string='Sexe', readonly=True)
    
    age_avg = fields.Float(u"Age moyen des recrutés", group_operator="avg", digits=0)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'hr_recruitment_report')
        self._cr.execute("""
            create or replace view hr_recruitment_report as (
                 select
                     min(s.id) as id,
                     s.active,
                     s.create_date as date_create,
                     date(s.date_closed) as date_closed,
                     s.date_last_stage_update as date_last_stage_update,
                     s.partner_id,
                     s.company_id,
                     s.user_id,
                     s.job_id,
                     s.type_id,
                     s.department_id,
                     s.priority,
                     s.stage_id,
                     s.last_stage_id,
                     s.medium_id,
                     s.source_id,
                     s.sexe,
                     (sum(age)/count(*)) as age_avg,
                     sum(salary_proposed) as salary_prop,
                     (sum(salary_proposed)/count(*)) as salary_prop_avg,
                     sum(salary_expected) as salary_exp,
                     (sum(salary_expected)/count(*)) as salary_exp_avg,
                     extract('epoch' from (s.write_date-s.create_date))/(3600*24) as delay_close,
                     count(*) as nbr
                 from hr_applicant s
                 group by
                     s.active,
                     s.date_open,
                     s.create_date,
                     s.write_date,
                     s.date_closed,
                     s.date_last_stage_update,
                     s.partner_id,
                     s.company_id,
                     s.user_id,
                     s.stage_id,
                     s.last_stage_id,
                     s.type_id,
                     s.priority,
                     s.job_id,
                     s.department_id,
                     s.medium_id,
                     s.source_id,
                     s.sexe
            )
        """)
