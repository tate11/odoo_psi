# -*- coding: utf-8 -*-
{
    'name': 'Gestion des Projets PSI',
    'version': '1.0',
    'category': 'Projet',
    'sequence': 0,
    'description': """Gestion des Projets chez PSI-M""",
    'website': 'https://www.ingenosya.mg',
    'depends': ['project','hr_employee_psi','hr_timesheet_psi'],
    'data':  [
              'views/project_views.xml',
             ],
    'demo': [],
    'test': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
