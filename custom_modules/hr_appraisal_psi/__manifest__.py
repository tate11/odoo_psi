# -*- coding: utf-8 -*-
{
    'name': 'Employee Appraisals PSI',
    'version': '1.0',
    'category': 'Human Resources',
    'sequence': 0,
    'description': """Gestion des evaluations PSI""",
    'website': 'https://www.ingenosya.mg',
    'depends': ['hr_appraisal'],
    'data': [
        'views/hr_appraisal_views.xml',
        'views/hr_appraisal_wkf.xml',
        ],
    'demo': [],
    'test': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
