# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, exceptions
from odoo.exceptions import ValidationError
import re


class PKSSupplier(models.Model):
    """
    Model Supplier PKS dengan Portal Mixin
    ======================================
    Supplier dapat mengakses portal untuk melihat history pengiriman
    """
    _name = 'pks.supplier'
    _description = 'PKS Supplier'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = 'name'
    
    # === Fields ===
    name = fields.Char(
        string='Nama Supplier',
        required=True,
        tracking=True
    )
    
    code = fields.Char(
        string='Kode Supplier',
        required=True,
        copy=False,
        unique=True,
        tracking=True
    )
    
    active = fields.Boolean(
        string='Aktif',
        default=True
    )
    
    supplier_type = fields.Selection([
        ('individual', 'Perorangan'),
        ('company', 'Perusahaan'),
        ('cooperative', 'Koperasi'),
        ('plasma', 'Plasma'),
    ], string='Tipe Supplier', required=True, default='individual', tracking=True)
    
    # Informasi Kontak
    street = fields.Char(string='Alamat')
    street2 = fields.Char(string='Alamat 2')
    city = fields.Char(string='Kota')
    state_id = fields.Many2one('res.country.state', string='Provinsi')
    zip = fields.Char(string='Kode Pos')
    country_id = fields.Many2one('res.country', string='Negara', default=lambda self: self.env.ref('base.id'))
    
    phone = fields.Char(string='Telepon', tracking=True)
    mobile = fields.Char(string='HP', tracking=True)
    email = fields.Char(string='Email', tracking=True)
    website = fields.Char(string='Website')
    
    # Informasi Bisnis
    npwp = fields.Char(
        string='NPWP',
        tracking=True
    )
    
    nik = fields.Char(
        string='NIK',
        tracking=True
    )
    
    bank_name = fields.Char(string='Nama Bank')
    bank_account = fields.Char(string='No. Rekening')
    bank_account_name = fields.Char(string='Atas Nama Rekening')
    
    # Status Verifikasi
    verification_state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Menunggu Verifikasi'),
        ('verified', 'Terverifikasi'),
        ('rejected', 'Ditolak'),
    ], string='Status Verifikasi', default='draft', tracking=True)
    
    verified_by = fields.Many2one('res.users', string='Diverifikasi Oleh', readonly=True)
    verified_date = fields.Date(string='Tanggal Verifikasi', readonly=True)
    rejection_reason = fields.Text(string='Alasan Penolakan')
    
    # Kontrak
    contract_start = fields.Date(string='Mulai Kontrak')
    contract_end = fields.Date(string='Akhir Kontrak')
    contract_state = fields.Selection([
        ('none', 'Tidak Ada'),
        ('active', 'Aktif'),
        ('expired', 'Kadaluarsa'),
    ], string='Status Kontrak', compute='_compute_contract_state', store=True)
    
    # Harga
    price_per_kg = fields.Float(
        string='Harga per kg',
        digits=(12, 2),
        tracking=True
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Mata Uang',
        default=lambda self: self.env.company.currency_id
    )
    
    # Related Partner untuk Portal
    partner_id = fields.Many2one(
        'res.partner',
        string='Partner Terkait',
        ondelete='restrict',
        help='Partner yang digunakan untuk akses portal'
    )
    
    user_id = fields.Many2one(
        'res.users',
        string='User Portal',
        readonly=True,
        help='User portal yang terhubung dengan supplier ini'
    )
    
    # Statistics
    total_deliveries = fields.Integer(
        string='Total Pengiriman',
        compute='_compute_total_deliveries',
        store=True
    )
    
    total_weight = fields.Float(
        string='Total Berat (kg)',
        compute='_compute_total_deliveries',
        store=True,
        digits=(12, 2)
    )
    
    average_quality = fields.Float(
        string='Rata-rata Kualitas',
        compute='_compute_quality_stats',
        store=True
    )
    
    # Kebun
    estate_ids = fields.One2many(
        'pks.supplier.estate',
        'supplier_id',
        string='Kebun'
    )
    
    estate_count = fields.Integer(
        string='Jumlah Kebun',
        compute='_compute_estate_count'
    )
    
    # Notes
    notes = fields.Text(string='Catatan')
    
    # === Compute Methods ===
    @api.depends('contract_start', 'contract_end')
    def _compute_contract_state(self):
        today = fields.Date.today()
        for record in self:
            if not record.contract_start or not record.contract_end:
                record.contract_state = 'none'
            elif record.contract_start <= today <= record.contract_end:
                record.contract_state = 'active'
            else:
                record.contract_state = 'expired'
    
    @api.depends('estate_ids')
    def _compute_estate_count(self):
        for record in self:
            record.estate_count = len(record.estate_ids)
    
    @api.depends('estate_ids.weighbridge_ids.state')
    def _compute_total_deliveries(self):
        for record in self:
            done_weighbridges = self.env['pks.weighbridge'].search([
                ('supplier_id', '=', record.id),
                ('state', '=', 'done'),
            ])
            record.total_deliveries = len(done_weighbridges)
            record.total_weight = sum(w.netto_weight for w in done_weighbridges)
    
    @api.depends('estate_ids.weighbridge_ids.quality_id')
    def _compute_quality_stats(self):
        for record in self:
            qualities = self.env['pks.quality'].search([
                ('weighbridge_id.supplier_id', '=', record.id),
            ])
            if qualities:
                record.average_quality = sum(q.final_grade for q in qualities) / len(qualities)
            else:
                record.average_quality = 0.0
    
    # === Constraints ===
    @api.constrains('npwp')
    def _check_npwp(self):
        for record in self:
            if record.npwp:
                # Format NPWP: 99.999.999.9-999.999
                pattern = r'^\d{2}\.\d{3}\.\d{3}\.\d{1}-\d{3}\.\d{3}$'
                if not re.match(pattern, record.npwp):
                    raise ValidationError(_('Format NPWP tidak valid! Format: 99.999.999.9-999.999'))
    
    @api.constrains('nik')
    def _check_nik(self):
        for record in self:
            if record.nik:
                if len(record.nik) != 16 or not record.nik.isdigit():
                    raise ValidationError(_('NIK harus 16 digit angka!'))
    
    @api.constrains('email')
    def _check_email(self):
        for record in self:
            if record.email:
                pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(pattern, record.email):
                    raise ValidationError(_('Format email tidak valid!'))
    
    # === SQL Constraints ===
    _sql_constraints = [
        ('unique_code', 'UNIQUE(code)', 'Kode supplier harus unik!'),
        ('unique_npwp', 'UNIQUE(npwp)', 'NPWP sudah terdaftar!'),
        ('unique_nik', 'UNIQUE(nik)', 'NIK sudah terdaftar!'),
    ]
    
    # === Onchange ===
    @api.onchange('supplier_type')
    def _onchange_supplier_type(self):
        if self.supplier_type == 'plasma':
            self.contract_state = 'active'
    
    # === Actions ===
    def action_verify(self):
        """Verifikasi supplier"""
        for record in self:
            if record.verification_state != 'pending':
                raise ValidationError(_('Hanya supplier dengan status menunggu verifikasi yang bisa diverifikasi!'))
            
            record.write({
                'verification_state': 'verified',
                'verified_by': self.env.user.id,
                'verified_date': fields.Date.today(),
            })
            
            record.message_post(body=_('Supplier diverifikasi oleh %s') % self.env.user.name)
    
    def action_reject(self):
        """Tolak verifikasi supplier"""
        for record in self:
            if record.verification_state != 'pending':
                raise ValidationError(_('Hanya supplier dengan status menunggu verifikasi yang bisa ditolak!'))
            
            return {
                'name': _('Tolak Verifikasi'),
                'type': 'ir.actions.act_window',
                'res_model': 'pks.supplier.reject.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {'default_supplier_id': record.id},
            }
    
    def action_submit_for_verification(self):
        """Ajukan untuk verifikasi"""
        for record in self:
            if record.verification_state != 'draft':
                raise ValidationError(_('Hanya supplier draft yang bisa diajukan verifikasi!'))
            
            # Validasi data lengkap
            if not record.npwp and record.supplier_type == 'company':
                raise ValidationError(_('NPWP wajib diisi untuk perusahaan!'))
            
            record.write({
                'verification_state': 'pending',
            })
            
            record.message_post(body=_('Supplier diajukan untuk verifikasi'))
    
    def action_create_portal_user(self):
        """Buat user portal untuk supplier"""
        for record in self:
            if record.user_id:
                raise ValidationError(_('Supplier sudah memiliki user portal!'))
            
            if not record.email:
                raise ValidationError(_('Email wajib diisi untuk membuat user portal!'))
            
            # Buat partner jika belum ada
            if not record.partner_id:
                partner_vals = {
                    'name': record.name,
                    'email': record.email,
                    'phone': record.phone,
                    'mobile': record.mobile,
                    'street': record.street,
                    'street2': record.street2,
                    'city': record.city,
                    'state_id': record.state_id.id,
                    'zip': record.zip,
                    'country_id': record.country_id.id,
                    'company_type': 'person' if record.supplier_type == 'individual' else 'company',
                }
                partner = self.env['res.partner'].create(partner_vals)
                record.partner_id = partner.id
            
            # Buat user portal
            user_vals = {
                'name': record.name,
                'login': record.email,
                'email': record.email,
                'partner_id': record.partner_id.id,
                'groups_id': [(6, 0, [self.env.ref('base.group_portal').id])],
            }
            user = self.env['res.users'].create(user_vals)
            record.user_id = user.id
            
            record.message_post(body=_('User portal dibuat: %s') % record.email)
            
            # Kirim email invitation
            user.action_reset_password()
    
    def action_view_weighbridges(self):
        """Lihat daftar timbangan supplier"""
        self.ensure_one()
        return {
            'name': _('Timbangan'),
            'type': 'ir.actions.act_window',
            'res_model': 'pks.weighbridge',
            'view_mode': 'tree,form',
            'domain': [('supplier_id', '=', self.id)],
            'context': {'default_supplier_id': self.id},
        }
    
    def action_view_estates(self):
        """Lihat daftar kebun supplier"""
        self.ensure_one()
        return {
            'name': _('Kebun'),
            'type': 'ir.actions.act_window',
            'res_model': 'pks.supplier.estate',
            'view_mode': 'tree,form',
            'domain': [('supplier_id', '=', self.id)],
            'context': {'default_supplier_id': self.id},
        }
    
    # === Portal Mixin Override ===
    def _compute_access_url(self):
        super(PKSSupplier, self)._compute_access_url()
        for supplier in self:
            supplier.access_url = '/my/supplier/%s' % supplier.id
    
    # === Name Get ===
    def name_get(self):
        result = []
        for record in self:
            name = f"[{record.code}] {record.name}"
            result.append((record.id, name))
        return result
    
    # === Search ===
    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', '|', ('name', operator, name), ('code', operator, name), ('npwp', operator, name)]
        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)


