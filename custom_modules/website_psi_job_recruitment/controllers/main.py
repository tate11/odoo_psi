# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import json
import pytz

from datetime import datetime
from psycopg2 import IntegrityError

from odoo import http
from odoo.http import request
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.translate import _
from odoo.exceptions import ValidationError
from odoo.addons.base.ir.ir_qweb.fields import nl2br
from odoo.addons.website.models.website import slug

class WebsiteHrRecruitment(http.Controller):
  
     # Check and insert values from the form on the model <model>
    @http.route('/website_form_apply/<string:model_name>', type='http', auth="public", methods=['POST'], website=True)
    def website_form(self, model_name, **kwargs):
        model_record = request.env['ir.model'].search([('model', '=', model_name), ('website_form_access', '=', True)])
        if not model_record:
            return json.dumps(False)

        try:
            data = self.extract_data_override(model_record, request.params)
            print "DATA : ",data
        # If we encounter an issue while extracting data
        except ValidationError, e:
            # I couldn't find a cleaner way to pass data to an exception
            return json.dumps({'error_fields' : e.args[0]})

        try:
            id_record = self.insert_record(request, model_record, data['record'], data['custom'], data.get('meta'))
           
            if id_record:
                self.insert_attachment(model_record, id_record, data['attachments'], data['record'])

        # Some fields have additional SQL constraints that we can't check generically
        # Ex: crm.lead.probability which is a float between 0 and 1
        # TODO: How to get the name of the erroneous field ?
        except IntegrityError:
            return json.dumps(False)

        request.session['form_builder_model'] = model_record.name
        request.session['form_builder_id']    = id_record

        return json.dumps({'id': id_record})

    # Constants string to make custom info and metadata readable on a text field

    _custom_label = "%s\n___________\n\n" % _("Custom infos")  # Title for custom fields
    _meta_label = "%s\n________\n\n" % _("Metadata")  # Title for meta data

    # Dict of dynamically called filters following type of field to be fault tolerent

    def identity(self, field_label, field_input):
        return field_input

    def integer(self, field_label, field_input):
        return int(field_input)

    def floating(self, field_label, field_input):
        return float(field_input)

    def boolean(self, field_label, field_input):
        return bool(field_input)

    def date(self, field_label, field_input):
        lang = request.env['ir.qweb.field'].user_lang()
        return datetime.strptime(field_input, lang.date_format).strftime(DEFAULT_SERVER_DATE_FORMAT)

    def datetime(self, field_label, field_input):
        lang = request.env['ir.qweb.field'].user_lang()
        strftime_format = (u"%s %s" % (lang.date_format, lang.time_format))
        user_tz = pytz.timezone(request.context.get('tz') or request.env.user.tz or 'UTC')
        dt = user_tz.localize(datetime.strptime(field_input, strftime_format)).astimezone(pytz.utc)
        return dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    def binary(self, field_label, field_input):
        return base64.b64encode(field_input.read())

    def one2many(self, field_label, field_input):
        #return [int(i) for i in field_input.split(',')]
        return field_input
    
    def many2many(self, field_label, field_input, *args):
        return [(args[0] if args else (6,0)) + (self.one2many(field_label, field_input),)]

    _input_filters = {
        'char': identity,
        'text': identity,
        'html': identity,
        'date': date,
        'datetime': datetime,
        'many2one': integer,
        'one2many': one2many,
        'many2many':many2many,
        'selection': identity,
        'boolean': boolean,
        'integer': integer,
        'float': floating,
        'binary': binary,
    }


    # Extract all data sent by the form and sort its on several properties
    def extract_data(self, model, values):

        data = {
            'record': {},        # Values to create record
            'attachments': [],  # Attached files
            'custom': '',        # Custom fields values
        }

        authorized_fields = model.sudo()._get_form_writable_fields()
        error_fields = []


        for field_name, field_value in values.items():
            # If the value of the field if a file
            if hasattr(field_value, 'filename'):
                # Undo file upload field name indexing
                field_name = field_name.rsplit('[', 1)[0]

                # If it's an actual binary field, convert the input file
                # If it's not, we'll use attachments instead
               
                if field_name in authorized_fields and authorized_fields[field_name]['type'] == 'binary':
                    data['record'][field_name] = base64.b64encode(field_value.read())
                else:
                    field_value.field_name = field_name
                    data['attachments'].append(field_value)

            # If it's a known field
            elif field_name in authorized_fields:
                try:
                    input_filter = self._input_filters[authorized_fields[field_name]['type']]
                    data['record'][field_name] = input_filter(self, field_name, field_value)
                except ValueError:
                    error_fields.append(field_name)

            # If it's a custom field
            elif field_name != 'context':
                data['custom'] += "%s : %s\n" % (field_name.decode('utf-8'), field_value)

        # Add metadata if enabled
        environ = request.httprequest.headers.environ
        if(request.website.website_form_enable_metadata):
            data['meta'] += "%s : %s\n%s : %s\n%s : %s\n%s : %s\n" % (
                "IP"                , environ.get("REMOTE_ADDR"),
                "USER_AGENT"        , environ.get("HTTP_USER_AGENT"),
                "ACCEPT_LANGUAGE"   , environ.get("HTTP_ACCEPT_LANGUAGE"),
                "REFERER"           , environ.get("HTTP_REFERER")
            )

        # This function can be defined on any model to provide
        # a model-specific filtering of the record values
        # Example:
        # def website_form_input_filter(self, values):
        #     values['name'] = '%s\'s Application' % values['partner_name']
        #     return values
        dest_model = request.env[model.model]
        if hasattr(dest_model, "website_form_input_filter"):
            data['record'] = dest_model.website_form_input_filter(request, data['record'])

        missing_required_fields = [label for label, field in authorized_fields.iteritems() if field['required'] and not label in data['record']]
        if any(error_fields):
            raise ValidationError(error_fields + missing_required_fields)

        return data

    def insert_record(self, request, model, values, custom, meta=None):
        record = request.env[model.model].sudo().create(values)

        if custom or meta:
            default_field = model.website_form_default_field_id
            default_field_data = values.get(default_field.name, '')
            custom_content = (default_field_data + "\n\n" if default_field_data else '') \
                           + (self._custom_label + custom + "\n\n" if custom else '') \
                           + (self._meta_label + meta if meta else '')

            # If there is a default field configured for this model, use it.
            # If there isn't, put the custom data in a message instead
            if default_field.name:
                if default_field.ttype == 'html' or model.model == 'mail.mail':
                    custom_content = nl2br(custom_content)
                record.update({default_field.name: custom_content})
            else:
                values = {
                    'body': nl2br(custom_content),
                    'model': model.model,
                    'message_type': 'comment',
                    'no_auto_thread': False,
                    'res_id': record.id,
                }
                mail_id = request.env['mail.message'].sudo().create(values)

        return record.id

    # Link all files attached on the form
    def insert_attachment(self, model, id_record, files, values):
        
        orphan_attachment_ids = []
        record = model.env[model.model].browse(id_record)
        
        authorized_fields = model.sudo()._get_form_writable_fields()
        
        for file in files:
           
            custom_field = file.field_name not in authorized_fields
            attachment_value = {
                'name': "CV_"+values.get('name'),
                'datas': base64.encodestring(file.read()),
                'datas_fname': file.filename,
                'res_model': 'hr.applicant',
                'res_id': record.id,
            }
            print attachment_value['res_model']
            attachment_id = request.env['ir.attachment'].sudo().create(attachment_value)
            if attachment_id and not custom_field:
                record.sudo()[file.field_name] = [(4, attachment_id.id)]
            else:
                orphan_attachment_ids.append(attachment_id.id)
            

        # If some attachments didn't match a field on the model,
        # we create a mail.message to link them to the record
        if orphan_attachment_ids:
            if model.model != 'mail.mail':
                values = {
                    'body': _('<p>Attached files : </p>'),
                    'model': model.model,
                    'message_type': 'comment',
                    'no_auto_thread': False,
                    'res_id': id_record,
                    'attachment_ids': [(6, 0, orphan_attachment_ids)],
                }
                mail_id = request.env['mail.message'].sudo().create(values)
        else:
            # If the model is mail.mail then we have no other choice but to
            # attach the custom binary field files on the attachment_ids field.
            for attachment_id_id in orphan_attachment_ids:
                record.attachment_ids = [(4, attachment_id_id)]

    def extract_data_override(self, model, values):
        #form personal information 
        parents = values.pop('name_parent[]','').split(',')
        degree_of_relationships = values.pop('degree_of_relationship[]','').split(',')
        post_office_titles = values.pop('post_office_title[]','').split(',')
        
        #form alweready applicant
        postes = values.pop('name_poste[]','').split(',')
        periods = values.pop('period[]','').split(',')
        
        #connaissance linguistique
        linguistics = values.pop('linguistique[]','').split(',')
        writtens = values.pop('written[]','').split(',') 
        spokens = values.pop('spoken[]','').split(',')
        listens = values.pop('listen[]','').split(',')
        
        #etudes universitaires
        name_universitys = values.pop('name_university[]','').split(',')
        city_universitys = values.pop('city_university[]','').split(',')
        country_id_universitys = values.pop('country_id_university[]','').split(',')
        from_date_universitys = values.pop('from_date_university[]','').split(',')
        end_date_universitys = values.pop('end_date_university[]','').split(',')
        degree_universitys = values.pop('degree_university[]','').split(',')
        study_domain_universitys = values.pop('study_domain_university[]','').split(',')
        
        #etudes secondaires
        name_secondarys = values.pop('name_secondary[]','').split(',')
        city_secondarys = values.pop('city_secondary[]','').split(',')
        country_id_secondarys = values.pop('country_id_secondary[]','').split(',')
        from_date_secondarys = values.pop('from_date_secondary[]','').split(',')
        end_date_secondarys = values.pop('end_date_secondary[]','').split(',')
        degree_secondarys = values.pop('degree_secondary[]','').split(',')
        study_domain_secondarys = values.pop('study_domain_secondary[]','').split(',')
        
        #fonctions_anterieures
        begin_dates = values.pop('begin_date[]','').split(',')
        end_dates = values.pop('end_date[]','').split(',')
        last_basic_salarys = values.pop('last_basic_salary[]','').split(',')
        title_functions = values.pop('title_function[]','').split(',')
        employers = values.pop('employer[]','').split(',')
        type_of_activitys = values.pop('type_of_activity[]','').split(',')
        addresss = values.pop('address[]','').split(',')
        name_of_supervisors = values.pop('name_of_supervisor[]','').split(',')
        number_of_superviseds = values.pop('number_of_supervised[]','').split(',')
        reason_for_leavings = values.pop('reason_for_leaving[]','').split(',')
        mobile_phones = values.pop('mobile_phone[]','').split(',')
        work_emails = values.pop('work_email[]','').split(',')
        descriptions = values.pop('description[]','').split(',')
        
        #reference professionnelles
        ref_names = values.pop('ref_name[]','').split(',')
        ref_function_titles = values.pop('ref_function_title[]','').split(',')
        ref_companys = values.pop('ref_company[]','').split(',')
        ref_mobile_phones = values.pop('ref_mobile_phone[]','').split(',')
        ref_work_emails = values.pop('ref_work_email[]','').split(',')
        
                
        parent_information_line_ids = []
        
        parent_information_line = {}
        if len(parents) > 0 and parents[0] != '' :
            for index, parent in enumerate(parents):
                if parents[index] != '' and degree_of_relationships[index] != '' and post_office_titles[index] !='' :
                    parent_information_line = {
    
                        'name': parents[index],
                        'degree_of_relationship': degree_of_relationships[index],
                        'post_office_title' : post_office_titles[index]
    
                        }
                    parent_information_line_ids.append((0, 0, parent_information_line))
                
        description_already_answered_application_line_ids = []
        
        description_already_answered_application_line = {}
        if len(postes) > 0 and postes[0] != '' :
            for index, poste in enumerate(postes):
                 if postes[index] != '' and periods[index] != '' :
                    description_already_answered_application_line = {
    
                        'name': postes[index],
                        'period': periods[index]
                    
    
                        }
                    description_already_answered_application_line_ids.append((0, 0, description_already_answered_application_line))
         
        linguistic_knowledge_line_ids = []
        
        linguistic_knowledge_line = {}
        if len(linguistics) > 0 and linguistics[0] != '' and writtens[0] != '' and spokens[0] != '' and listens[0] != '' :
            for index, linguistic in enumerate(linguistics):
                print "AIZA E : ",linguistics[0]
                if  linguistics[index] != '' and writtens[index] != '' and spokens[index] != '' and listens[index] != '' :
                    linguistic_knowledge_line = {
    
                        'name': linguistics[index],
                        'written': writtens[index],
                        'spoken': spokens[index],
                        'listen': listens[index]
                    
                       }
                    linguistic_knowledge_line_ids.append((0, 0, linguistic_knowledge_line))
        
        university_line_ids = []
        
        university_line = {}
        if len(name_universitys) > 0 and name_universitys[0] != '' :
            for index, name_university in enumerate(name_universitys):
                if name_universitys[index] != '' and city_universitys[index] != '' and country_id_universitys[index] != '' and degree_universitys[index] != '' and  study_domain_universitys[index] != '' and from_date_universitys[index] != '' and end_date_universitys[index] != '' :
                        university_line = {
                                           'name': name_universitys[index],
                                           'city': city_universitys[index],
                                           'country_id': country_id_universitys[index],
                                           'from_date': from_date_universitys[index],
                                           'end_date': end_date_universitys[index],
                                           'degree': degree_universitys[index],
                                           'study_domain': study_domain_universitys[index]
    
                        }
                        university_line_ids.append((0, 0, university_line))
        
        secondary_line_ids = []
        
        secondary_line = {}
        if len(name_secondarys) > 0 and name_secondarys[0] != '' :
            for index, name_secondary in enumerate(name_secondarys):
                if name_secondarys[index] != '' and city_secondarys[index] != '' and country_id_secondarys[index] != '' and degree_secondarys[index] != '' and  study_domain_secondarys[index] != '' and from_date_secondarys[index] != '' and end_date_secondarys[index] != '' :
                        secondary_line = {
                                           'name': name_secondarys[index],
                                           'city': city_secondarys[index],
                                           'country_id': country_id_secondarys[index],
                                           'from_date': from_date_secondarys[index],
                                           'end_date': end_date_secondarys[index],
                                           'degree': degree_secondarys[index],
                                           'study_domain': study_domain_secondarys[index]
    
                        }
                        secondary_line_ids.append((0, 0, secondary_line))
                
                
        previous_functions_line_ids = []
        
        previous_functions_line = {}
        if len(begin_dates) > 0 and begin_dates[0] != '' :
            for index, begin_date in enumerate(begin_dates):
                if begin_dates[index] != '' and  end_dates[index] != '' and last_basic_salarys[index] != '' and title_functions[index] != '' and employers[index] != '' and type_of_activitys[index] != '' and addresss[index] != '' and name_of_supervisors[index] != '' and name_of_supervisors[index] != '' and number_of_superviseds[index] != '' and reason_for_leavings[index] != '' and mobile_phones[index] != '' and work_emails[index] != '' and descriptions[index] != '':   
                    previous_functions_line = {
    
                    'begin_date': begin_dates[index],
                    'end_date': end_dates[index],
                    'last_basic_salary': last_basic_salarys[index],
                    'title_function': title_functions[index],
                    'employer': employers[index],
                    'type_of_activity': type_of_activitys[index],
                    'address': addresss[index],
                    'name_of_supervisor': name_of_supervisors[index],
                    'number_of_supervised': number_of_superviseds[index],
                    'reason_for_leaving': reason_for_leavings[index],
                    'mobile_phone': mobile_phones[index],
                     'work_email': work_emails[index],
                    'description': descriptions[index]
    
                    }
                    previous_functions_line_ids.append((0, 0, previous_functions_line))
                
        professional_references_line_ids = []
        
        professional_references_line = {}
        if len(ref_names) > 0 and ref_names[0] != '' :
            for index, ref_name in enumerate(ref_names):
                if ref_names[index] != '' and ref_function_titles[index] != '' and ref_companys[index] != '' and ref_mobile_phones[index] != '' and ref_work_emails[index] != '' :
                     if ref_names[index] != '' and ref_function_titles[index] != '' and ref_companys[index] != '' and ref_mobile_phones[index] != '' and ref_work_emails[index] != '' :
                         professional_references_line = {
                                                        
                            'name': ref_names[index],
                            'function_title': ref_function_titles[index],
                            'company': ref_companys[index],
                            'mobile_phone': ref_mobile_phones[index],
                            'work_email': ref_work_emails[index]
    
                            }
                         professional_references_line_ids.append((0, 0, professional_references_line))
        data = self.extract_data(model, values)
    
        if data['record']:
    
          data['record']['parent_information_employees'] = parent_information_line_ids
          data['record']['description_already_answered_application'] = description_already_answered_application_line_ids
          data['record']['linguistic_knowledge'] = linguistic_knowledge_line_ids
          data['record']['university_studies'] = university_line_ids
          data['record']['secondary_studies'] = secondary_line_ids
          data['record']['previous_functions'] = previous_functions_line_ids
          data['record']['professional_references'] = professional_references_line_ids
         
        return data
