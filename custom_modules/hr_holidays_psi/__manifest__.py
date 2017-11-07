# -*- coding: utf-8 -*-
{
    'name': 'Gestion des absences PSI',
    'version': '1.0',
    'category': 'Human Resources',
    'sequence': 0,
    'description': """Gestion des absences PSI""",
    'website': 'https://www.ingenosya.mg',
    'depends': ['hr_holidays','hr_recruitment_psi','hr_employee_psi','report'],
    'data': [
        'data/hr_holidays_cron.xml',
        'data/hr_holidays_data.xml',
        'data/mail_template_hr_holidays_data.xml',
        'views/hr_holidays_views.xml',
        'views/hr_holidays_configuration_views.xml',
        ],
    'demo': [],
    'test': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
