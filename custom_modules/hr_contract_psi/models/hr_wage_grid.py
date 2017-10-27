# -*- coding: utf-8 -*-

from odoo import fields, models, _, api

class hr_wage_grid(models.Model):
        _name ='hr.wage.grid'
        name  = fields.Char('Name')
        wage_grid_details = fields.One2many('hr.wage.grid.details','wage_grid_id','')
      
class hr_wage_grid_details(models.Model):
    _name = 'hr.wage.grid.details'
    
    psi_professional_category  = fields.Selection([
                                        ('appui','APPUI'),
                                        ('execution','EXECUTION'),
                                        ('superviseur','SUPERVISEUR'),
                                        ('coordinateur','COORDINATEUR'),
                                       ('directeur','DIRECTEUR'),
                                       ('rra','RRA')], string="Titre de Catégorie")
    
    name       = fields.Char(string='')
    
    psi_category                = fields.Selection([
                                       ('a','A'),
                                       ('b','B'),
                                       ('c','C'),
                                       ('d','D'),
                                       ('e','E'),
                                       ('hc','HC')
                               ], string="CAT")
    
    psi_sub_category            = fields.Selection([
                                       ('1','1'),
                                       ('2','2'),
                                       ('3','3'),
                                       ('4','4')
                               ], string="Sous Cat")
    
    echelon_1                = fields.Integer(string='1')
    echelon_2                = fields.Integer(string='2')
    echelon_3                = fields.Integer(string='3')
    echelon_4                = fields.Integer(string='4')
    echelon_5                = fields.Integer(string='5')
    echelon_6                = fields.Integer(string='6')
    echelon_7                = fields.Integer(string='7')
    echelon_8                = fields.Integer(string='8')
    echelon_9                = fields.Integer(string='9')
    echelon_10               = fields.Integer(string='10')
    echelon_11               = fields.Integer(string='11')
    echelon_12               = fields.Integer(string='12')
    echelon_13               = fields.Integer(string='13')
    echelon_14               = fields.Integer(string='14')
    echelon_15               = fields.Integer(string='15')
    echelon_16               = fields.Integer(string='16')
    echelon_17               = fields.Integer(string='17')
    echelon_18               = fields.Integer(string='18')
    echelon_19               = fields.Integer(string='19')
    echelon_20               = fields.Integer(string='20')
    echelon_hc               = fields.Integer(string='HC')

    wage_grid_id             = fields.Many2one('hr.wage.grid','Wage Grid ID')