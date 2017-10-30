# -*- coding: utf-8 -*-
{
    'name': 'Gestion des Employées PSI',
    'version': '1.0',
    'category': 'Contract',
    'sequence': 0,
    'description': """Gestion des Employées chez PSI-M""",
    'website': 'https://www.ingenosya.mg',
    'depends': ['hr', 'hr_recruitment_psi'],
    'data':  [
              'data/hr_employee_cron.xml',
              'data/mail_template_hr_employee_data.xml',
              'data/hr_employee_data.xml',
              'views/hr_employee_views.xml',
             ],
    'demo': [],
    'test': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
