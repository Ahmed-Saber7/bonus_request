# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ReContractType(models.Model):
    _name = "re.contract.type"
    _description = "Contract Type (Terms Template)"
    _order = "sequence, name"

    name = fields.Char(string="نوع العقد", required=True)
    code = fields.Char(string="الكود")
    sequence = fields.Integer(string="الترتيب", default=10)
    active = fields.Boolean(string="نشط", default=True)
    company_id = fields.Many2one(
        "res.company",
        string="الشركة",
        default=lambda self: self.env.company,
    )
    base_type = fields.Selection(
        [
            ("residential", "سكني"),
            ("commercial", "تجاري"),
        ],
        string="التصنيف الأساسي",
        help="يُزامَن مع حقل نوع العقد القياسي في العقد (سكني/تجاري).",
    )
    terms = fields.Html(
        string="الشروط والأحكام",
        help="هذه الشروط تُنسخ تلقائياً إلى العقد عند اختيار هذا النوع.",
    )
    note = fields.Text(string="ملاحظات داخلية")
    contract_ids = fields.One2many("re.contract", "contract_type_id", string="العقود")
    contract_count = fields.Integer(
        string="عدد العقود", compute="_compute_contract_count"
    )

    _sql_constraints = [
        ("code_company_uniq", "unique(code, company_id)", "كود نوع العقد مكرر لنفس الشركة."),
    ]

    @api.depends("contract_ids")
    def _compute_contract_count(self):
        for rec in self:
            rec.contract_count = len(rec.contract_ids)

    def action_view_contracts(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.name,
            "res_model": "re.contract",
            "view_mode": "list,form",
            "domain": [("contract_type_id", "=", self.id)],
            "context": {"default_contract_type_id": self.id},
        }
