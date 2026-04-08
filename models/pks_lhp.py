# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, exceptions
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class PKSLHP(models.Model):
    """
    Model LHP (Laporan Harian Pabrik) dengan OER/KER Calculation
    =============================================================
    Laporan harian produksi pabrik kelapa sawit
    """
    _name = 'pks.lhp'
    _description = 'PKS Daily Report (LHP)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc'
    
    # === Fields ===
    name = fields.Char(
        string='No. LHP',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Dikonfirmasi'),
        ('approved', 'Disetujui'),
        ('done', 'Selesai'),
        ('cancelled', 'Dibatalkan'),
    ], string='Status', default='draft', tracking=True)
    
    date = fields.Date(
        string='Tanggal',
        required=True,
        default=fields.Date.today,
        tracking=True
    )
    
    shift = fields.Selection([
        ('1', 'Shift 1 (00:00 - 08:00)'),
        ('2', 'Shift 2 (08:00 - 16:00)'),
        ('3', 'Shift 3 (16:00 - 24:00)'),
        ('daily', 'Harian (Full)'),
    ], string='Shift', required=True, default='daily')
    
    # Informasi Pabrik
    mill_id = fields.Many2one(
        'res.company',
        string='Pabrik',
        required=True,
        default=lambda self: self.env.company
    )
    
    supervisor_id = fields.Many2one(
        'hr.employee',
        string='Supervisor',
        required=True
    )
    
    # === Input TBS (Tandan Buah Segar) ===
    # TBS Masuk
    tbs_in_internal = fields.Float(
        string='TBS Internal (kg)',
        digits=(12, 2),
        tracking=True
    )
    
    tbs_in_external = fields.Float(
        string='TBS Eksternal (kg)',
        digits=(12, 2),
        tracking=True
    )
    
    tbs_in_plasma = fields.Float(
        string='TBS Plasma (kg)',
        digits=(12, 2),
        tracking=True
    )
    
    tbs_in_total = fields.Float(
        string='Total TBS Masuk (kg)',
        compute='_compute_tbs_totals',
        store=True,
        digits=(12, 2)
    )
    
    # TBS Olah
    tbs_processed = fields.Float(
        string='TBS Diolah (kg)',
        digits=(12, 2),
        tracking=True
    )
    
    tbs_remaining = fields.Float(
        string='Sisa TBS (kg)',
        compute='_compute_tbs_remaining',
        store=True,
        digits=(12, 2)
    )
    
    # === Output Produk ===
    # CPO (Crude Palm Oil)
    cpo_produced = fields.Float(
        string='CPO Dihasilkan (kg)',
        digits=(12, 2),
        tracking=True
    )
    
    cpo_ffa = fields.Float(
        string='CPO FFA (%)',
        digits=(5, 2),
        help='Free Fatty Acid - kadar asam lemak bebas'
    )
    
    cpo_moisture = fields.Float(
        string='CPO Moisture (%)',
        digits=(5, 2),
        help='Kadar air dalam CPO'
    )
    
    cpo_dirt = fields.Float(
        string='CPO Dirt (%)',
        digits=(5, 2),
        help='Kadar kotoran dalam CPO'
    )
    
    # Kernel (Inti Sawit)
    kernel_produced = fields.Float(
        string='Kernel Dihasilkan (kg)',
        digits=(12, 2),
        tracking=True
    )
    
    kernel_moisture = fields.Float(
        string='Kernel Moisture (%)',
        digits=(5, 2)
    )
    
    kernel_dirt = fields.Float(
        string='Kernel Dirt (%)',
        digits=(5, 2)
    )
    
    # === Waste/By-products ===
    fiber_produced = fields.Float(
        string='Fiber (kg)',
        digits=(12, 2)
    )
    
    shell_produced = fields.Float(
        string='Cangkang (kg)',
        digits=(12, 2)
    )
    
    empty_bunch_produced = fields.Float(
        string='Janjang Kosong (kg)',
        digits=(12, 2)
    )
    
    effluent_produced = fields.Float(
        string='Effluent/POME (kg)',
        digits=(12, 2)
    )
    
    # === OER/KER Calculation ===
    # OER (Oil Extraction Rate)
    oer_percent = fields.Float(
        string='OER (%)',
        compute='_compute_oer_ker',
        store=True,
        digits=(5, 2),
        help='Oil Extraction Rate - Persentase ekstraksi minyak dari TBS'
    )
    
    # KER (Kernel Extraction Rate)
    ker_percent = fields.Float(
        string='KER (%)',
        compute='_compute_oer_ker',
        store=True,
        digits=(5, 2),
        help='Kernel Extraction Rate - Persentase ekstraksi kernel dari TBS'
    )
    
    # Total Extraction Rate
    total_er_percent = fields.Float(
        string='Total ER (%)',
        compute='_compute_oer_ker',
        store=True,
        digits=(5, 2),
        help='Total Extraction Rate - OER + KER'
    )
    
    # === Losses ===
    oil_loss_in_fiber = fields.Float(
        string='Oil Loss in Fiber (%)',
        digits=(5, 2)
    )
    
    oil_loss_in_effluent = fields.Float(
        string='Oil Loss in Effluent (%)',
        digits=(5, 2)
    )
    
    total_oil_loss = fields.Float(
        string='Total Oil Loss (%)',
        compute='_compute_losses',
        store=True,
        digits=(5, 2)
    )
    
    # === Performance Indicators ===
    throughput_per_hour = fields.Float(
        string='Throughput (kg/jam)',
        compute='_compute_performance',
        store=True,
        digits=(10, 2)
    )
    
    machine_availability = fields.Float(
        string='Ketersediaan Mesin (%)',
        digits=(5, 2)
    )
    
    downtime_hours = fields.Float(
        string='Downtime (jam)',
        digits=(5, 2)
    )
    
    downtime_reason = fields.Text(string='Alasan Downtime')
    
    # === Target vs Actual ===
    target_oer = fields.Float(
        string='Target OER (%)',
        digits=(5, 2),
        default=22.0
    )
    
    target_ker = fields.Float(
        string='Target KER (%)',
        digits=(5, 2),
        default=5.0
    )
    
    oer_variance = fields.Float(
        string='OER Variance (%)',
        compute='_compute_variance',
        store=True,
        digits=(5, 2)
    )
    
    ker_variance = fields.Float(
        string='KER Variance (%)',
        compute='_compute_variance',
        store=True,
        digits=(5, 2)
    )
    
    # === Relations ===
    weighbridge_ids = fields.One2many(
        'pks.weighbridge',
        'lhp_id',
        string='Timbangan Terkait',
        domain=[('state', '=', 'done')]
    )
    
    weighbridge_count = fields.Integer(
        string='Jumlah Timbangan',
        compute='_compute_weighbridge_count'
    )
    
    # === Summary ===
    total_suppliers = fields.Integer(
        string='Jumlah Supplier',
        compute='_compute_summary',
        store=True
    )
    
    total_trucks = fields.Integer(
        string='Jumlah Truk',
        compute='_compute_summary',
        store=True
    )
    
    notes = fields.Text(string='Catatan')
    
    # === Approval ===
    confirmed_by = fields.Many2one('res.users', string='Dikonfirmasi Oleh', readonly=True)
    confirmed_date = fields.Datetime(string='Tanggal Konfirmasi', readonly=True)
    
    approved_by = fields.Many2one('res.users', string='Disetujui Oleh', readonly=True)
    approved_date = fields.Datetime(string('Tanggal Persetujuan'), readonly=True)
    
    # === Compute Methods ===
    @api.depends('tbs_in_internal', 'tbs_in_external', 'tbs_in_plasma')
    def _compute_tbs_totals(self):
        for record in self:
            record.tbs_in_total = record.tbs_in_internal + record.tbs_in_external + record.tbs_in_plasma
    
    @api.depends('tbs_in_total', 'tbs_processed')
    def _compute_tbs_remaining(self):
        for record in self:
            record.tbs_remaining = record.tbs_in_total - record.tbs_processed
    
    @api.depends('tbs_processed', 'cpo_produced', 'kernel_produced')
    def _compute_oer_ker(self):
        for record in self:
            if record.tbs_processed > 0:
                record.oer_percent = (record.cpo_produced / record.tbs_processed) * 100
                record.ker_percent = (record.kernel_produced / record.tbs_processed) * 100
                record.total_er_percent = record.oer_percent + record.ker_percent
            else:
                record.oer_percent = 0.0
                record.ker_percent = 0.0
                record.total_er_percent = 0.0
    
    @api.depends('oil_loss_in_fiber', 'oil_loss_in_effluent')
    def _compute_losses(self):
        for record in self:
            record.total_oil_loss = record.oil_loss_in_fiber + record.oil_loss_in_effluent
    
    @api.depends('tbs_processed', 'shift')
    def _compute_performance(self):
        for record in self:
            hours = 24 if record.shift == 'daily' else 8
            if hours > 0:
                record.throughput_per_hour = record.tbs_processed / hours
            else:
                record.throughput_per_hour = 0.0
    
    @api.depends('target_oer', 'target_ker', 'oer_percent', 'ker_percent')
    def _compute_variance(self):
        for record in self:
            record.oer_variance = record.oer_percent - record.target_oer
            record.ker_variance = record.ker_percent - record.target_ker
    
    def _compute_weighbridge_count(self):
        for record in self:
            record.weighbridge_count = len(record.weighbridge_ids)
    
    @api.depends('weighbridge_ids')
    def _compute_summary(self):
        for record in self:
            record.total_suppliers = len(record.weighbridge_ids.mapped('supplier_id'))
            record.total_trucks = len(record.weighbridge_ids.mapped('truck_id'))
    
    # === SQL Constraints ===
    _sql_constraints = [
        ('unique_date_shift_mill', 'UNIQUE(date, shift, mill_id)', 
         'LHP untuk tanggal, shift, dan pabrik ini sudah ada!'),
    ]
    
    # === Defaults ===
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('pks.lhp') or _('New')
        return super(PKSLHP, self).create(vals)
    
    # === Actions ===
    def action_confirm(self):
        """Konfirmasi LHP"""
        for record in self:
            if record.state != 'draft':
                raise ValidationError(_('Hanya LHP draft yang bisa dikonfirmasi!'))
            
            record.write({
                'state': 'confirmed',
                'confirmed_by': self.env.user.id,
                'confirmed_date': fields.Datetime.now(),
            })
            
            record.message_post(body=_('LHP dikonfirmasi oleh %s') % self.env.user.name)
    
    def action_approve(self):
        """Setujui LHP"""
        for record in self:
            if record.state != 'confirmed':
                raise ValidationError(_('Hanya LHP yang sudah dikonfirmasi yang bisa disetujui!'))
            
            record.write({
                'state': 'approved',
                'approved_by': self.env.user.id,
                'approved_date': fields.Datetime.now(),
            })
            
            record.message_post(body=_('LHP disetujui oleh %s') % self.env.user.name)
    
    def action_done(self):
        """Selesaikan LHP"""
        for record in self:
            if record.state != 'approved':
                raise ValidationError(_('Hanya LHP yang sudah disetujui yang bisa diselesaikan!'))
            
            record.write({
                'state': 'done',
            })
            
            record.message_post(body=_('LHP selesai'))
    
    def action_cancel(self):
        """Batalkan LHP"""
        for record in self:
            if record.state == 'done':
                raise ValidationError(_('LHP yang sudah selesai tidak bisa dibatalkan!'))
            
            record.write({
                'state': 'cancelled',
            })
            
            record.message_post(body=_('LHP dibatalkan oleh %s') % self.env.user.name)
    
    def action_reset_to_draft(self):
        """Reset ke draft"""
        for record in self:
            if record.state not in ['cancelled']:
                raise ValidationError(_('Hanya LHP yang dibatalkan yang bisa direset!'))
            
            record.write({
                'state': 'draft',
                'confirmed_by': False,
                'confirmed_date': False,
                'approved_by': False,
                'approved_date': False,
            })
    
    def action_import_from_weighbridge(self):
        """Import data dari timbangan"""
        for record in self:
            # Cari timbangan yang selesai pada tanggal ini
            weighbridges = self.env['pks.weighbridge'].search([
                ('state', '=', 'done'),
                ('weight_out_datetime', '>=', record.date),
                ('weight_out_datetime', '<', record.date + timedelta(days=1)),
            ])
            
            if weighbridges:
                record.weighbridge_ids = [(6, 0, weighbridges.ids)]
                
                # Hitung total TBS
                internal_weight = sum(w.netto_weight for w in weighbridges if w.tbs_type == 'internal')
                external_weight = sum(w.netto_weight for w in weighbridges if w.tbs_type == 'external')
                plasma_weight = sum(w.netto_weight for w in weighbridges if w.tbs_type == 'plasma')
                
                record.write({
                    'tbs_in_internal': internal_weight,
                    'tbs_in_external': external_weight,
                    'tbs_in_plasma': plasma_weight,
                })
                
                record.message_post(
                    body=_('Data timbangan diimport: %s transaksi') % len(weighbridges)
                )
            else:
                raise ValidationError(_('Tidak ada data timbangan untuk tanggal ini!'))
    
    def action_view_weighbridges(self):
        """Lihat timbangan terkait"""
        self.ensure_one()
        return {
            'name': _('Timbangan'),
            'type': 'ir.actions.act_window',
            'res_model': 'pks.weighbridge',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.weighbridge_ids.ids)],
        }
    
    # === Business Methods ===
    def get_performance_summary(self):
        """Get ringkasan performa"""
        self.ensure_one()
        return {
            'date': self.date,
            'shift': self.shift,
            'tbs_processed': self.tbs_processed,
            'cpo_produced': self.cpo_produced,
            'kernel_produced': self.kernel_produced,
            'oer': self.oer_percent,
            'ker': self.ker_percent,
            'total_er': self.total_er_percent,
            'oer_variance': self.oer_variance,
            'ker_variance': self.ker_variance,
            'throughput': self.throughput_per_hour,
            'downtime': self.downtime_hours,
        }
    
    def get_oer_analysis(self):
        """Analisis OER detail"""
        self.ensure_one()
        return {
            'oer_actual': self.oer_percent,
            'oer_target': self.target_oer,
            'oer_variance': self.oer_variance,
            'oer_variance_percent': (self.oer_variance / self.target_oer * 100) if self.target_oer else 0,
            'performance_status': 'good' if self.oer_variance >= 0 else 'need_improvement',
        }
    
    # === Name Get ===
    def name_get(self):
        result = []
        for record in self:
            name = f"[{record.name}] {record.date} - OER: {record.oer_percent:.2f}%"
            result.append((record.id, name))
        return result
    
    # === Cron Jobs ===
    @api.model
    def _cron_auto_create_daily_lhp(self):
        """Cron job untuk auto-create LHP harian"""
        yesterday = fields.Date.today() - timedelta(days=1)
        
        # Cek apakah sudah ada
        existing = self.search([
            ('date', '=', yesterday),
            ('shift', '=', 'daily'),
            ('mill_id', '=', self.env.company.id),
        ])
        
        if not existing:
            lhp = self.create({
                'date': yesterday,
                'shift': 'daily',
            })
            
            # Import data dari timbangan
            lhp.action_import_from_weighbridge()
            
            _logger.info(f'Auto-created LHP for {yesterday}')
            return lhp.id
        
        return False


class PKSLHPLine(models.Model):
    """Detail Line LHP per Supplier"""
    _name = 'pks.lhp.line'
    _description = 'PKS LHP Detail Line'
    
    lhp_id = fields.Many2one('pks.lhp', string='LHP', required=True, ondelete='cascade')
    supplier_id = fields.Many2one('pks.supplier', string='Supplier', required=True)
    
    # TBS
    tbs_weight = fields.Float(string='Berat TBS (kg)', digits=(12, 2))
    
    # Quality
    quality_grade = fields.Char(string='Grade')
    deduction_kg = fields.Float(string='Potongan (kg)', digits=(12, 2))
    net_weight = fields.Float(string='Berat Bersih (kg)', digits=(12, 2))
    
    # CPO & Kernel allocation
    cpo_allocated = fields.Float(string='CPO Allocation (kg)', digits=(12, 2))
    kernel_allocated = fields.Float(string='Kernel Allocation (kg)', digits=(12, 2))
    
    sequence = fields.Integer(string='Sequence', default=10)
