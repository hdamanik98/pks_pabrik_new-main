# -*- coding: utf-8 -*-
{
    'name': 'PKS Pabrik - Palm Oil Mill Management',
    'version': '19.0.1.0.0',
    'category': 'Manufacturing/Agriculture',
    'summary': 'Complete Palm Oil Mill Management System',
    'description': """
        Modul PKS (Pabrik Kelapa Sawit) Lengkap
        ======================================
        
        Fitur:
        - Timbangan dengan State Machine
        - Manajemen Supplier dengan Portal
        - Tracking Truk dengan RFID
        - Quality Control dengan Grading Otomatis
        - LHP (Laporan Harian Pabrik) dengan OER/KER
        - REST API untuk integrasi
        - Kiosk timbangan mobile-responsive
        - Reports: Slip Timbang & LHP
    """,
    'author': 'PT. Sawit Nusantara',
    'website': 'https://www.sawitnusantara.co.id',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'portal',
        'web',
        'mail',
        'stock',
        'account',
        'hr',
    ],
    'data': [
        # Security
        'security/pks_security.xml',
        'security/ir.model.access.csv',
        
        # Data
        'data/pks_sequence.xml',
        'data/pks_grade_data.xml',
        
        # Views
        'views/pks_supplier_views.xml',
        'views/pks_truck_views.xml',
        'views/pks_weighbridge_views.xml',
        'views/pks_quality_views.xml',
        'views/pks_lhp_views.xml',
        'views/dashboard_views.xml',
        'views/menu_views.xml',
        
        # Reports
        'reports/slip_timbang.xml',
        'reports/lhp_report.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'pks_pabrik/static/src/components/kiosk/*.js',
            'pks_pabrik/static/src/components/kiosk/*.xml',
            'pks_pabrik/static/src/components/kiosk/*.scss',
        ],
    },
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
