# -*- coding: utf-8 -*-
{
    'name': 'Payroll PSI',
    'version': '1.0',
    'category': 'Human Resources',
    'sequence': 0,
    'description': """PSI""",
    'website': 'https://www.ingenosya.mg',
    'depends': ['hr','hr_payroll'],
    'data': [
             'views/hr_payroll_views.xml',
             'data/hr_payroll_data.xml',
             ],
    'demo': [],
    'test': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
