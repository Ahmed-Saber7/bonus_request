# -*- coding: utf-8 -*-
from odoo import api, fields, models

_ONES = ("", "واحد", "اثنان", "ثلاثة", "أربعة", "خمسة", "ستة", "سبعة", "ثمانية", "تسعة", "عشرة",
         "أحد عشر", "اثنا عشر", "ثلاثة عشر", "أربعة عشر", "خمسة عشر", "ستة عشر", "سبعة عشر", "ثمانية عشر", "تسعة عشر")
_TENS = ("", "", "عشرون", "ثلاثون", "أربعون", "خمسون", "ستون", "سبعون", "ثمانون", "تسعون")
_HUNDREDS = ("", "مائة", "مائتان", "ثلاثمائة", "أربعمائة", "خمسمائة", "ستمائة", "سبعمائة", "ثمانمائة", "تسعمائة")


def _chunk_to_ar(n):
    n = int(n)
    if n <= 0:
        return ""
    parts = []
    hundreds, rest = n // 100, n % 100
    if hundreds:
        parts.append(_HUNDREDS[hundreds])
    if rest:
        if rest < 20:
            parts.append(_ONES[rest])
        else:
            ones, tens = rest % 10, rest // 10
            parts.append(f"{_ONES[ones]} و{_TENS[tens]}" if ones else _TENS[tens])
    return " و".join(parts)


def amount_to_text_ar(amount, currency_name="دينار كويتي", decimals=3):
    try:
        amount = float(amount or 0.0)
    except (TypeError, ValueError):
        amount = 0.0
    if amount < 0:
        amount = abs(amount)
    major = int(amount)
    factor = 10 ** int(decimals)
    minor = int(round((amount - major) * factor))
    if minor >= factor:
        major += 1
        minor = 0
    if major == 0 and minor == 0:
        return f"فقط صفر {currency_name} لاغير"
    parts = []
    millions = major // 1_000_000
    thousands = (major % 1_000_000) // 1000
    rem = major % 1000
    if millions:
        w = _chunk_to_ar(millions)
        parts.append("مليون" if millions == 1 else "مليونان" if millions == 2 else (f"{w} ملايين" if 3 <= millions <= 10 else f"{w} مليون"))
    if thousands:
        w = _chunk_to_ar(thousands)
        parts.append("ألف" if thousands == 1 else "ألفان" if thousands == 2 else (f"{w} آلاف" if 3 <= thousands <= 10 else f"{w} ألف"))
    if rem:
        parts.append(_chunk_to_ar(rem))
    body = " و".join([p for p in parts if p])
    text = f"{body} {currency_name}"
    if minor:
        text = f"{text} و{_chunk_to_ar(minor)} فلس"
    return f"فقط {text} لاغير"


