# -*- coding: utf-8 -*-
{
    "name": "أنواع العقود والشروط الديناميكية",
    "version": "19.0.1.1.3",
    "category": "Real Estate",
    "summary": "نوع عقد له شروط وأحكام — اختيار النوع في العقد ينزّل الشروط تلقائياً",
    "description": """
أنواع عقود ديناميكية:
- كل نوع عقد له شروطه وأحكامه الخاصة (HTML قابل للتحرير)
- عند اختيار نوع العقد في عقد الإيجار تُنسخ الشروط تلقائياً إلى حقل الشروط
- نسخة العقد تبقى ثابتة: تعديل شروط النوع لاحقاً لا يغيّر العقود القديمة
- زر لتحديث شروط العقد من نوعه عند الحاجة
    """,
    "author": "Bidayat / Dynamics Solutions",
    "license": "LGPL-3",
    "depends": ["real_estate_management"],
    "data": [
        "security/ir.model.access.csv",
        "data/re_contract_type_data.xml",
        "views/re_contract_type_views.xml",
        "views/re_contract_views.xml",
        "report/contract_report.xml",
        "report/contract_templates.xml",
    ],
    "installable": True,
    "application": False,
}
