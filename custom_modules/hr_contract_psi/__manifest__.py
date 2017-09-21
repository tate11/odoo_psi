# -*- coding: utf-8 -*-
{
    'name': 'Gestion des contrats PSI',
    'version': '1.0',
    'category': 'Contract',
    'sequence': 0,
    'description': """Gestion ds contrats sur le PSI""",
    'website': 'https://www.ingenosya.mg',
    'depends': ['hr','hr_contract'],
    'data':  [
              'views/hr_contract_views.xml',
             ],
    'demo': [],
    'test': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