class ReContract(models.Model):
    _inherit = "re.contract"

    contract_type_id = fields.Many2one(
        "re.contract.type",
        string="نوع العقد (الشروط)",
        ondelete="restrict",
        help="اختر نوع العقد وستُنزَّل شروطه وأحكامه تلقائياً في حقل الشروط.",
    )

    # ------------------------------------------------------------------
    # Auto-fill terms from the selected contract type
    # ------------------------------------------------------------------
    @api.onchange("contract_type_id")
    def _onchange_contract_type_id(self):
        for rec in self:
            ctype = rec.contract_type_id
            if not ctype:
                continue
            if ctype.terms:
                rec.terms = ctype.terms
            if ctype.base_type:
                rec.contract_type = ctype.base_type

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("contract_type_id") and not vals.get("terms"):
                ctype = self.env["re.contract.type"].browse(vals["contract_type_id"])
                if ctype.exists() and ctype.terms:
                    vals["terms"] = ctype.terms
                if ctype.exists() and ctype.base_type and not vals.get("contract_type"):
                    vals["contract_type"] = ctype.base_type
        return super().create(vals_list)

    def write(self, vals):
        # Only when the type itself changes (and terms not sent explicitly),
        # refresh the contract's terms snapshot from the new type.
        if vals.get("contract_type_id") and "terms" not in vals:
            ctype = self.env["re.contract.type"].browse(vals["contract_type_id"])
            if ctype.exists() and ctype.terms:
                vals = dict(vals, terms=ctype.terms)
                if ctype.base_type and "contract_type" not in vals:
                    vals["contract_type"] = ctype.base_type
        return super().write(vals)

    def action_refresh_terms_from_type(self):
        """Re-copy terms from the contract type (manual refresh button)."""
        for rec in self:
            if rec.contract_type_id and rec.contract_type_id.terms:
                rec.terms = rec.contract_type_id.terms
                if rec.contract_type_id.base_type:
                    rec.contract_type = rec.contract_type_id.base_type
        return True

    # ------------------------------------------------------------------
    # Dynamic print data: header from company settings
    # ------------------------------------------------------------------
    def _re_contract_print_data(self):
        self.ensure_one()
        company = self.company_id or self.env.company
        tenant = self.tenant_id
        unit = self.unit_id
        prop = self.property_id

        # --- Header: 100% from Settings > Companies (res.company) ---
        address_parts = []
        for val in (company.street, company.street2, company.city):
            if val:
                address_parts.append(val)
        if company.state_id:
            address_parts.append(company.state_id.name)
        if company.country_id:
            address_parts.append(company.country_id.name)
        if company.zip:
            address_parts.append(company.zip)

        logo_src = False
        if company.logo:
            logo_b64 = company.logo
            if isinstance(logo_b64, bytes):
                logo_b64 = logo_b64.decode("ascii")
            logo_src = f"data:image/png;base64,{logo_b64}"

        # --- Body ---
        street = ""
        if prop:
            street = prop.street_name or prop.street or ""
        address_parts_unit = []
        if prop and prop.name:
            address_parts_unit.append(prop.name)
        if street:
            address_parts_unit.append(f"بشارع {street}")
        if unit and unit.name:
            address_parts_unit.append(f"وحدة رقم {unit.name}")
        if unit and unit.floor:
            address_parts_unit.append(f"بالدور {unit.floor}")

        currency = self.currency_id
        is_kwd = bool(currency and currency.name == "KWD")
        currency_name = "دينار كويتي" if is_kwd else (
            (currency.currency_unit_label or currency.name) if currency else "دينار كويتي"
        )
        decimals = 3 if is_kwd else 2
        rent = self.rent_final or self.rent_amount or 0.0

        def _partner_field(partner, fname):
            if partner and fname in partner._fields:
                val = partner[fname]
                if val:
                    return val.name if hasattr(val, "name") else val
            return ""

        return {
            # header (company settings)
            "company_name": company.name or "",
            "logo_src": logo_src,
            "company_address": " — ".join(address_parts),
            "company_phone": company.phone or "",
            "company_email": company.email or "",
            "company_website": company.website or "",
            # contract body
            "contract_no": self.name or "",
            "type_name": self.contract_type_id.name if self.contract_type_id else "",
            "landlord": company.name or "",
            "tenant": tenant.name if tenant else "",
            "tenant_civil": _partner_field(tenant, "civil_id"),
            "tenant_nationality": _partner_field(tenant, "nationality_id"),
            "tenant_phone": (tenant.phone or "") if tenant else "",
            "tenant_job": _partner_field(tenant, "function"),
            "unit_desc": " ".join(address_parts_unit),
            "unit_name": unit.name if unit else "",
            "rent": f"{rent:,.{decimals}f}",
            "rent_words": amount_to_text_ar(rent, currency_name, decimals=decimals),
            "date_start": self.date_start.strftime("%Y-%m-%d") if self.date_start else "",
            "date_end": self.date_end.strftime("%Y-%m-%d") if self.date_end else "",
        }
