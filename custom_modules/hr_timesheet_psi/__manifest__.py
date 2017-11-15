# -*- coding: utf-8 -*-
{
    'name': 'Gestion des Timesheet PSI',
    'version': '1.0',
    'category': 'Timesheet',
    'sequence': 0,
    'description': """Gestion des Timesheet chez PSI-M""",
    'website': 'https://www.ingenosya.mg',
    'depends': ['hr_timesheet'],
    'data':  [
              'data/hr_timesheet_data.xml',
              'views/hr_timesheet_psi_views.xml'
             ],
    'demo': [],
    'test': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
