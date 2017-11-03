# -*- coding: utf-8 -*-

import werkzeug

import odoo.http as http

from odoo.http import request

class ContractController(http.Controller):

    @http.route('/contract_psi/renouveller', type='http', auth="public")
    def renouveller(self,id,**kwargs):
         result = ''
         menu = request.env['ir.model.data'].get_object_reference('hr', 'menu_hr_root')
         result += '#id=' + str(id) + '&view_type=form&model=hr.contract&menu_id=' + str(menu[1])
         return werkzeug.utils.redirect('/web%s' %(result))
    
    @http.route('/contract_psi/nouveau', type='http', auth="public")
    def nouveau(self,**kwargs):
         result = ''
         menu = request.env['ir.model.data'].get_object_reference('hr', 'menu_hr_root')
         result += '#id=' + str(id) + '&view_type=form&model=hr.contract&menu_id=' + str(menu[1])
         return werkzeug.utils.redirect('/web%s' %(result))