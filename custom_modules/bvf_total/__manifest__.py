# -*- coding: utf-8 -*-
{
    'name': 'Suivi des Factures TOTAL',
    'version': '1.0',
    'category': 'Ressources humaines',
    'sequence': 0,
    'description': """Gestion Bordereau de Vérification Facture""",
    'website': 'https://www.ingenosya.mg',
    'depends': ['base', 'mail', 'account'],
    'data': ['data/delai_de_paiement_data.xml', 
             'data/sequence.xml',
             'data/res_groups.xml',
             'data/ir_rule.xml',
             'data/ir_model_access.xml',
             'data/mail_template.xml',   
             'data/relance_cron.xml',           
             'wizards/unlink_confirmation.xml',
             'wizards/change_status_confirmation.xml',
             'wizards/change_status_facture.xml',
             'wizards/relancer_bvf.xml',
             'wizards/reattribuer.xml',
             'wizards/select_prescripteur.xml',
             'wizards/second_confirm.xml',
             'wizards/second_confirm_facture.xml',
             'views/res_users.xml',
             'views/res_currency.xml',
             'views/account_journal.xml',
             'views/account_payment_term.xml',
             'views/bvf_total_views.xml',
             'views/field_restriction_access.xml',
             'reports/report_bvf_total.xml',
        ],
    'demo': [],
    'qweb': ['static/src/xml/base.xml',],
    'test': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}