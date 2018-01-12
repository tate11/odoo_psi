# -*- coding: utf-8 -*-
{
    'name': 'Prestataire PSI',
    'version': '1.0',
    'category': 'Prestataire',
    'sequence': 0,
    'description': """Prestataire chez PSI-M""",
    'website': 'https://www.ingenosya.mg',
    'depends': ['project_psi'],
    'data':  [
              'data/res_groups.xml',
              'views/res_partner_views.xml',
              'views/project_views.xml',
             ],
    'demo': [],
    'test': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
