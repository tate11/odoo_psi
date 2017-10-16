# -*- coding: utf-8 -*-
{
    'name': 'Gestion des contrats PSI',
    'version': '1.0',
    'category': 'Contract',
    'sequence': 0,
    'description': """Gestion ds contrats sur le PSI""",
    'website': 'https://www.ingenosya.mg',
    'depends': ['base','hr','hr_contract','mail','contacts'],
    'data':  [
              'views/hr_contract_views.xml',
              'views/hr_template_email.xml',
             ],
    'demo': [],
    'test': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
