# -*- coding: utf-8 -*-

from odoo import fields, models, _, api

class hr_wage_grid(models.Model):
        _name ='hr.wage.grid'
        name  = fields.Char('Name')
        wage_grid_details = fields.One2many('hr.wage.grid.details','wage_grid_id','')
      
class hr_wage_grid_details(models.Model):
    _name = 'hr.wage.grid.details'
    
    
    psi_category_details  = fields.Many2one('hr.psi.category.details')
    psi_professional_category  = fields.Selection(related='psi_category_details.psi_professional_category', store=True)
    
    name = fields.Char(string='')
    
    psi_category                = fields.Char(related='psi_category_details.psi_cat', store=True)
    
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
    
    def _get_echelon(self,method):
        if method == 'echelon_1' :
            return self.echelon_1
        if method == 'echelon_2' :
            return self.echelon_2
        if method == 'echelon_3' :
            return self.echelon_3
        if method == 'echelon_4' :
            return self.echelon_4
        if method == 'echelon_5' :
            return self.echelon_5
        if method == 'echelon_6' :
            return self.echelon_6
        if method == 'echelon_7' :
            return self.echelon_7
        if method == 'echelon_8' :
            return self.echelon_8
        if method == 'echelon_9' :
            return self.echelon_9
        if method == 'echelon_10' :
            return self.echelon_10
        if method == 'echelon_11' :
            return self.echelon_11
        if method == 'echelon_12' :
            return self.echelon_12
        if method == 'echelon_13' :
            return self.echelon_13
        if method == 'echelon_14' :
            return self.echelon_14
        if method == 'echelon_15' :
            return self.echelon_15
        if method == 'echelon_16' :
            return self.echelon_16
        if method == 'echelon_17' :
            return self.echelon_17
        if method == 'echelon_18' :
            return self.echelon_18
        if method == 'echelon_19' :
            return self.echelon_19
        if method == 'echelon_20' :
            return self.echelon_20
        if method == 'echelon_hc' :
            return self.echelon_hc
        return 0