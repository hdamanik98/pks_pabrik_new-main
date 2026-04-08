# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, exceptions
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class PKSWeighbridge(models.Model):
    """
    Model Timbangan PKS dengan State Machine
    ========================================
    State: draft -> weighing_in -> waiting_unload -> weighing_out -> done -> cancelled
    """
    _name = 'pks.weighbridge'
    _description = 'PKS Weighbridge Transaction'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    
    # === Fields ===
    name = fields.Char(
        string='No. Tiket',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        tracking=True
    )
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('weighing_in', 'Timbang Masuk'),
        ('waiting_unload', 'Menunggu Bongkar'),
        ('weighing_out', 'Timbang Keluar'),
        ('done', 'Selesai'),
        ('cancelled', 'Dibatalkan'),
    ], string='Status', default='draft', tracking=True, copy=False)
    
    # Relasi
    supplier_id = fields.Many2one(
        'pks.supplier',
        string='Supplier',
        required=True,
        tracking=True,
        domain=[('active', '=', True)]
    )
    
    truck_id = fields.Many2one(
        'pks.truck',
        string='Truk',
        required=True,
        tracking=True,
        domain=[('active', '=', True)]
    )
    
    driver_id = fields.Many2one(
        'hr.employee',
        string='Supir',
        tracking=True
    )
    
    quality_id = fields.Many2one(
        'pks.quality',
        string='Hasil Quality',
        readonly=True,
        copy=False
    )
    
    # Timbang Masuk
    weight_in = fields.Float(
        string='Berat Masuk (kg)',
        digits=(12, 2),
        tracking=True
    )
    weight_in_datetime = fields.Datetime(
        string='Waktu Timbang Masuk',
        readonly=True
    )
    weight_in_operator_id = fields.Many2one(
        'res.users',
        string='Operator Timbang Masuk',
        readonly=True
    )
    
    # Timbang Keluar
    weight_out = fields.Float(
        string='Berat Keluar (kg)',
        digits=(12, 2),
        tracking=True
    )
    weight_out_datetime = fields.Datetime(
        string='Waktu Timbang Keluar',
        readonly=True
    )
    weight_out_operator_id = fields.Many2one(
        'res.users',
        string='Operator Timbang Keluar',
        readonly=True
    )
    
    # Netto Calculation
    netto_weight = fields.Float(
        string='Berat Bersih (kg)',
        compute='_compute_netto_weight',
        store=True,
        digits=(12, 2)
    )
    
    # Informasi TBS
    tbs_type = fields.Selection([
        ('internal', 'Internal'),
        ('external', 'Eksternal'),
        ('plasma', 'Plasma'),
    ], string='Jenis TBS', required=True, default='external', tracking=True)
    
    estate_block = fields.Char(
        string='Blok Kebun',
        tracking=True
    )
    
    harvest_date = fields.Date(
        string='Tanggal Panen',
        tracking=True
    )
    
    # RFID
    rfid_tag = fields.Char(
        string='RFID Tag',
        related='truck_id.rfid_tag',
        readonly=True,
        store=True
    )
    
    # Notes
    notes = fields.Text(string='Catatan')
    
    # Cancel Info
    cancel_reason = fields.Text(string='Alasan Pembatalan')
    cancelled_by = fields.Many2one('res.users', string='Dibatalkan Oleh', readonly=True)
    cancelled_date = fields.Datetime(string='Tanggal Pembatalan', readonly=True)
    
    # === Compute Methods ===
    @api.depends('weight_in', 'weight_out')
    def _compute_netto_weight(self):
        for record in self:
            if record.weight_in and record.weight_out:
                record.netto_weight = record.weight_in - record.weight_out
            else:
                record.netto_weight = 0.0
    
    # === SQL Constraints ===
    _sql_constraints = [
        ('check_weight_in_positive', 'CHECK(weight_in >= 0)', 'Berat masuk harus positif!'),
        ('check_weight_out_positive', 'CHECK(weight_out >= 0)', 'Berat keluar harus positif!'),
    ]
    
    # === Constraints ===
    @api.constrains('weight_in', 'weight_out')
    def _check_weight_logic(self):
        for record in self:
            if record.weight_out and record.weight_in and record.weight_out > record.weight_in:
                raise ValidationError(_('Berat keluar tidak boleh lebih besar dari berat masuk!'))
    
    # === Defaults ===
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('pks.weighbridge') or _('New')
        return super(PKSWeighbridge, self).create(vals)
    
    # === State Machine Actions ===
    def action_weigh_in(self):
        """Action untuk timbang masuk"""
        for record in self:
            if record.state != 'draft':
                raise UserError(_('Hanya tiket draft yang bisa timbang masuk!'))
            if record.weight_in <= 0:
                raise UserError(_('Berat masuk harus lebih dari 0!'))
            
            record.write({
                'state': 'weighing_in',
                'weight_in_datetime': fields.Datetime.now(),
                'weight_in_operator_id': self.env.user.id,
            })
            
            # Update last activity truck
            record.truck_id.write({
                'last_activity': 'weighbridge_in',
                'last_activity_date': fields.Datetime.now(),
            })
            
            # Log message
            record.message_post(
                body=_('Timbang Masuk: %s kg oleh %s') % (
                    record.weight_in,
                    self.env.user.name
                )
            )
    
    def action_confirm_arrival(self):
        """Konfirmasi kedatangan dan mulai proses bongkar"""
        for record in self:
            if record.state != 'weighing_in':
                raise UserError(_('Hanya tiket yang sudah timbang masuk yang bisa diproses!'))
            
            record.write({
                'state': 'waiting_unload',
            })
            
            record.message_post(body=_('Truk tiba di area bongkar'))
    
    def action_weigh_out(self):
        """Action untuk timbang keluar"""
        for record in self:
            if record.state != 'waiting_unload':
                raise UserError(_('Hanya tiket yang sudah bongkar yang bisa timbang keluar!'))
            if record.weight_out <= 0:
                raise UserError(_('Berat keluar harus lebih dari 0!'))
            if record.weight_out >= record.weight_in:
                raise UserError(_('Berat keluar harus lebih kecil dari berat masuk!'))
            
            record.write({
                'state': 'weighing_out',
                'weight_out_datetime': fields.Datetime.now(),
                'weight_out_operator_id': self.env.user.id,
            })
            
            # Update truck activity
            record.truck_id.write({
                'last_activity': 'weighbridge_out',
                'last_activity_date': fields.Datetime.now(),
            })
            
            record.message_post(
                body=_('Timbang Keluar: %s kg, Netto: %s kg') % (
                    record.weight_out,
                    record.netto_weight
                )
            )
    
    def action_done(self):
        """Selesaikan tiket timbangan"""
        for record in self:
            if record.state != 'weighing_out':
                raise UserError(_('Hanya tiket yang sudah timbang keluar yang bisa diselesaikan!'))
            
            # Validasi quality sudah ada
            if not record.quality_id:
                raise UserError(_('Hasil quality control harus diisi terlebih dahulu!'))
            
            record.write({
                'state': 'done',
            })
            
            # Update supplier stats
            record.supplier_id._compute_total_deliveries()
            
            record.message_post(body=_('Tiket timbangan selesai'))
    
    def action_cancel(self):
        """Batalkan tiket timbangan"""
        for record in self:
            if record.state == 'done':
                raise UserError(_('Tiket yang sudah selesai tidak bisa dibatalkan!'))
            if record.state == 'cancelled':
                raise UserError(_('Tiket sudah dibatalkan!'))
            
            # Open wizard untuk alasan pembatalan
            return {
                'name': _('Batalkan Tiket'),
                'type': 'ir.actions.act_window',
                'res_model': 'pks.weighbridge.cancel.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {'default_weighbridge_id': record.id},
            }
    
    def action_reset_to_draft(self):
        """Reset tiket ke draft (hanya untuk admin)"""
        for record in self:
            if record.state not in ['cancelled']:
                raise UserError(_('Hanya tiket yang dibatalkan yang bisa direset!'))
            
            record.write({
                'state': 'draft',
                'weight_in': 0,
                'weight_in_datetime': False,
                'weight_in_operator_id': False,
                'weight_out': 0,
                'weight_out_datetime': False,
                'weight_out_operator_id': False,
                'cancel_reason': False,
                'cancelled_by': False,
                'cancelled_date': False,
            })
            
            record.message_post(body=_('Tiket direset ke draft'))
    
    # === Business Methods ===
    def get_processing_time(self):
        """Hitung waktu proses dari timbang masuk sampai timbang keluar"""
        self.ensure_one()
        if self.weight_in_datetime and self.weight_out_datetime:
            delta = self.weight_out_datetime - self.weight_in_datetime
            hours, remainder = divmod(delta.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return "00:00:00"
    
    def name_get(self):
        """Custom display name"""
        result = []
        for record in self:
            name = f"[{record.name}] {record.supplier_id.name} - {record.netto_weight:,.2f} kg"
            result.append((record.id, name))
        return result
    
    # === Cron Jobs ===
    @api.model
    def _cron_cleanup_draft_tickets(self):
        """Cron job untuk membersihkan tiket draft yang sudah lama"""
        expiry_date = fields.Datetime.now() - timedelta(days=7)
        old_drafts = self.search([
            ('state', '=', 'draft'),
            ('create_date', '<', expiry_date),
        ])
        
        for ticket in old_drafts:
            ticket.write({
                'state': 'cancelled',
                'cancel_reason': 'Otomatis dibatalkan karena draft lebih dari 7 hari',
                'cancelled_by': self.env.ref('base.user_root').id,
                'cancelled_date': fields.Datetime.now(),
            })
        
        _logger.info(f'Cleaned up {len(old_drafts)} old draft tickets')
        return len(old_drafts)


class PKSWeighbridgeCancelWizard(models.TransientModel):
    """Wizard untuk pembatalan tiket timbangan"""
    _name = 'pks.weighbridge.cancel.wizard'
    _description = 'Wizard Pembatalan Tiket Timbangan'
    
    weighbridge_id = fields.Many2one(
        'pks.weighbridge',
        string='Tiket Timbangan',
        required=True
    )
    
    cancel_reason = fields.Text(
        string='Alasan Pembatalan',
        required=True
    )
    
    def action_confirm_cancel(self):
        """Konfirmasi pembatalan"""
        self.ensure_one()
        
        if not self.cancel_reason:
            raise UserError(_('Alasan pembatalan harus diisi!'))
        
        self.weighbridge_id.write({
            'state': 'cancelled',
            'cancel_reason': self.cancel_reason,
            'cancelled_by': self.env.user.id,
            'cancelled_date': fields.Datetime.now(),
        })
        
        self.weighbridge_id.message_post(
            body=_('Tiket dibatalkan. Alasan: %s') % self.cancel_reason
        )
        
        return {'type': 'ir.actions.act_window_close'}
