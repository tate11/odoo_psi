# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class Calendar(models.Model):

    _inherit = "resource.calendar"

    ville = fields.Many2one('ville', string='Ville/Bureau')


class Ville(models.Model):
    
    _name = 'ville'
    
    name = fields.Char(string='Ville/Bureau')