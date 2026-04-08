# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, exceptions
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class PKSTruck(models.Model):
    """
    Model Truk PKS dengan RFID Integration
    ======================================
    Tracking truk menggunakan RFID tag untuk otomatisasi timbangan
    """
    _name = 'pks.truck'
    _description = 'PKS Truck'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'
    
    # === Fields ===
    name = fields.Char(
        string='No. Polisi',
        required=True,
        tracking=True
    )
    
    rfid_tag = fields.Char(
        string='RFID Tag',
        required=True,
        copy=False,
        unique=True,
        tracking=True,
        help='Unique RFID tag untuk identifikasi otomatis'
    )
    
    active = fields.Boolean(
        string='Aktif',
        default=True
    )
    
    # Informasi Truk
    truck_type = fields.Selection([
        ('dump_truck', 'Dump Truck'),
        ('pickup', 'Pickup'),
        ('tronton', 'Tronton'),
        ('container', 'Container'),
        ('trailer', 'Trailer'),
        ('other', 'Lainnya'),
    ], string='Tipe Truk', required=True, default='dump_truck')
    
    brand = fields.Char(string='Merk')
    model_year = fields.Integer(string='Tahun')
    capacity_kg = fields.Float(
        string='Kapasitas (kg)',
        digits=(10, 2)
    )
    
    # Status
    ownership = fields.Selection([
        ('own', 'Milik Sendiri'),
        ('rent', 'Sewa'),
        ('third_party', 'Pihak Ketiga'),
    ], string='Kepemilikan', required=True, default='third_party')
    
    # Informasi STNK
    stnk_number = fields.Char(string='No. STNK')
    stnk_expiry = fields.Date(string='Masa Berlaku STNK')
    kir_expiry = fields.Date(string='Masa Berlaku KIR')
    
    # Driver
    driver_id = fields.Many2one(
        'hr.employee',
        string='Supir Default',
        domain=[('job_id.name', 'ilike', 'driver')]
    )
    
    # Supplier (jika truk milik supplier)
    supplier_id = fields.Many2one(
        'pks.supplier',
        string='Supplier',
        help='Supplier yang memiliki truk ini (jika pihak ketiga)'
    )
    
    # Status Tracking
    current_state = fields.Selection([
        ('available', 'Tersedia'),
        ('in_weighbridge', 'Di Timbangan'),
        ('in_mill', 'Di Pabrik'),
        ('maintenance', 'Maintenance'),
        ('inactive', 'Tidak Aktif'),
    ], string='Status Saat Ini', default='available', tracking=True)
    
    last_activity = fields.Selection([
        ('none', 'Tidak Ada'),
        ('weighbridge_in', 'Timbang Masuk'),
        ('weighbridge_out', 'Timbang Keluar'),
        ('maintenance', 'Maintenance'),
    ], string='Aktivitas Terakhir', default='none')
    
    last_activity_date = fields.Datetime(string='Tanggal Aktivitas Terakhir')
    
    # Lokasi Real-time (dari GPS/RFID)
    current_location = fields.Char(string='Lokasi Saat Ini')
    last_gps_latitude = fields.Float(string='Latitude Terakhir', digits=(10, 7))
    last_gps_longitude = fields.Float(string='Longitude Terakhir', digits=(10, 7))
    last_gps_update = fields.Datetime(string='Update GPS Terakhir')
    
    # Statistics
    total_trips = fields.Integer(
        string='Total Trip',
        compute='_compute_statistics',
        store=True
    )
    
    total_weight_delivered = fields.Float(
        string='Total Berat Terkirim (kg)',
        compute='_compute_statistics',
        store=True,
        digits=(12, 2)
    )
    
    average_trip_weight = fields.Float(
        string='Rata-rata Berat per Trip (kg)',
        compute='_compute_statistics',
        store=True,
        digits=(12, 2)
    )
    
    # Relations
    weighbridge_ids = fields.One2many(
        'pks.weighbridge',
        'truck_id',
        string='History Timbangan'
    )
    
    maintenance_ids = fields.One2many(
        'pks.truck.maintenance',
        'truck_id',
        string='History Maintenance'
    )
    
    # Notes
    notes = fields.Text(string='Catatan')
    
    # === Compute Methods ===
    @api.depends('weighbridge_ids.state')
    def _compute_statistics(self):
        for record in self:
            done_weighbridges = record.weighbridge_ids.filtered(lambda w: w.state == 'done')
            record.total_trips = len(done_weighbridges)
            record.total_weight_delivered = sum(w.netto_weight for w in done_weighbridges)
            record.average_trip_weight = record.total_weight_delivered / record.total_trips if record.total_trips > 0 else 0.0
    
    # === SQL Constraints ===
    _sql_constraints = [
        ('unique_rfid', 'UNIQUE(rfid_tag)', 'RFID tag harus unik!'),
        ('unique_plate', 'UNIQUE(name)', 'Nomor polisi harus unik!'),
    ]
    
    # === Constraints ===
    @api.constrains('stnk_expiry', 'kir_expiry')
    def _check_document_expiry(self):
        today = fields.Date.today()
        for record in self:
            if record.stnk_expiry and record.stnk_expiry < today:
                _logger.warning(f'STNK truk {record.name} sudah kadaluarsa!')
            if record.kir_expiry and record.kir_expiry < today:
                _logger.warning(f'KIR truk {record.name} sudah kadaluarsa!')
    
    # === Onchange ===
    @api.onchange('ownership')
    def _onchange_ownership(self):
        if self.ownership == 'own':
            self.supplier_id = False
    
    # === Actions ===
    def action_update_location(self, latitude=None, longitude=None, location=None):
        """Update lokasi truk dari GPS/RFID"""
        for record in self:
            vals = {'last_gps_update': fields.Datetime.now()}
            if latitude is not None:
                vals['last_gps_latitude'] = latitude
            if longitude is not None:
                vals['last_gps_longitude'] = longitude
            if location:
                vals['current_location'] = location
            record.write(vals)
    
    def action_view_on_map(self):
        """Lihat truk di peta"""
        self.ensure_one()
        if not self.last_gps_latitude or not self.last_gps_longitude:
            raise ValidationError(_('Lokasi GPS tidak tersedia untuk truk ini!'))
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'https://www.google.com/maps?q={self.last_gps_latitude},{self.last_gps_longitude}',
            'target': 'new',
        }
    
    def action_view_weighbridges(self):
        """Lihat history timbangan"""
        self.ensure_one()
        return {
            'name': _('History Timbangan'),
            'type': 'ir.actions.act_window',
            'res_model': 'pks.weighbridge',
            'view_mode': 'tree,form',
            'domain': [('truck_id', '=', self.id)],
            'context': {'default_truck_id': self.id},
        }
    
    def action_schedule_maintenance(self):
        """Jadwalkan maintenance"""
        self.ensure_one()
        return {
            'name': _('Jadwalkan Maintenance'),
            'type': 'ir.actions.act_window',
            'res_model': 'pks.truck.maintenance',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_truck_id': self.id},
        }
    
    def action_set_maintenance(self):
        """Set status truk ke maintenance"""
        for record in self:
            if record.current_state == 'maintenance':
                raise ValidationError(_('Truk sudah dalam status maintenance!'))
            record.write({
                'current_state': 'maintenance',
                'last_activity': 'maintenance',
                'last_activity_date': fields.Datetime.now(),
            })
    
    def action_set_available(self):
        """Set status truk ke tersedia"""
        for record in self:
            record.write({
                'current_state': 'available',
            })
    
    # === RFID Methods ===
    @api.model
    def find_by_rfid(self, rfid_tag):
        """Cari truk berdasarkan RFID tag"""
        truck = self.search([('rfid_tag', '=', rfid_tag), ('active', '=', True)], limit=1)
        if not truck:
            return {'status': 'error', 'message': 'RFID tag tidak ditemukan'}
        
        return {
            'status': 'success',
            'truck_id': truck.id,
            'plate_number': truck.name,
            'driver': truck.driver_id.name if truck.driver_id else False,
            'current_state': truck.current_state,
        }
    
    @api.model
    def process_rfid_scan(self, rfid_tag, location='weighbridge'):
        """Proses scan RFID di timbangan"""
        result = self.find_by_rfid(rfid_tag)
        
        if result['status'] == 'error':
            return result
        
        truck = self.browse(result['truck_id'])
        
        # Update lokasi
        truck.write({
            'current_location': location,
            'last_activity_date': fields.Datetime.now(),
        })
        
        # Cek apakah ada tiket aktif
        active_ticket = self.env['pks.weighbridge'].search([
            ('truck_id', '=', truck.id),
            ('state', 'in', ['weighing_in', 'waiting_unload']),
        ], limit=1, order='create_date desc')
        
        result.update({
            'has_active_ticket': bool(active_ticket),
            'active_ticket_id': active_ticket.id if active_ticket else False,
            'active_ticket_state': active_ticket.state if active_ticket else False,
        })
        
        return result
    
    # === Name Get ===
    def name_get(self):
        result = []
        for record in self:
            name = f"[{record.rfid_tag}] {record.name}"
            if record.driver_id:
                name += f" ({record.driver_id.name})"
            result.append((record.id, name))
        return result
    
    # === Search ===
    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('name', operator, name), ('rfid_tag', operator, name)]
        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)
    
    # === Cron Jobs ===
    @api.model
    def _cron_check_document_expiry(self):
        """Cron job untuk cek dokumen yang akan kadaluarsa"""
        today = fields.Date.today()
        warning_date = today + fields.Date.relattimedelta(days=30)
        
        # Cek STNK
        expiring_stnk = self.search([
            ('stnk_expiry', '<=', warning_date),
            ('stnk_expiry', '>=', today),
            ('active', '=', True),
        ])
        
        for truck in expiring_stnk:
            days_remaining = (truck.stnk_expiry - today).days
            _logger.warning(f'STNK truk {truck.name} akan kadaluarsa dalam {days_remaining} hari')
            
            # Create activity
            truck.activity_schedule(
                'mail.mail_activity_data_todo',
                summary=_('STNK akan kadaluarsa'),
                note=_('STNK truk %s akan kadaluarsa pada %s (%s hari lagi)') % (
                    truck.name, truck.stnk_expiry, days_remaining
                ),
                user_id=self.env.ref('base.user_admin').id,
            )
        
        # Cek KIR
        expiring_kir = self.search([
            ('kir_expiry', '<=', warning_date),
            ('kir_expiry', '>=', today),
            ('active', '=', True),
        ])
        
        for truck in expiring_kir:
            days_remaining = (truck.kir_expiry - today).days
            _logger.warning(f'KIR truk {truck.name} akan kadaluarsa dalam {days_remaining} hari')
            
            truck.activity_schedule(
                'mail.mail_activity_data_todo',
                summary=_('KIR akan kadaluarsa'),
                note=_('KIR truk %s akan kadaluarsa pada %s (%s hari lagi)') % (
                    truck.name, truck.kir_expiry, days_remaining
                ),
                user_id=self.env.ref('base.user_admin').id,
            )
        
        return len(expiring_stnk) + len(expiring_kir)


