# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

import time
from lxml import etree
from odoo import models, fields, api


class SchoolEvaluation(models.Model):
    _name = "school.evaluation"
    _rec_name = 'type'

    @api.multi
    def get_record(self):
        '''Method to get the evaluation questions'''
        eval_temp_obj = self.env['school.evaluation.template']
        eval_list = []
        for rec in self:
            eval_list = []
            eval_temps = eval_temp_obj.search([('type', '=', rec.type)])
            for eval_temp in eval_temps:
                eval_list.append((0, 0, {'stu_eval_id': eval_temp.id}))
            if rec.eval_line:
                rec.write({'eval_line': []})
            rec.write({'eval_line': eval_list})
        return True

    @api.multi
    @api.depends('eval_line')
    def _compute_total_points(self):
        '''Method to compute evaluation points'''
        for rec in self:
            if rec.eval_line:
                rec.total = sum(line.point_id.point for line in rec.eval_line
                                if line.point_id.point)

    @api.model
    def fields_view_get(self, view_id=None, viewtype='form', toolbar=False,
                        submenu=False):

        res = super(SchoolEvaluation, self).fields_view_get(view_id=view_id,
                                                            view_type=viewtype,
                                                            toolbar=toolbar,
                                                            submenu=submenu)
        teacher_group = self.env.user.has_group('school.group_school_teacher')
        doc = etree.XML(res['arch'])
        if teacher_group:
            if viewtype == 'tree':
                nodes = doc.xpath("//tree[@name='teacher_evaluation']")
                for node in nodes:
                    node.set('create', 'false')
                    node.set('edit', 'false')
                res['arch'] = etree.tostring(doc)
            if viewtype == 'form':
                nodes = doc.xpath("//form[@name='teacher_evaluation']")
                for node in nodes:
                    node.set('create', 'false')
                    node.set('edit', 'false')
                res['arch'] = etree.tostring(doc)
        return res

    student_id = fields.Many2one('student.student', 'Student Name',
                                 help="Select Student")
    teacher_id = fields.Many2one('hr.employee', "Teacher")
    type = fields.Selection([('student', 'Student'),
                             ('faculty', 'Faculty')],
                            'User Type', required=True,
                            help="Type of evaluation")
    date = fields.Date('Evaluation Date', required=True,
                       help="Evaluation Date",
                       default=lambda * a: time.strftime('%Y-%m-%d'))
#    evaluator_id = fields.Many2one('hr.employee', 'Faculty Name')
    eval_line = fields.One2many('school.evaluation.line', 'eval_id',
                                'Questionnaire')
    total = fields.Float('Total Points', compute='_compute_total_points',
                         method=True, help="Total Points Obtained")
    state = fields.Selection([('draft', 'Draft'), ('start', 'Start'),
                              ('finished', 'Finish'), ('cancelled', 'Cancel')],
                             'State', readonly=True, default='draft')
    username = fields.Many2one('res.users', 'User', readonly=True,
                               default=lambda self: self.env.user)

    @api.multi
    def set_start(self):
        '''change state to start'''
        for rec in self:
            rec.state = 'start'
        return True

    @api.model
    def default_get(self, fields):
        '''Override method to get default value of teacher'''
        res = super(SchoolEvaluation, self).default_get(fields)
        if res.get('type') == 'student':
            hr_emp = self.env['hr.employee'].search([('user_id', '=',
                                                      self._uid)])
            res.update({'teacher_id': hr_emp.id})
        return res

    @api.multi
    def set_finish(self):
        '''Change state to finished'''
        for rec in self:
            rec.state = 'finished'
        return True

    @api.multi
    def set_cancel(self):
        '''Change state to cancelled'''
        for rec in self:
            rec.state = 'cancelled'
        return True

    @api.multi
    def set_draft(self):
        '''Changes state to draft'''
        for rec in self:
            rec.state = 'draft'
        return True


class StudentEvaluationLine(models.Model):
    _name = 'school.evaluation.line'

    @api.onchange('point_id')
    def onchange_point(self):
        '''Method to get rating point based on rating'''
        if self.point_id:
            self.rating = self.point_id.rating

    eval_id = fields.Many2one('school.evaluation', 'Evaluation id')
#    teacher_eval_id = fields.Many2one('teacher.evaluation',
#                                      'Teacher Evaluation id')
    stu_eval_id = fields.Many2one('school.evaluation.template', 'Question')
    point_id = fields.Many2one('rating.rating', 'Rating',
                               domain="[('rating_id', '=', stu_eval_id)]")
    rating = fields.Char('Remarks')

    _sql_constraints = [
        ('number_uniq', 'unique(eval_id, stu_eval_id)',
         'Questions already exist!'),
    ]


class SchoolEvaluationTemplate(models.Model):
    _name = "school.evaluation.template"
    _rec_name = 'desc'

    desc = fields.Char('Description', required=True)
    type = fields.Selection([('faculty', 'Faculty'), ('student', 'Student')],
                            'User Type', required=True, default='faculty',
                            help="Type of Evaluation")
    rating_line = fields.One2many('rating.rating', 'rating_id', 'Rating')


class RatingRating(models.Model):
    _name = 'rating.rating'
    _rec_name = 'point'
    _order = "point desc"

    rating_id = fields.Many2one('school.evaluation.template', 'Stud',
                                help="Ratings")
    point = fields.Integer('Rating in points', required=True,
                           help="Points")
    rating = fields.Char('Remarks', required=True)
