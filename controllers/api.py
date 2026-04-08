# -*- coding: utf-8 -*-
from odoo import http, _, exceptions
from odoo.http import request, Response
import json
import logging
import base64
from functools import wraps

_logger = logging.getLogger(__name__)


def require_api_auth(func):
    """Decorator untuk memerlukan API authentication"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth_header = request.httprequest.headers.get('Authorization')
        
        if not auth_header:
            return Response(
                json.dumps({'error': 'Authorization header missing'}),
                status=401,
                content_type='application/json'
            )
        
        try:
            # Basic Auth: Basic base64(username:password)
            auth_type, auth_string = auth_header.split(' ', 1)
            if auth_type.lower() != 'basic':
                return Response(
                    json.dumps({'error': 'Invalid authentication type'}),
                    status=401,
                    content_type='application/json'
                )
            
            decoded = base64.b64decode(auth_string).decode('utf-8')
            username, password = decoded.split(':', 1)
            
            # Authenticate
            uid = request.session.authenticate(request.db, username, password)
            if not uid:
                return Response(
                    json.dumps({'error': 'Invalid credentials'}),
                    status=401,
                    content_type='application/json'
                )
            
            request.uid = uid
            return func(*args, **kwargs)
            
        except Exception as e:
            _logger.error(f'API Auth Error: {str(e)}')
            return Response(
                json.dumps({'error': 'Authentication failed'}),
                status=401,
                content_type='application/json'
            )
    
    return wrapper


def require_api_token(func):
    """Decorator untuk memerlukan API Token"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = request.httprequest.headers.get('X-API-Token')
        
        if not token:
            return Response(
                json.dumps({'error': 'API Token missing'}),
                status=401,
                content_type='application/json'
            )
        
        # Validasi token (implementasi sesuai kebutuhan)
        valid_token = request.env['ir.config_parameter'].sudo().get_param('pks.api_token')
        
        if token != valid_token:
            return Response(
                json.dumps({'error': 'Invalid API Token'}),
                status=401,
                content_type='application/json'
            )
        
        return func(*args, **kwargs)
    
    return wrapper


def json_response(data, status=200):
    """Helper untuk membuat JSON response"""
    return Response(
        json.dumps(data, default=str),
        status=status,
        content_type='application/json'
    )


