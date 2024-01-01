# -*- coding: utf-8 -*-

from pyexpat import model
from odoo import models, fields, api, exceptions
from datetime import timedelta, date
from odoo.tools.float_utils import float_compare


class Salesman(models.Model):
    _inherit = "res.users"

    property_ids = fields.One2many(
        "estate.property", "sales_person", string="Property")


class EstatePoperty(models.Model):
    _name = "estate.property"
    _description = "Estate Property by Kororo"
    _order = "id desc"

    name = fields.Char(string="Name", required=True)
    description = fields.Text(string="Description")
    postcode = fields.Char(string="Post Code")
    date_availability = fields.Date(
        string="Available From", default=fields.Datetime.today)
    expected_price = fields.Float(string="Expected Price", required=True)
    best_offer = fields.Float(string="Best Offer")
    selling_price = fields.Float(
        string="Selling Price", readonly=True)
    bedrooms = fields.Integer(string="Bedrooms", default=2)
    living_area = fields.Integer(string="Living Area (sqm)")
    facades = fields.Integer(string="Facades")
    garage = fields.Boolean(string="Garage", default=False)
    garden = fields.Boolean(string="Garden", default=False)
    garden_area = fields.Integer(string="Garden Area")
    garden_orientation = fields.Selection(
        string="Garden Orientation",
        selection=[
            ('north', 'North'),
            ('south', 'South'),
            ('east', 'East'),
            ('west', 'West')
        ],
        default="north"
    )
    status = fields.Selection(
        string="Status",
        selection=[
            ('new', 'New'),
            ('received', 'Offer Received'),
            ('accepted', 'Offer Accepted'),
            ('sold', 'Sold'),
            ('canceled', 'Canceled'),
        ],
        default='new',
        readonly=True
    )
    active = fields.Boolean(string="Active", default=False)
    property_type_id = fields.Many2one(
        "estate.property.type", string="Property Type", ondelete="cascade", index=True)
    sales_person = fields.Many2one(
        "res.users", string="Salesman", default=lambda self: self.env.user)
    buyer = fields.Many2one("res.users", string="Buyer")
    tag_ids = fields.Many2many("estate.tags", string="Tags")
    offer_ids = fields.One2many(
        "estate.property.offer", "property_id", string="Offer")
    total_area = fields.Float(
        string="Total Area", compute="_compute_total_area")

    _sql_constraints = [
        ('check_expected_price', 'CHECK(expected_price > 0)',
         'Expected price must be strictly positive.'),
        ('check_selling_price', 'CHECK(selling_price > 0)',
         'Selling Price must be strictly positive.'),
        ('check_best_offer', 'CHECK(best_offer > 0)',
         'Best Offer Price must be strictly positive.'),
    ]

    @api.depends('garden_area')
    def _compute_total_area(self):
        for rec in self:
            rec.total_area = rec.garden_area + rec.living_area

    @api.onchange('garden')
    def _onchange_garden(self):
        if self.garden:
            self.garden_area = 10
            self.garden_orientation = 'north'
        else:
            self.garden_area = 0
            self.garden_orientation = ''

    def sell_property(self):
        if self.status == 'canceled':
            raise exceptions.UserError("Canceled property cannot be sold")
        self.status = 'sold'

    def cancel_selling(self):
        self.status = 'canceled'

    @api.constrains('selling_price')
    def selling_price_check(self):
        for item in self:
            if float_compare(item.selling_price, item.best_offer, precision_rounding=0.01) <= 0:
                raise exceptions.ValidationError(
                    "Selling price is less than or similar Best Offer. Please make sure to set your Buyer offer price greater than your Best Offer.")

    def unlink(self):
        for item in self:
            if item.status == 'new' or item.status == 'canceled':
                return super(EstatePoperty, item).unlink()
        raise exceptions.UserError(
            "Only New and Canceled record can be deleted.")


class EstatePropertyType(models.Model):
    _name = "estate.property.type"
    _description = "Estate Property Type"
    _order = "name"

    name = fields.Char(string="Name", required=True)
    property_ids = fields.One2many(
        "estate.property", "property_type_id", "Estate Property")
    sequence = fields.Integer('Sequence', default=1,
                              help="Used to order stages. Lower is better.")
    offer_ids = fields.One2many(
        "estate.property.offer", "property_type_id", string="Property Offer")

    offer_count = fields.Integer(compute="_counting_offers", string=" Offers")
    _sql_constraints = [
        ('unique_name', 'unique(name)', 'Tag name must be unique'),
    ]

    @api.depends("offer_ids")
    def _counting_offers(self):
        for item in self:
            item.offer_count = self.env['estate.property.offer'].search_count([
                ('property_type_id', '=', item.id)])


class Tags(models.Model):
    _name = "estate.tags"
    _description = "Estate Tags"
    _order = "name"

    name = fields.Char()
    color = fields.Integer()

    _sql_constraints = [
        ('unique_name', 'unique(name)', 'Tag name must be unique'),
    ]


class EstatePropertyOffer(models.Model):
    _name = "estate.property.offer"
    _description = "Estate Property Offer"
    _order = "price desc"

    price = fields.Float(string="Price")
    status = fields.Selection(
        string="Status",
        selection=[
            ('accepted', 'Accepted'),
            ('refused', 'Refused')
        ]
    )
    partner_id = fields.Many2one(
        "res.partner", string="Partner", required=True)
    property_id = fields.Many2one(
        "estate.property", string="Estate Property", required=True, ondelete="cascade", index=True)
    validity = fields.Integer(default=7, string="Validity (Days)")
    date_deadline = fields.Date(compute="_create_date")
    property_type_id = fields.Integer(
        related="property_id.property_type_id.id", store=True)

    @api.model
    def create(self, val):
        self.env['estate.property'].browse(
            val['property_id']).status = 'received'
        return super(EstatePropertyOffer, self).create(val)

    @api.depends("validity")
    def _create_date(self):
        for rec in self:
            rec.date_deadline = timedelta(days=rec.validity) + date.today()

    def accept_buyer(self):
        self.status = 'accepted'
        for item in self.property_id:
            item.selling_price = self.price
            item.status = 'accepted'

    def reject_buyer(self):
        self.status = 'refused'
