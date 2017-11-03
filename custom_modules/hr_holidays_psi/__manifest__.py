# -*- coding: utf-8 -*-
{
    'name': 'Gestion des absences PSI',
    'version': '1.0',
    'category': 'Human Resources',
    'sequence': 0,
    'description': """Gestion des absences PSI""",
    'website': 'https://www.ingenosya.mg',
    'depends': ['hr_holidays','hr_recruitment'],
    'data': [
             'data/hr_holidays_data.xml',
             'views/hr_holidays_views.xml',
        ],
    'demo': [],
    'test': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
