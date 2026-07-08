# Copyright 2019 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class MaintenanceRequest(models.Model):

    _inherit = "maintenance.request"

    purchase_order_ids = fields.Many2many(
        "purchase.order",
        "maintenance_purchase_order",
        "maintenance_request_id",
        "purchase_order_id",
        groups="purchase.group_purchase_user",
        string="Purchase Orders",
        copy=False,
    )
    purchases_count = fields.Integer(
        compute="_compute_purchases_count",
        store=True,
        groups="purchase.group_purchase_user",
    )

    total_purchase_amount = fields.Monetary(
        compute="_compute_total_purchase_amount",
        store=True,
        groups="purchase.group_purchase_user",
        currency_field="currency_id",
    )

    currency_id = fields.Many2one(
        "res.currency",
        compute="_compute_currency_id",
        store=True,
        readonly=True,
    )

    def _get_company(self):
        """Deterministic company for the request.

        maintenance.request.company_id is optional, so derive the company
        from the request's own data -- its equipment, then its team, then
        its creator (always set) -- instead of the acting user's company,
        so a stored value never depends on who triggers the recompute.
        """
        self.ensure_one()
        return (
            self.company_id
            or self.equipment_id.company_id
            or self.maintenance_team_id.company_id
            or self.create_uid.company_id
        )

    @api.depends(
        "company_id.currency_id",
        "equipment_id.company_id.currency_id",
        "maintenance_team_id.company_id.currency_id",
        "create_uid.company_id.currency_id",
    )
    def _compute_currency_id(self):
        for record in self:
            record.currency_id = record._get_company().currency_id.id

    @api.depends(
        "purchase_order_ids.amount_total",
        "purchase_order_ids.currency_id",
        "currency_id",
        "purchase_order_ids.state",
    )
    def _compute_total_purchase_amount(self):
        date = self.env.context.get("actual_date") or fields.Date.today()
        for record in self:
            company = record._get_company()
            company_currency = record.currency_id
            total = sum(
                po.currency_id._convert(
                    po.amount_total,
                    company_currency,
                    company,
                    date,
                )
                for po in record.purchase_order_ids.filtered(
                    lambda po: po.state in ("purchase", "done")
                )
            )
            record.total_purchase_amount = total

    @api.depends("purchase_order_ids")
    def _compute_purchases_count(self):
        for record in self:
            record.purchases_count = len(record.purchase_order_ids.ids)
