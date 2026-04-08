# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request, Response
import json
import logging

_logger = logging.getLogger(__name__)


class PKSPortalController(http.Controller):
    """
    Portal Controller untuk Supplier
    ================================
    """
    
    @http.route('/my/supplier/<int:supplier_id>', type='http', auth='user', website=True)
    def portal_supplier_detail(self, supplier_id, **kw):
        """Halaman detail supplier di portal"""
        supplier = request.env['pks.supplier'].sudo().browse(supplier_id)
        
        if not supplier.exists():
            return request.not_found()
        
        # Cek akses
        if not request.env.user.has_group('pks_pabrik.group_pks_supplier_portal'):
            return request.redirect('/')
        
        values = {
            'supplier': supplier,
            'page_name': 'supplier_detail',
        }
        
        return request.render('pks_pabrik.portal_supplier_detail', values)
    
    @http.route('/my/supplier/weighbridges', type='http', auth='user', website=True)
    def portal_supplier_weighbridges(self, **kw):
        """Daftar timbangan supplier di portal"""
        # Cari supplier yang terhubung dengan user
        supplier = request.env['pks.supplier'].sudo().search([
            ('user_id', '=', request.env.user.id),
        ], limit=1)
        
        if not supplier:
            return request.redirect('/')
        
        weighbridges = request.env['pks.weighbridge'].sudo().search([
            ('supplier_id', '=', supplier.id),
            ('state', '=', 'done'),
        ], order='create_date desc')
        
        values = {
            'supplier': supplier,
            'weighbridges': weighbridges,
            'page_name': 'supplier_weighbridges',
        }
        
        return request.render('pks_pabrik.portal_supplier_weighbridges', values)
    
    @http.route('/my/supplier/dashboard', type='http', auth='user', website=True)
    def portal_supplier_dashboard(self, **kw):
        """Dashboard supplier di portal"""
        supplier = request.env['pks.supplier'].sudo().search([
            ('user_id', '=', request.env.user.id),
        ], limit=1)
        
        if not supplier:
            return request.redirect('/')
        
        # Hitung statistik
        total_deliveries = supplier.total_deliveries
        total_weight = supplier.total_weight
        average_quality = supplier.average_quality
        
        values = {
            'supplier': supplier,
            'total_deliveries': total_deliveries,
            'total_weight': total_weight,
            'average_quality': average_quality,
            'page_name': 'supplier_dashboard',
        }
        
        return request.render('pks_pabrik.portal_supplier_dashboard', values)


class PKSKioskController(http.Controller):
    """
    Controller untuk Kiosk Timbangan
    ================================
    """
    
    @http.route('/pks/kiosk', type='http', auth='public', website=True)
    def kiosk_main(self, **kw):
        """Halaman utama kiosk timbangan"""
        return request.render('pks_pabrik.kiosk_main', {})
    
    @http.route('/pks/kiosk/weigh-in', type='http', auth='public', website=True)
    def kiosk_weigh_in(self, **kw):
        """Halaman timbang masuk kiosk"""
        return request.render('pks_pabrik.kiosk_weigh_in', {})
    
    @http.route('/pks/kiosk/weigh-out', type='http', auth='public', website=True)
    def kiosk_weigh_out(self, **kw):
        """Halaman timbang keluar kiosk"""
        return request.render('pks_pabrik.kiosk_weigh_out', {})
    
    @http.route('/pks/kiosk/rfid-scan', type='json', auth='public', methods=['POST'], csrf=False)
    def kiosk_rfid_scan(self, **kw):
        """Handle RFID scan dari kiosk"""
        rfid_tag = kw.get('rfid_tag')
        
        if not rfid_tag:
            return {'status': 'error', 'message': 'RFID tag tidak ditemukan'}
        
        # Proses RFID scan
        result = request.env['pks.truck'].sudo().process_rfid_scan(rfid_tag)
        
        return result
