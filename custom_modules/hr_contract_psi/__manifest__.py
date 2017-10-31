# -*- coding: utf-8 -*-
{
    'name': 'Gestion des contrats PSI',
    'version': '1.0',
    'category': 'Contract',
    'sequence': 0,
    'description': """Gestion des contrats chez PSI""",
    'website': 'https://www.ingenosya.mg',
    'depends': ['base','hr','hr_contract','mail','contacts','hr_recruitment_psi','hr_employee_psi'],
    'data':  [
              'data/hr_wage_grid_data.xml',
              'data/mail_template_hr_contract_data.xml',
              'data/hr_contract_data.xml',
              'data/mail_template_evenement_professionnel.xml',
              'views/hr_contract_views.xml',          
             ],
    'demo': [],
    'test': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