class PKSAPIController(http.Controller):
    """
    REST API Controller untuk PKS Pabrik
    ====================================
    Authentication: Basic Auth atau API Token
    """
    
    # ============================================================
    # SUPPLIER API
    # ============================================================
    
    @http.route('/api/v1/pks/suppliers', type='http', auth='none', methods=['GET'], csrf=False)
    @require_api_auth
    def api_get_suppliers(self, **kw):
        """Get daftar supplier"""
        try:
            domain = [('active', '=', True)]
            
            # Filter
            if kw.get('supplier_type'):
                domain.append(('supplier_type', '=', kw.get('supplier_type')))
            if kw.get('verification_state'):
                domain.append(('verification_state', '=', kw.get('verification_state')))
            if kw.get('search'):
                domain.append('|')
                domain.append(('name', 'ilike', kw.get('search')))
                domain.append(('code', 'ilike', kw.get('search')))
            
            suppliers = request.env['pks.supplier'].sudo().search(domain)
            
            data = []
            for supplier in suppliers:
                data.append({
                    'id': supplier.id,
                    'name': supplier.name,
                    'code': supplier.code,
                    'supplier_type': supplier.supplier_type,
                    'verification_state': supplier.verification_state,
                    'phone': supplier.phone,
                    'email': supplier.email,
                    'total_deliveries': supplier.total_deliveries,
                    'total_weight': supplier.total_weight,
                })
            
            return json_response({'status': 'success', 'data': data})
            
        except Exception as e:
            _logger.error(f'API Error: {str(e)}')
            return json_response({'status': 'error', 'message': str(e)}, 500)
    
    @http.route('/api/v1/pks/suppliers/<int:supplier_id>', type='http', auth='none', methods=['GET'], csrf=False)
    @require_api_auth
    def api_get_supplier_detail(self, supplier_id, **kw):
        """Get detail supplier"""
        try:
            supplier = request.env['pks.supplier'].sudo().browse(supplier_id)
            
            if not supplier.exists():
                return json_response({'status': 'error', 'message': 'Supplier not found'}, 404)
            
            data = {
                'id': supplier.id,
                'name': supplier.name,
                'code': supplier.code,
                'supplier_type': supplier.supplier_type,
                'verification_state': supplier.verification_state,
                'street': supplier.street,
                'city': supplier.city,
                'phone': supplier.phone,
                'email': supplier.email,
                'npwp': supplier.npwp,
                'total_deliveries': supplier.total_deliveries,
                'total_weight': supplier.total_weight,
                'average_quality': supplier.average_quality,
            }
            
            return json_response({'status': 'success', 'data': data})
            
        except Exception as e:
            return json_response({'status': 'error', 'message': str(e)}, 500)
    
    @http.route('/api/v1/pks/suppliers', type='http', auth='none', methods=['POST'], csrf=False)
    @require_api_auth
    def api_create_supplier(self, **kw):
        """Create supplier baru"""
        try:
            data = json.loads(request.httprequest.data)
            
            required_fields = ['name', 'code', 'supplier_type']
            for field in required_fields:
                if field not in data:
                    return json_response({'status': 'error', 'message': f'{field} is required'}, 400)
            
            supplier = request.env['pks.supplier'].sudo().create({
                'name': data['name'],
                'code': data['code'],
                'supplier_type': data['supplier_type'],
                'phone': data.get('phone'),
                'email': data.get('email'),
                'street': data.get('street'),
                'city': data.get('city'),
                'npwp': data.get('npwp'),
            })
            
            return json_response({
                'status': 'success',
                'message': 'Supplier created successfully',
                'data': {'id': supplier.id, 'name': supplier.name}
            }, 201)
            
        except Exception as e:
            return json_response({'status': 'error', 'message': str(e)}, 500)
    
    # ============================================================
    # TRUCK API
    # ============================================================
    
    @http.route('/api/v1/pks/trucks', type='http', auth='none', methods=['GET'], csrf=False)
    @require_api_auth
    def api_get_trucks(self, **kw):
        """Get daftar truk"""
        try:
            domain = [('active', '=', True)]
            
            if kw.get('current_state'):
                domain.append(('current_state', '=', kw.get('current_state')))
            if kw.get('search'):
                domain.append('|')
                domain.append(('name', 'ilike', kw.get('search')))
                domain.append(('rfid_tag', 'ilike', kw.get('search')))
            
            trucks = request.env['pks.truck'].sudo().search(domain)
            
            data = []
            for truck in trucks:
                data.append({
                    'id': truck.id,
                    'plate_number': truck.name,
                    'rfid_tag': truck.rfid_tag,
                    'truck_type': truck.truck_type,
                    'current_state': truck.current_state,
                    'driver': truck.driver_id.name if truck.driver_id else None,
                    'total_trips': truck.total_trips,
                    'total_weight_delivered': truck.total_weight_delivered,
                })
            
            return json_response({'status': 'success', 'data': data})
            
        except Exception as e:
            return json_response({'status': 'error', 'message': str(e)}, 500)
    
    @http.route('/api/v1/pks/trucks/rfid/<rfid_tag>', type='http', auth='none', methods=['GET'], csrf=False)
    @require_api_auth
    def api_get_truck_by_rfid(self, rfid_tag, **kw):
        """Get truk berdasarkan RFID"""
        try:
            result = request.env['pks.truck'].sudo().find_by_rfid(rfid_tag)
            
            if result['status'] == 'error':
                return json_response(result, 404)
            
            truck = request.env['pks.truck'].sudo().browse(result['truck_id'])
            
            data = {
                'id': truck.id,
                'plate_number': truck.name,
                'rfid_tag': truck.rfid_tag,
                'truck_type': truck.truck_type,
                'current_state': truck.current_state,
                'driver': truck.driver_id.name if truck.driver_id else None,
                'capacity_kg': truck.capacity_kg,
            }
            
            return json_response({'status': 'success', 'data': data})
            
        except Exception as e:
            return json_response({'status': 'error', 'message': str(e)}, 500)
    
    @http.route('/api/v1/pks/trucks', type='http', auth='none', methods=['POST'], csrf=False)
    @require_api_auth
    def api_create_truck(self, **kw):
        """Create truk baru"""
        try:
            data = json.loads(request.httprequest.data)
            
            required_fields = ['name', 'rfid_tag', 'truck_type']
            for field in required_fields:
                if field not in data:
                    return json_response({'status': 'error', 'message': f'{field} is required'}, 400)
            
            truck = request.env['pks.truck'].sudo().create({
                'name': data['name'],
                'rfid_tag': data['rfid_tag'],
                'truck_type': data['truck_type'],
                'brand': data.get('brand'),
                'capacity_kg': data.get('capacity_kg'),
                'ownership': data.get('ownership', 'third_party'),
            })
            
            return json_response({
                'status': 'success',
                'message': 'Truck created successfully',
                'data': {'id': truck.id, 'plate_number': truck.name}
            }, 201)
            
        except Exception as e:
            return json_response({'status': 'error', 'message': str(e)}, 500)
    
    # ============================================================
    # WEIGHBRIDGE API
    # ============================================================
    
    @http.route('/api/v1/pks/weighbridges', type='http', auth='none', methods=['GET'], csrf=False)
    @require_api_auth
    def api_get_weighbridges(self, **kw):
        """Get daftar timbangan"""
        try:
            domain = []
            
            if kw.get('state'):
                domain.append(('state', '=', kw.get('state')))
            if kw.get('supplier_id'):
                domain.append(('supplier_id', '=', int(kw.get('supplier_id'))))
            if kw.get('truck_id'):
                domain.append(('truck_id', '=', int(kw.get('truck_id'))))
            if kw.get('date_from'):
                domain.append(('create_date', '>=', kw.get('date_from')))
            if kw.get('date_to'):
                domain.append(('create_date', '<=', kw.get('date_to')))
            
            weighbridges = request.env['pks.weighbridge'].sudo().search(domain, limit=100)
            
            data = []
            for wb in weighbridges:
                data.append({
                    'id': wb.id,
                    'ticket_number': wb.name,
                    'state': wb.state,
                    'supplier': {'id': wb.supplier_id.id, 'name': wb.supplier_id.name},
                    'truck': {'id': wb.truck_id.id, 'plate': wb.truck_id.name, 'rfid': wb.truck_id.rfid_tag},
                    'weight_in': wb.weight_in,
                    'weight_in_datetime': wb.weight_in_datetime,
                    'weight_out': wb.weight_out,
                    'weight_out_datetime': wb.weight_out_datetime,
                    'netto_weight': wb.netto_weight,
                    'tbs_type': wb.tbs_type,
                })
            
            return json_response({'status': 'success', 'data': data})
            
        except Exception as e:
            return json_response({'status': 'error', 'message': str(e)}, 500)
    
    @http.route('/api/v1/pks/weighbridges', type='http', auth='none', methods=['POST'], csrf=False)
    @require_api_auth
    def api_create_weighbridge(self, **kw):
        """Create tiket timbangan baru"""
        try:
            data = json.loads(request.httprequest.data)
            
            required_fields = ['supplier_id', 'truck_id', 'tbs_type']
            for field in required_fields:
                if field not in data:
                    return json_response({'status': 'error', 'message': f'{field} is required'}, 400)
            
            weighbridge = request.env['pks.weighbridge'].sudo().create({
                'supplier_id': data['supplier_id'],
                'truck_id': data['truck_id'],
                'tbs_type': data['tbs_type'],
                'estate_block': data.get('estate_block'),
                'harvest_date': data.get('harvest_date'),
                'notes': data.get('notes'),
            })
            
            return json_response({
                'status': 'success',
                'message': 'Weighbridge ticket created',
                'data': {
                    'id': weighbridge.id,
                    'ticket_number': weighbridge.name,
                    'state': weighbridge.state,
                }
            }, 201)
            
        except Exception as e:
            return json_response({'status': 'error', 'message': str(e)}, 500)
    
    @http.route('/api/v1/pks/weighbridges/<int:weighbridge_id>/weigh-in', type='http', auth='none', methods=['POST'], csrf=False)
    @require_api_auth
    def api_weigh_in(self, weighbridge_id, **kw):
        """Timbang masuk"""
        try:
            data = json.loads(request.httprequest.data)
            
            if 'weight_in' not in data:
                return json_response({'status': 'error', 'message': 'weight_in is required'}, 400)
            
            weighbridge = request.env['pks.weighbridge'].sudo().browse(weighbridge_id)
            
            if not weighbridge.exists():
                return json_response({'status': 'error', 'message': 'Weighbridge not found'}, 404)
            
            weighbridge.write({'weight_in': data['weight_in']})
            weighbridge.action_weigh_in()
            
            return json_response({
                'status': 'success',
                'message': 'Weigh in recorded',
                'data': {
                    'ticket_number': weighbridge.name,
                    'weight_in': weighbridge.weight_in,
                    'weight_in_datetime': weighbridge.weight_in_datetime,
                }
            })
            
        except Exception as e:
            return json_response({'status': 'error', 'message': str(e)}, 500)
    
    @http.route('/api/v1/pks/weighbridges/<int:weighbridge_id>/weigh-out', type='http', auth='none', methods=['POST'], csrf=False)
    @require_api_auth
    def api_weigh_out(self, weighbridge_id, **kw):
        """Timbang keluar"""
        try:
            data = json.loads(request.httprequest.data)
            
            if 'weight_out' not in data:
                return json_response({'status': 'error', 'message': 'weight_out is required'}, 400)
            
            weighbridge = request.env['pks.weighbridge'].sudo().browse(weighbridge_id)
            
            if not weighbridge.exists():
                return json_response({'status': 'error', 'message': 'Weighbridge not found'}, 404)
            
            weighbridge.write({'weight_out': data['weight_out']})
            weighbridge.action_weigh_out()
            
            return json_response({
                'status': 'success',
                'message': 'Weigh out recorded',
                'data': {
                    'ticket_number': weighbridge.name,
                    'weight_out': weighbridge.weight_out,
                    'weight_out_datetime': weighbridge.weight_out_datetime,
                    'netto_weight': weighbridge.netto_weight,
                }
            })
            
        except Exception as e:
            return json_response({'status': 'error', 'message': str(e)}, 500)
    
    # ============================================================
    # QUALITY API
    # ============================================================
    
    @http.route('/api/v1/pks/qualities', type='http', auth='none', methods=['GET'], csrf=False)
    @require_api_auth
    def api_get_qualities(self, **kw):
        """Get daftar quality control"""
        try:
            domain = []
            
            if kw.get('state'):
                domain.append(('state', '=', kw.get('state')))
            if kw.get('final_grade'):
                domain.append(('final_grade', '=', kw.get('final_grade')))
            
            qualities = request.env['pks.quality'].sudo().search(domain, limit=100)
            
            data = []
            for q in qualities:
                data.append({
                    'id': q.id,
                    'analysis_number': q.name,
                    'state': q.state,
                    'weighbridge_id': q.weighbridge_id.id,
                    'supplier': q.supplier_id.name,
                    'final_grade': q.final_grade,
                    'grade_score': q.grade_score,
                    'deduction_factor': q.deduction_factor,
                    'weight_deduction_kg': q.weight_deduction_kg,
                    'net_weight_after_deduction': q.net_weight_after_deduction,
                })
            
            return json_response({'status': 'success', 'data': data})
            
        except Exception as e:
            return json_response({'status': 'error', 'message': str(e)}, 500)
    
    @http.route('/api/v1/pks/qualities', type='http', auth='none', methods=['POST'], csrf=False)
    @require_api_auth
    def api_create_quality(self, **kw):
        """Create quality control baru"""
        try:
            data = json.loads(request.httprequest.data)
            
            required_fields = ['weighbridge_id', 'sample_weight']
            for field in required_fields:
                if field not in data:
                    return json_response({'status': 'error', 'message': f'{field} is required'}, 400)
            
            quality = request.env['pks.quality'].sudo().create({
                'weighbridge_id': data['weighbridge_id'],
                'sample_weight': data['sample_weight'],
                'sampler_id': data.get('sampler_id'),
                'analyst_id': data.get('analyst_id'),
                'moisture_content': data.get('moisture_content'),
                'impurities_percent': data.get('impurities_percent'),
                'unripe_percent': data.get('unripe_percent'),
                'rotten_percent': data.get('rotten_percent'),
                'empty_bunches_percent': data.get('empty_bunches_percent'),
                'small_particles_percent': data.get('small_particles_percent'),
                'notes': data.get('notes'),
            })
            
            return json_response({
                'status': 'success',
                'message': 'Quality control created',
                'data': {
                    'id': quality.id,
                    'analysis_number': quality.name,
                    'final_grade': quality.final_grade,
                    'grade_score': quality.grade_score,
                }
            }, 201)
            
        except Exception as e:
            return json_response({'status': 'error', 'message': str(e)}, 500)
    
    # ============================================================
    # LHP API
    # ============================================================
    
    @http.route('/api/v1/pks/lhps', type='http', auth='none', methods=['GET'], csrf=False)
    @require_api_auth
    def api_get_lhps(self, **kw):
        """Get daftar LHP"""
        try:
            domain = []
            
            if kw.get('state'):
                domain.append(('state', '=', kw.get('state')))
            if kw.get('date'):
                domain.append(('date', '=', kw.get('date')))
            if kw.get('date_from'):
                domain.append(('date', '>=', kw.get('date_from')))
            if kw.get('date_to'):
                domain.append(('date', '<=', kw.get('date_to')))
            
            lhps = request.env['pks.lhp'].sudo().search(domain, limit=100)
            
            data = []
            for lhp in lhps:
                data.append({
                    'id': lhp.id,
                    'lhp_number': lhp.name,
                    'date': lhp.date,
                    'shift': lhp.shift,
                    'state': lhp.state,
                    'tbs_processed': lhp.tbs_processed,
                    'cpo_produced': lhp.cpo_produced,
                    'kernel_produced': lhp.kernel_produced,
                    'oer_percent': lhp.oer_percent,
                    'ker_percent': lhp.ker_percent,
                    'total_er_percent': lhp.total_er_percent,
                })
            
            return json_response({'status': 'success', 'data': data})
            
        except Exception as e:
            return json_response({'status': 'error', 'message': str(e)}, 500)
    
    @http.route('/api/v1/pks/lhps/<int:lhp_id>', type='http', auth='none', methods=['GET'], csrf=False)
    @require_api_auth
    def api_get_lhp_detail(self, lhp_id, **kw):
        """Get detail LHP"""
        try:
            lhp = request.env['pks.lhp'].sudo().browse(lhp_id)
            
            if not lhp.exists():
                return json_response({'status': 'error', 'message': 'LHP not found'}, 404)
            
            data = {
                'id': lhp.id,
                'lhp_number': lhp.name,
                'date': lhp.date,
                'shift': lhp.shift,
                'state': lhp.state,
                'tbs_in_internal': lhp.tbs_in_internal,
                'tbs_in_external': lhp.tbs_in_external,
                'tbs_in_plasma': lhp.tbs_in_plasma,
                'tbs_in_total': lhp.tbs_in_total,
                'tbs_processed': lhp.tbs_processed,
                'tbs_remaining': lhp.tbs_remaining,
                'cpo_produced': lhp.cpo_produced,
                'cpo_ffa': lhp.cpo_ffa,
                'kernel_produced': lhp.kernel_produced,
                'oer_percent': lhp.oer_percent,
                'ker_percent': lhp.ker_percent,
                'total_er_percent': lhp.total_er_percent,
                'oer_variance': lhp.oer_variance,
                'ker_variance': lhp.ker_variance,
                'throughput_per_hour': lhp.throughput_per_hour,
                'downtime_hours': lhp.downtime_hours,
            }
            
            return json_response({'status': 'success', 'data': data})
            
        except Exception as e:
            return json_response({'status': 'error', 'message': str(e)}, 500)
    
    # ============================================================
    # DASHBOARD API
    # ============================================================
    
    @http.route('/api/v1/pks/dashboard', type='http', auth='none', methods=['GET'], csrf=False)
    @require_api_auth
    def api_dashboard(self, **kw):
        """Get dashboard data"""
        try:
            today = fields.Date.today()
            
            # Statistik hari ini
            today_weighbridges = request.env['pks.weighbridge'].sudo().search([
                ('create_date', '>=', today),
                ('state', '=', 'done'),
            ])
            
            today_lhp = request.env['pks.lhp'].sudo().search([
                ('date', '=', today),
                ('state', '=', 'done'),
            ], limit=1)
            
            data = {
                'today': {
                    'total_weighbridges': len(today_weighbridges),
                    'total_tbs_weight': sum(wb.netto_weight for wb in today_weighbridges),
                    'total_suppliers': len(set(wb.supplier_id.id for wb in today_weighbridges)),
                    'oer': today_lhp.oer_percent if today_lhp else 0,
                    'ker': today_lhp.ker_percent if today_lhp else 0,
                },
                'truck_status': {
                    'available': request.env['pks.truck'].sudo().search_count([('current_state', '=', 'available')]),
                    'in_weighbridge': request.env['pks.truck'].sudo().search_count([('current_state', '=', 'in_weighbridge')]),
                    'in_mill': request.env['pks.truck'].sudo().search_count([('current_state', '=', 'in_mill')]),
                    'maintenance': request.env['pks.truck'].sudo().search_count([('current_state', '=', 'maintenance')]),
                },
                'weighbridge_by_state': {
                    'draft': request.env['pks.weighbridge'].sudo().search_count([('state', '=', 'draft')]),
                    'weighing_in': request.env['pks.weighbridge'].sudo().search_count([('state', '=', 'weighing_in')]),
                    'waiting_unload': request.env['pks.weighbridge'].sudo().search_count([('state', '=', 'waiting_unload')]),
                    'weighing_out': request.env['pks.weighbridge'].sudo().search_count([('state', '=', 'weighing_out')]),
                    'done': request.env['pks.weighbridge'].sudo().search_count([('state', '=', 'done')]),
                }
            }
            
            return json_response({'status': 'success', 'data': data})
            
        except Exception as e:
            return json_response({'status': 'error', 'message': str(e)}, 500)
    
    # ============================================================
    # AUTH API
    # ============================================================
    
    @http.route('/api/v1/pks/auth/token', type='http', auth='none', methods=['POST'], csrf=False)
    def api_get_token(self, **kw):
        """Get API Token (untuk API Key authentication)"""
        try:
            data = json.loads(request.httprequest.data)
            
            username = data.get('username')
            password = data.get('password')
            
            if not username or not password:
                return json_response({'status': 'error', 'message': 'Username and password required'}, 400)
            
            uid = request.session.authenticate(request.db, username, password)
            
            if not uid:
                return json_response({'status': 'error', 'message': 'Invalid credentials'}, 401)
            
            # Generate token (simplified - implement proper JWT in production)
            import hashlib
            import time
            token_string = f"{username}:{time.time()}:{request.db}"
            token = hashlib.sha256(token_string.encode()).hexdigest()
            
            # Simpan token (implementasi sesuai kebutuhan)
            
            return json_response({
                'status': 'success',
                'data': {
                    'token': token,
                    'expires_in': 3600,
                }
            })
            
        except Exception as e:
            return json_response({'status': 'error', 'message': str(e)}, 500)
