# -*- coding: utf-8 -*-

from odoo import fields, models, _, api

class hr_psi_category(models.Model):
        _name ='hr.psi.category'
        name  = fields.Char('Name')
        psi_category_ids = fields.One2many('hr.psi.category.details','psi_category_id','')
      
class hr_psi_category_details(models.Model):
    _name = 'hr.psi.category.details'
    
    name  = fields.Char('')
    psi_professional_category  = fields.Selection([
                                        ('appui','APPUI'),
                                        ('execution','EXECUTION'),
                                        ('superviseur','SUPERVISEUR'),
                                        ('coordinateur','COORDINATEUR'),
                                       ('directeur','DIRECTEUR'),
                                       ('rra','RRA')], string="Titre de la Catégorie")
    
    psi_cat = fields.Char(string="CAT", size=2)
    prior_notice       = fields.Integer(string='Durée du Préavis')
    test_duration      = fields.Integer(string="Durée de la période d'essai")
    psi_category_id    = fields.Many2one('hr.psi.category','Category ID')