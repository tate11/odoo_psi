# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http, _
from odoo.addons.website.models.website import slug
from odoo.http import request


class WebsiteHrRecruitment(http.Controller):

    @http.route('/jobs/form/<model("hr.job"):job>', type='http', auth="public", website=True)
    def jobs_apply(self, job, **kwargs):
        error = {}
        default = {}
        
        parent_information_employees = http.request.env['hr.recruitement.parent.information'].sudo().search([])
        
        if 'website_hr_recruitment_error' in request.session:
            error = request.session.pop('website_hr_recruitment_error')
            default = request.session.pop('website_hr_recruitment_default')
        return request.render("website_hr_recruitment.apply", {
            'job': job,
            'parent_information_employees': parent_information_employees,
            'error': error,
            'default': default,
        })
