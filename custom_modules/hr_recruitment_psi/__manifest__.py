# -*- coding: utf-8 -*-
{
    'name': 'Recrutement PSI',
    'version': '1.0',
    'category': 'Human Resources',
    'sequence': 0,
    'description': """Gestion de recrutement PSI""",
    'website': 'https://www.ingenosya.mg',
    'depends': ['hr','hr_recruitment','mail','contacts'],
    'data': [
             'data/hr_recruitment_data.xml',
             'views/hr_job_views.xml',
             'views/hr_job_wkf.xml',
             'views/hr_recruitement_views.xml',
             'views/hr_recruitement_wkf.xml',
             'views/template_mail_refus.xml',
             ],
    'demo': [],
    'test': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
