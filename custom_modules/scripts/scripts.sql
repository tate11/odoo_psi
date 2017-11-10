-- mise a jour des champs blacklistes dans ir.model.fields
update ir_model_fields set website_form_blacklisted = false
where model like 'hr.applicant%' 
and name in ('name', 'salary_expected', 'psi_salary_type', 'birthday', 'country_id', 'partner_mobile', 'number_of_dependent_children', 'already_answered_application', 'sexe', 'marital')