class PKSTruckMaintenance(models.Model):
    """Maintenance Truk"""
    _name = 'pks.truck.maintenance'
    _description = 'PKS Truck Maintenance'
    _order = 'date desc'
    
    name = fields.Char(string='Referensi', required=True, default=lambda self: _('New'))
    truck_id = fields.Many2one('pks.truck', string='Truk', required=True, ondelete='cascade')
    date = fields.Date(string='Tanggal', required=True, default=fields.Date.today)
    
    maintenance_type = fields.Selection([
        ('routine', 'Rutin'),
        ('repair', 'Perbaikan'),
        ('inspection', 'Inspeksi'),
        ('tire', 'Ganti Ban'),
        ('oil', 'Ganti Oli'),
        ('other', 'Lainnya'),
    ], string='Tipe Maintenance', required=True)
    
    description = fields.Text(string='Deskripsi', required=True)
    cost = fields.Float(string='Biaya', digits=(12, 2))
    
    workshop_name = fields.Char(string='Nama Bengkel')
    mechanic_name = fields.Char(string='Nama Mekanik')
    
    next_maintenance_date = fields.Date(string='Maintenance Berikutnya')
    next_maintenance_km = fields.Integer(string='KM Berikutnya')
    
    state = fields.Selection([
        ('planned', 'Direncanakan'),
        ('in_progress', 'Sedang Dikerjakan'),
        ('done', 'Selesai'),
        ('cancelled', 'Dibatalkan'),
    ], string='Status', default='planned')
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('pks.truck.maintenance') or _('New')
        return super(PKSTruckMaintenance, self).create(vals)
