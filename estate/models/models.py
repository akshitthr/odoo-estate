# -*- coding: utf-8 -*-

from copy import copy
from email.policy import default
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class estate(models.Model):
    _name = 'estate.model'
    _description = 'A test model for estate'
    _order = 'id desc'

    name = fields.Char(required=True)
    description = fields.Text()
    postcode = fields.Char()
    date_availability = fields.Date(default=fields.Date.add(fields.date.today(), months=3), copy=False)
    expected_price = fields.Float(required=True)
    selling_price = fields.Float(readonly=True, copy=False)
    bedrooms = fields.Integer(default=2)
    living_area = fields.Integer()
    facades = fields.Integer()
    garage = fields.Boolean()
    garden = fields.Boolean()
    garden_area = fields.Integer()
    garden_orientation = fields.Selection(
        string='Garden Orientation',
        selection=[('north', 'North'), ('south', 'South'), ('east', 'East'), ('west', 'West')],
        help='Select orientation of the garden'
    )
    active = fields.Boolean(default=True)
    state = fields.Selection(
        string='State',
        selection=[('new', 'New'), ('offer received', 'Offer Received'), ('offer accepted', 'Offer Accepted'), ('sold', 'Sold'), ('canceled', 'Canceled')],
        help='Select the current state of the property',
        required=True,
        copy=False,
        default='new'
    )
    property_type_id = fields.Many2one('estate.model.type', string="Type")
    salesperson_id = fields.Many2one('res.users', string="Salesperson", default=lambda self: self.env.user)
    buyer_id = fields.Many2one('res.partner', string="Buyer", copy=False)
    tag_ids = fields.Many2many('estate.model.tags', string="Tags")
    offer_ids = fields.One2many('estate.model.offers', 'property_id', string="Property")
    total_area = fields.Integer(compute='_compute_total_area')
    best_price = fields.Float(compute='_compute_best_price')

    _sql_constraints = [
        ('check_expected_price_positive', 'CHECK (expected_price > 0)', 'Expected price must be greater than 0'),
        ('check_selling_price_positive', 'CHECK (selling_price > 0)', 'Selling Price must be greater than 0.')
    ]

    def sold_btn_clicked(self):
        for record in self:
            if record.state != 'canceled':
                record.state = 'sold'
            else:
                raise UserError("Canceled property cannot be sold.")
        return True
    
    def cancel_btn_clicked(self):
        for record in self:
            if record.state != 'sold':
                record.state = 'canceled'
            else:
                raise UserError("Sold property cannot be canceled.")
        return True

    @api.depends('living_area', 'garden_area')
    def _compute_total_area(self):
        for record in self:
            record.total_area = record.living_area + record.garden_area

    @api.depends('offer_ids.price')
    def _compute_best_price(self):
        for record in self:
            price_list = self.mapped('offer_ids.price')
            if price_list:
                record.best_price = max(price_list)
            else:
                record.best_price = 0

    @api.onchange('garden')
    def _onchange_garden(self):
        if self.garden:
            self.garden_area = 10
            self.garden_orientation = 'north'

        else:
            self.garden_area = 0
            self.garden_orientation = ''
    
    @api.constrains('expected_price', 'selling_price')
    def _check_price_percentage(self):
        for record in self:
            if record.selling_price <= 0:
                return
            if record.selling_price >= (record.expected_price * 0.9):
                return
            raise ValidationError("Selling price must be at least 90% of expected price. Please increase the selling price or decrease the expected price.")
    
    @api.ondelete(at_uninstall=False)
    def _unlink_constraint(self):
        if any(record.state != 'new' and record.state != 'canceled' for record in self):
            raise UserError("Can't delete records that aren't new or canceled.")


class type(models.Model):
    _name = 'estate.model.type'
    _description = 'Type model for estates'
    _order = 'name'

    name = fields.Char(required=True, string="Name")
    property_ids = fields.One2many('estate.model', 'property_type_id', string="Property")
    offer_ids = fields.One2many('estate.model.offers', 'property_type_id')
    offer_count = fields.Integer(compute="_compute_offer_count", string="Offer Count")
    sequence = fields.Integer(string="Sequence", default=2, help="Used to order property types. Lower is better.")

    _sql_constraints = [
        ('check_type_unique', 'UNIQUE (name)', 'Type name must be unique.')
    ]

    @api.depends('offer_ids')
    def _compute_offer_count(self):
        for record in self:
            record.offer_count = len(record.offer_ids)
    
    def action_open_offers(self):
        return {
            'name': 'Offers',
            'view_mode': 'tree,form',
            'res_model': 'estate.model.offers',
            'type': 'ir.actions.act_window',
            'domain': [('property_type_id', '=', self.id)]
        }


class tags(models.Model):
    _name = 'estate.model.tags'
    _description = 'Model containing tags for estates'
    _order = 'name'

    name = fields.Char(required=True, string="Name")
    color = fields.Integer(string="color")

    _sql_constraints = [
        ('check_tag_unique', 'UNIQUE (name)', 'Tag name must be unique')
    ]


class offers(models.Model):
    _name = 'estate.model.offers'
    _description = 'Model containing offers for estates'
    _order = 'price desc'

    price = fields.Float()
    status = fields.Selection(
        string="Status",
        selection=[('accepted', 'Accepted'), ('refused', 'Refused')],
        copy=False
    )
    partner_id = fields.Many2one('res.partner', string="Partner", required=True)
    property_id = fields.Many2one('estate.model', string="Property", required=True)
    property_type_id = fields.Many2one(related="property_id.property_type_id", store=True)
    validity = fields.Integer(default=7)
    date_deadline = fields.Date(compute='_compute_date_deadline')

    _sql_constraints = [
        ('check_price_positive', 'CHECK (price > 0)', 'Price must be greater than 0')
    ]

    def offer_confirm(self):
        for record in self.property_id.offer_ids:
            if record.status == 'accepted':
                raise UserError("Only one offer can be accepted for a property.")
        
        for record in self:
            self.status = 'accepted'
            self.property_id.buyer_id = self.partner_id
            self.property_id.selling_price = self.price
            self.property_id.state = 'offer accepted'
    
    def offer_decline(self):
        for record in self:
            record.status = 'refused'

    @api.depends('validity')
    def _compute_date_deadline(self):
        for record in self:
            if not record.create_date:
                record.date_deadline = fields.Date.add(fields.date.today(), days=record.validity)
            else:
                record.date_deadline = fields.Date.add(record.create_date, days=record.validity)
    
    @api.model
    def create(self, vals):
        estate = self.env['estate.model'].browse(vals['property_id'])

        if vals['price'] < estate.best_price:
            raise UserError("Offer price cannot be lower than existing offer.")
        
        estate.state = 'offer received'
        return super().create(vals)


class users(models.Model):
    _inherit = 'res.users'

    property_ids = fields.One2many('estate.model', 'salesperson_id', string="Property")
