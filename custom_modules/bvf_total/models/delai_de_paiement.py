# -*- coding: utf-8 -*-

from odoo import models,fields
from datetime import date

class Delai_de_paiement_total(models.Model):
    _name = "delai_paiement.total"
    _rec_name = 'valeur'
    
    code = fields.Char(string='Code', required=True)
    libelle = fields.Char(string='Libellé', required=True)
    valeur = fields.Integer(string='Valeur en jours', required=True)