class PKSSupplierEstate(models.Model):
    """Kebun Supplier"""
    _name = 'pks.supplier.estate'
    _description = 'PKS Supplier Estate'
    _order = 'name'
    
    name = fields.Char(string='Nama Kebun', required=True)
    code = fields.Char(string='Kode Kebun', required=True)
    supplier_id = fields.Many2one('pks.supplier', string='Supplier', required=True, ondelete='cascade')
    
    # Lokasi
    location = fields.Char(string='Lokasi')
    latitude = fields.Float(string='Latitude', digits=(10, 7))
    longitude = fields.Float(string='Longitude', digits=(10, 7))
    area_hectare = fields.Float(string='Luas (Ha)', digits=(10, 2))
    
    # Informasi
    planting_year = fields.Integer(string='Tahun Tanam')
    tree_count = fields.Integer(string='Jumlah Pohon')
    variety = fields.Char(string='Varietas')
    
    active = fields.Boolean(string='Aktif', default=True)
    
    # Relations
    weighbridge_ids = fields.One2many(
        'pks.weighbridge',
        'estate_block',
        string='Timbangan'
    )
    
    _sql_constraints = [
        ('unique_code_supplier', 'UNIQUE(code, supplier_id)', 'Kode kebun harus unik per supplier!'),
    ]


class PKSSupplierRejectWizard(models.TransientModel):
    """Wizard untuk menolak verifikasi supplier"""
    _name = 'pks.supplier.reject.wizard'
    _description = 'Wizard Penolakan Supplier'
    
    supplier_id = fields.Many2one('pks.supplier', string='Supplier', required=True)
    rejection_reason = fields.Text(string='Alasan Penolakan', required=True)
    
    def action_confirm_reject(self):
        self.ensure_one()
        
        if not self.rejection_reason:
            raise ValidationError(_('Alasan penolakan harus diisi!'))
        
        self.supplier_id.write({
            'verification_state': 'rejected',
            'rejection_reason': self.rejection_reason,
        })
        
        self.supplier_id.message_post(
            body=_('Verifikasi ditolak. Alasan: %s') % self.rejection_reason
        )
        
        return {'type': 'ir.actions.act_window_close'}
