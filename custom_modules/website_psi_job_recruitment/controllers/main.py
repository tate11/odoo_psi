# -*- coding: utf-8 -*-

from odoo import http

class WebSiteFormRecruitment(http.Controller):
    @http.route('/website_form_applicant/<string:model_name>', type='http', auth="public", methods=['POST'], website=True)
    def website_form(self, model_name, **kwargs):
        