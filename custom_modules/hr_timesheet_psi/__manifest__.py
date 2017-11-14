# -*- coding: utf-8 -*-
{
    'name': 'Gestion des Timesheet PSI',
    'version': '1.0',
    'category': 'Timesheet',
    'sequence': 0,
    'description': """Gestion des Timesheet chez PSI-M""",
    'website': 'https://www.ingenosya.mg',
    'depends': ['account', 'hr', 'project'],
    'data':  [
              'data/hr_timesheet_data.xml',
              'views/resource_views_psi.xml',
              'views/hr_timesheet_views.xml',
             ],
    'demo': [],
    'test': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
