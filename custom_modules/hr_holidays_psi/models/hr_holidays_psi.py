# -*- coding: utf-8 -*-

import dateutil.parser
from datetime import date, datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _

class hr_holidays_psi(models.Model):
    _inherit = "hr.holidays"

    justificatif_file = fields.Binary(string=u'Pièce justificatif', help=u"Joindre un certificat médical ou une ordonnance", tracability="onchange") 
 
#    color_name_holidays_status = fields.Selection(related='holiday_status_id.color_name', string="color")
    
    # Send mail - rappel piece justificatif - conge maladie  
    @api.multi
    @api.constrains('holiday_status_id')  
    def _send_email_rappel_justificatif_conge_maladie(self, automatic=False):
        print "test cron by send mail"
        date_debut = self.date_from
        date = dateutil.parser.parse(date_debut).date()
        dt = datetime.strptime(date_debut,'%Y-%m-%d %H:%M:%S')
        date_y_m_d = datetime(
                                     year=date.year, 
                                     month=date.month,
                                     day=date.day,
                )   
        date_to_notif = date_y_m_d + relativedelta(hours=48)   
        if self.id != False :
            for record in self:
                if record.holiday_status_id.color_name == 'blue' or record.holiday_status_id.name == u"Cong� maladie":
#                    if not record.justificatif_file:
                    if not self.justificatif_file and date_to_notif.date() == datetime.today().date() :
                        template = self.env.ref('hr_holidays_psi.custom_template_rappel_justificatif_conge_maladie')
                        self.env['mail.template'].browse(template.id).send_mail(self.id)               
        if automatic:
            self._cr.commit()