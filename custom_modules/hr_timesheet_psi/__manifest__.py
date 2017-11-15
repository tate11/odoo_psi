# -*- coding: utf-8 -*-
{
    'name': 'Gestion des Timesheets PSI',
    'version': '1.0',
    'category': 'Timesheet',
    'sequence': 0,
    'description': """Gestion des Timesheet chez PSI-M""",
    'website': 'https://www.ingenosya.mg',
    'depends': ['account', 'hr', 'project'],
    'data':  [
        'data/resource_calendar.xml',
        'security/ir.model.access.csv',
        ],
    'demo': [],
    'test': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
