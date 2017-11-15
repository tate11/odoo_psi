# -*- coding: utf-8 -*-

import time
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.tools.translate import _
from odoo.tools.sql import drop_view_if_exists
from odoo.exceptions import UserError, ValidationError

class HrTimesheetPsi(models.Model):
    _name = "hr_timesheet_psi.sheet"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _table = 'hr_timesheet_psi_sheet'
    _order = "id desc"
    _description = "Timesheet"

    def _default_date_from(self):
        user = self.env['res.users'].browse(self.env.uid)
        r = user.company_id and user.company_id.timesheet_range or 'month'
        if r == 'month':
            return time.strftime('%Y-%m-01')
        elif r == 'week':
            return (datetime.today() + relativedelta(weekday=0, days=-6)).strftime('%Y-%m-%d')
        elif r == 'year':
            return time.strftime('%Y-01-01')
        return fields.Date.context_today(self)

    def _default_date_to(self):
        user = self.env['res.users'].browse(self.env.uid)
        r = user.company_id and user.company_id.timesheet_range or 'month'
        if r == 'month':
            return (datetime.today() + relativedelta(months=+1, day=1, days=-1)).strftime('%Y-%m-%d')
        elif r == 'week':
            return (datetime.today() + relativedelta(weekday=6)).strftime('%Y-%m-%d')
        elif r == 'year':
            return time.strftime('%Y-12-31')
        return fields.Date.context_today(self)

    def _default_employee(self):
        emp_ids = self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return emp_ids and emp_ids[0] or False

    name = fields.Char(string="Note", states={'confirm': [('readonly', True)], 'done': [('readonly', True)]})
    employee_id = fields.Many2one('hr.employee', string=u'Employé', default=_default_employee, required=True)
    user_id = fields.Many2one('res.users', related='employee_id.user_id', string='User', store=True, readonly=True)
    date_from = fields.Date(string='Date debut', default=_default_date_from, required=True,
        index=True, readonly=True, states={'new': [('readonly', False)]})
    date_to = fields.Date(string='Date fin', default=_default_date_to, required=True,
        index=True, readonly=True, states={'new': [('readonly', False)]})
    motif = fields.Text(string="Motif")
    time_from = fields.Float(string="Heure de debut")
    time_to = fields.Float(string="Heure de fin")
    hours = fields.Integer(compute="_get_hours", String='Heure')
    
    state = fields.Selection([
        ('new', 'Nouveau'),
        ('draft', 'Ouvert'),
        ('confirm', 'En attente d\'approbation'),
        ('done', 'Validé')], default='new', track_visibility='onchange',
        string='Etat', required=True, readonly=True, index=True,
        help='Circuit d\'approbation du timesheet')
    company_id = fields.Many2one('res.company', string='Company')
    department_id = fields.Many2one('hr.department', string='Departement',
        default=lambda self: self.env['res.company']._company_default_get())
    
    @api.depends('time_from','time_to')
    def _get_hours(self):
        for record in self:
            if record.time_from and record.time_to:
                time_from = record.time_from
                time_to = record.time_to
                difference = int(time_to) - int(time_from)             
                record.hours = float(difference)
   
   
    @api.constrains('date_to', 'date_from', 'employee_id')
    def _check_sheet_date(self, forced_user_id=False):
        for sheet in self:
            new_user_id = forced_user_id or sheet.user_id and sheet.user_id.id
            if new_user_id:
                self.env.cr.execute('''
                    SELECT id
                    FROM hr_timesheet_psi_sheet
                    WHERE (date_from <= %s and %s <= date_to)
                        AND user_id=%s
                        AND id <> %s''',
                    (sheet.date_to, sheet.date_from, new_user_id, sheet.id))
                if any(self.env.cr.fetchall()):
                    raise ValidationError(u'Vous ne pouvez pas avoir 2 feuilles de temps en même temps')

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        if self.employee_id:
            self.department_id = self.employee_id.department_id
            self.user_id = self.employee_id.user_id

    def copy(self, *args, **argv):
        raise UserError(_('You cannot duplicate a timesheet.'))

    @api.model
    def create(self, vals):
        if 'employee_id' in vals:
            if not self.env['hr.employee'].browse(vals['employee_id']).user_id:
                raise UserError(_('In order to create a timesheet for this employee, you must link him/her to a user.'))
        res = super(HrTimesheetPsi, self).create(vals)
        res.write({'state': 'draft'})
        return res

    @api.multi
    def write(self, vals):
        if 'employee_id' in vals:
            new_user_id = self.env['hr.employee'].browse(vals['employee_id']).user_id.id
            if not new_user_id:
                raise UserError(_('In order to create a timesheet for this employee, you must link him/her to a user.'))
            self._check_sheet_date(forced_user_id=new_user_id)
        return super(HrTimesheetPsi, self).write(vals)

    @api.multi
    def action_timesheet_draft(self):
        if not self.env.user.has_group('hr_timesheet.group_hr_timesheet_user'):
            raise UserError(_('Only an HR Officer or Manager can refuse timesheets or reset them to draft.'))
        self.write({'state': 'draft'})
        return True

    @api.multi
    def action_timesheet_confirm(self):
        for sheet in self:
            if sheet.employee_id and sheet.employee_id.parent_id and sheet.employee_id.parent_id.user_id:
                self.message_subscribe_users(user_ids=[sheet.employee_id.parent_id.user_id.id])
        self.write({'state': 'confirm'})
        return True

    @api.multi
    def action_timesheet_done(self):
        if not self.env.user.has_group('hr_timesheet.group_hr_timesheet_user'):
            raise UserError(_('Only an HR Officer or Manager can approve timesheets.'))
        if self.filtered(lambda sheet: sheet.state != 'confirm'):
            raise UserError(_("Cannot approve a non-submitted timesheet."))
        self.write({'state': 'done'})

    @api.multi
    def name_get(self):
        # week number according to ISO 8601 Calendar
        return [(r['id'], _('Week ') + str(datetime.strptime(r['date_from'], '%Y-%m-%d').isocalendar()[1]))
            for r in self.read(['date_from'], load='_classic_write')]

    @api.multi
    def unlink(self):
        sheets = self.read(['state'])
        for sheet in sheets:
            if sheet['state'] in ('confirm', 'done'):
                raise UserError(_(u'Vous ne pouvez pas supprimé un timesheet qui est déjà valider.'))

        return super(HrTimesheetPsi, self).unlink()
