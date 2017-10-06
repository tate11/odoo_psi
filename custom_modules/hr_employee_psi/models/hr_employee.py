# -*- coding: utf-8 -*-

from odoo import fields, models

class hr_employee(models.Model):
    
    _inherit                        = 'hr.employee'
    
    father_name                     = fields.Char(string='Nom du pére')
    mother_name                     = fields.Char(string='Nom de la mére')
    spouse_s_name                   = fields.Char(string='Nom du conjoint')
    
    emergency_contact_id            = fields.Many2one('hr.person.information', string='Personne à contacter en cas d\'urgence',
         help='Person to contact in case of emergency')
    
    beneficiary_of_death_benefit_id = fields.Many2one('hr.person.information', string='Bénéficiaire d\'indemnité en cas de décéss',
         help='Beneficiary of death benefit')
    
    information_about_children_id   = fields.Many2one('hr.person', string=' Informations sur les enfants',help='Information about children')
    
    information_cin_id              = fields.Many2one('hr.information.cin', string='Information sur CIN',help='Information about CIN')

class Person(models.Model):

     _name         = 'hr.person'
     
     name          = fields.Char(string='Nom',required=True)
     date_of_birth = fields.Date(string="Date de naissance",required=True)    
     sex           = fields.Selection([
        ('M', 'Masculin'),
        ('F', 'Feminin')
     ], string='Genre')    

    
class PersonInformation(models.Model):
   
    _inherit      = 'hr.person'
    _name         = 'hr.person.information'
    
    address       = fields.Char(string='Adresse')
    contact       = fields.Integer(string='Contact')
    
    relation      = fields.Selection([
        ('enfant', 'Enfant'),
        ('famille', 'Famille'),
        ('conjoint', 'Conjoint')
    ], string='Relation')
    

class InformationCin(models.Model):
    
    _name               = 'hr.information.cin'
    
    num_cin             = fields.Char(u'Numéro', size=64, required=True)
    date_of_issue       = fields.Date(string="Date d’émission")
    place_of_issue      = fields.Char(string='Lieu d’émission')
    end_of_validity     = fields.Date(string="Fin de validité")
    duplicata           = fields.Boolean(string="Duplicata (O/N)")
    date_of_duplicata   = fields.Date(string="Date de duplicata")