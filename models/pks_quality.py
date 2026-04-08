# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, exceptions
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class PKSQuality(models.Model):
    """
    Model Quality Control PKS dengan Grading Otomatis
    =================================================
    Sistem grading TBS berdasarkan parameter kualitas
    """
    _name = 'pks.quality'
    _description = 'PKS Quality Control'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    
    # === Fields ===
    name = fields.Char(
        string='No. Analisa',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'Sedang Analisa'),
        ('done', 'Selesai'),
        ('cancelled', 'Dibatalkan'),
    ], string='Status', default='draft', tracking=True)
    
    # Relasi
    weighbridge_id = fields.Many2one(
        'pks.weighbridge',
        string='Tiket Timbangan',
        required=True,
        domain=[('state', 'in', ['weighing_in', 'waiting_unload', 'weighing_out'])]
    )
    
    supplier_id = fields.Many2one(
        'pks.supplier',
        string='Supplier',
        related='weighbridge_id.supplier_id',
        store=True,
        readonly=True
    )
    
    truck_id = fields.Many2one(
        'pks.truck',
        string='Truk',
        related='weighbridge_id.truck_id',
        store=True,
        readonly=True
    )
    
    # Sampling Info
    sample_date = fields.Datetime(
        string='Tanggal Sampling',
        default=fields.Datetime.now,
        required=True
    )
    
    sampler_id = fields.Many2one(
        'hr.employee',
        string='Petugas Sampling',
        required=True
    )
    
    analyst_id = fields.Many2one(
        'hr.employee',
        string='Analis',
        required=True
    )
    
    sample_weight = fields.Float(
        string='Berat Sampel (kg)',
        digits=(8, 2),
        required=True
    )
    
    # === Parameter Kualitas ===
    # 1. Kadar Air (Moisture Content)
    moisture_content = fields.Float(
        string='Kadar Air (%)',
        digits=(5, 2),
        help='Persentase kadar air dalam TBS'
    )
    
    moisture_grade = fields.Selection([
        ('1', 'Grade 1 (Baik)'),
        ('2', 'Grade 2 (Sedang)'),
        ('3', 'Grade 3 (Kurang)'),
        ('4', 'Grade 4 (Buruk)'),
    ], string='Grade Kadar Air', compute='_compute_grades', store=True)
    
    # 2. Kotoran (Impurities/Dirt)
    impurities_percent = fields.Float(
        string='Kotoran (%)',
        digits=(5, 2),
        help='Persentase kotoran dalam TBS'
    )
    
    impurities_grade = fields.Selection([
        ('1', 'Grade 1 (Baik)'),
        ('2', 'Grade 2 (Sedang)'),
        ('3', 'Grade 3 (Kurang)'),
        ('4', 'Grade 4 (Buruk)'),
    ], string='Grade Kotoran', compute='_compute_grades', store=True)
    
    # 3. Buah Mentah (Unripe Fruits)
    unripe_percent = fields.Float(
        string='Buah Mentah (%)',
        digits=(5, 2),
        help='Persentase buah mentah'
    )
    
    unripe_grade = fields.Selection([
        ('1', 'Grade 1 (Baik)'),
        ('2', 'Grade 2 (Sedang)'),
        ('3', 'Grade 3 (Kurang)'),
        ('4', 'Grade 4 (Buruk)'),
    ], string='Grade Buah Mentah', compute='_compute_grades', store=True)
    
    # 4. Buah Busuk (Rotten Fruits)
    rotten_percent = fields.Float(
        string='Buah Busuk (%)',
        digits=(5, 2),
        help='Persentase buah busuk'
    )
    
    rotten_grade = fields.Selection([
        ('1', 'Grade 1 (Baik)'),
        ('2', 'Grade 2 (Sedang)'),
        ('3', 'Grade 3 (Kurang)'),
        ('4', 'Grade 4 (Buruk)'),
    ], string='Grade Buah Busuk', compute='_compute_grades', store=True)
    
    # 5. Janjang Kosong (Empty Bunches)
    empty_bunches_percent = fields.Float(
        string('Janjang Kosong (%)'),
        digits=(5, 2),
        help='Persentase janjang kosong'
    )
    
    empty_bunches_grade = fields.Selection([
        ('1', 'Grade 1 (Baik)'),
        ('2', 'Grade 2 (Sedang)'),
        ('3', 'Grade 3 (Kurang)'),
        ('4', 'Grade 4 (Buruk)'),
    ], string='Grade Janjang Kosong', compute='_compute_grades', store=True)
    
    # 6. Partikel Kecil (Small Particles)
    small_particles_percent = fields.Float(
        string='Partikel Kecil (%)',
        digits=(5, 2),
        help='Persentase partikel kecil (< 5mm)'
    )
    
    small_particles_grade = fields.Selection([
        ('1', 'Grade 1 (Baik)'),
        ('2', 'Grade 2 (Sedang)'),
        ('3', 'Grade 3 (Kurang)'),
        ('4', 'Grade 4 (Buruk)'),
    ], string='Grade Partikel Kecil', compute='_compute_grades', store=True)
    
    # === Grading Otomatis ===
    final_grade = fields.Selection([
        ('A', 'Grade A (Premium)'),
        ('B', 'Grade B (Baik)'),
        ('C', 'Grade C (Sedang)'),
        ('D', 'Grade D (Kurang)'),
        ('E', 'Grade E (Buruk)'),
        ('reject', 'Ditolak'),
    ], string='Grade Final', compute='_compute_final_grade', store=True, tracking=True)
    
    grade_score = fields.Float(
        string='Skor Grade',
        compute='_compute_final_grade',
        store=True,
        digits=(5, 2)
    )
    
    # Deduction Factor (Faktor Potongan)
    deduction_factor = fields.Float(
        string='Faktor Potongan',
        compute='_compute_deduction_factor',
        store=True,
        digits=(5, 4)
    )
    
    # Potongan Berat
    weight_deduction_kg = fields.Float(
        string('Potongan Berat (kg)'),
        compute='_compute_weight_deduction',
        store=True,
        digits=(12, 2)
    )
    
    net_weight_after_deduction = fields.Float(
        string='Berat Bersih Setelah Potongan (kg)',
        compute='_compute_weight_deduction',
        store=True,
        digits=(12, 2)
    )
    
    # === Additional Info ===
    photo_ids = fields.One2many(
        'pks.quality.photo',
        'quality_id',
        string='Foto Sampling'
    )
    
    notes = fields.Text(string='Catatan Analisa')
    
    # === Compute Methods ===
    @api.depends('moisture_content', 'impurities_percent', 'unripe_percent',
                 'rotten_percent', 'empty_bunches_percent', 'small_particles_percent')
    def _compute_grades(self):
        """Hitung grade untuk setiap parameter"""
        for record in self:
            # Kadar Air grading
            if record.moisture_content <= 20:
                record.moisture_grade = '1'
            elif record.moisture_content <= 25:
                record.moisture_grade = '2'
            elif record.moisture_content <= 30:
                record.moisture_grade = '3'
            else:
                record.moisture_grade = '4'
            
            # Kotoran grading
            if record.impurities_percent <= 2:
                record.impurities_grade = '1'
            elif record.impurities_percent <= 5:
                record.impurities_grade = '2'
            elif record.impurities_percent <= 8:
                record.impurities_grade = '3'
            else:
                record.impurities_grade = '4'
            
            # Buah Mentah grading
            if record.unripe_percent <= 5:
                record.unripe_grade = '1'
            elif record.unripe_percent <= 10:
                record.unripe_grade = '2'
            elif record.unripe_percent <= 15:
                record.unripe_grade = '3'
            else:
                record.unripe_grade = '4'
            
            # Buah Busuk grading
            if record.rotten_percent <= 1:
                record.rotten_grade = '1'
            elif record.rotten_percent <= 3:
                record.rotten_grade = '2'
            elif record.rotten_percent <= 5:
                record.rotten_grade = '3'
            else:
                record.rotten_grade = '4'
            
            # Janjang Kosong grading
            if record.empty_bunches_percent <= 3:
                record.empty_bunches_grade = '1'
            elif record.empty_bunches_percent <= 6:
                record.empty_bunches_grade = '2'
            elif record.empty_bunches_percent <= 10:
                record.empty_bunches_grade = '3'
            else:
                record.empty_bunches_grade = '4'
            
            # Partikel Kecil grading
            if record.small_particles_percent <= 5:
                record.small_particles_grade = '1'
            elif record.small_particles_percent <= 10:
                record.small_particles_grade = '2'
            elif record.small_particles_percent <= 15:
                record.small_particles_grade = '3'
            else:
                record.small_particles_grade = '4'
    
    @api.depends('moisture_grade', 'impurities_grade', 'unripe_grade',
                 'rotten_grade', 'empty_bunches_grade', 'small_particles_grade')
    def _compute_final_grade(self):
        """Hitung grade final berdasarkan semua parameter"""
        for record in self:
            grades = [
                int(record.moisture_grade) if record.moisture_grade else 0,
                int(record.impurities_grade) if record.impurities_grade else 0,
                int(record.unripe_grade) if record.unripe_grade else 0,
                int(record.rotten_grade) if record.rotten_grade else 0,
                int(record.empty_bunches_grade) if record.empty_bunches_grade else 0,
                int(record.small_particles_grade) if record.small_particles_grade else 0,
            ]
            
            if not any(grades):
                record.final_grade = False
                record.grade_score = 0.0
                continue
            
            # Hitung rata-rata grade
            avg_grade = sum(grades) / len([g for g in grades if g > 0])
            record.grade_score = avg_grade
            
            # Tentukan grade final
            if avg_grade <= 1.5:
                record.final_grade = 'A'
            elif avg_grade <= 2.0:
                record.final_grade = 'B'
            elif avg_grade <= 2.5:
                record.final_grade = 'C'
            elif avg_grade <= 3.0:
                record.final_grade = 'D'
            elif avg_grade <= 3.5:
                record.final_grade = 'E'
            else:
                record.final_grade = 'reject'
    
    @api.depends('final_grade')
    def _compute_deduction_factor(self):
        """Hitung faktor potongan berdasarkan grade"""
        deduction_factors = {
            'A': 0.0,      # Tidak ada potongan
            'B': 0.02,     # 2% potongan
            'C': 0.05,     # 5% potongan
            'D': 0.08,     # 8% potongan
            'E': 0.12,     # 12% potongan
            'reject': 1.0, # 100% potongan (ditolak)
        }
        
        for record in self:
            record.deduction_factor = deduction_factors.get(record.final_grade, 0.0)
    
    @api.depends('weighbridge_id.netto_weight', 'deduction_factor')
    def _compute_weight_deduction(self):
        """Hitung potongan berat"""
        for record in self:
            if record.weighbridge_id and record.weighbridge_id.netto_weight:
                record.weight_deduction_kg = record.weighbridge_id.netto_weight * record.deduction_factor
                record.net_weight_after_deduction = record.weighbridge_id.netto_weight - record.weight_deduction_kg
            else:
                record.weight_deduction_kg = 0.0
                record.net_weight_after_deduction = 0.0
    
    # === SQL Constraints ===
    _sql_constraints = [
        ('check_moisture', 'CHECK(moisture_content >= 0 AND moisture_content <= 100)', 
         'Kadar air harus antara 0-100%!'),
        ('check_impurities', 'CHECK(impurities_percent >= 0 AND impurities_percent <= 100)', 
         'Kotoran harus antara 0-100%!'),
        ('check_unripe', 'CHECK(unripe_percent >= 0 AND unripe_percent <= 100)', 
         'Buah mentah harus antara 0-100%!'),
        ('check_rotten', 'CHECK(rotten_percent >= 0 AND rotten_percent <= 100)', 
         'Buah busuk harus antara 0-100%!'),
        ('check_empty_bunches', 'CHECK(empty_bunches_percent >= 0 AND empty_bunches_percent <= 100)', 
         'Janjang kosong harus antara 0-100%!'),
        ('check_small_particles', 'CHECK(small_particles_percent >= 0 AND small_particles_percent <= 100)', 
         'Partikel kecil harus antara 0-100%!'),
    ]
    
    # === Defaults ===
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('pks.quality') or _('New')
        
        record = super(PKSQuality, self).create(vals)
        
        # Link ke weighbridge
        if record.weighbridge_id:
            record.weighbridge_id.write({'quality_id': record.id})
        
        return record
    
    # === Actions ===
    def action_start_analysis(self):
        """Mulai analisa"""
        for record in self:
            if record.state != 'draft':
                raise ValidationError(_('Hanya analisa draft yang bisa dimulai!'))
            
            record.write({
                'state': 'in_progress',
            })
            
            record.message_post(body=_('Analisa quality dimulai'))
    
    def action_done(self):
        """Selesaikan analisa"""
        for record in self:
            if record.state != 'in_progress':
                raise ValidationError(_('Hanya analisa yang sedang berjalan yang bisa diselesaikan!'))
            
            # Validasi semua parameter terisi
            if not all([
                record.moisture_content is not None,
                record.impurities_percent is not None,
                record.unripe_percent is not None,
                record.rotten_percent is not None,
                record.empty_bunches_percent is not None,
                record.small_particles_percent is not None,
            ]):
                raise ValidationError(_('Semua parameter kualitas harus diisi!'))
            
            record.write({
                'state': 'done',
            })
            
            record.message_post(
                body=_('Analisa quality selesai. Grade: %s, Potongan: %s kg') % (
                    record.final_grade,
                    record.weight_deduction_kg
                )
            )
    
    def action_cancel(self):
        """Batalkan analisa"""
        for record in self:
            if record.state == 'done':
                raise ValidationError(_('Analisa yang sudah selesai tidak bisa dibatalkan!'))
            
            record.write({
                'state': 'cancelled',
            })
            
            record.message_post(body=_('Analisa quality dibatalkan'))
    
    def action_reset_to_draft(self):
        """Reset ke draft"""
        for record in self:
            if record.state not in ['cancelled']:
                raise ValidationError(_('Hanya analisa yang dibatalkan yang bisa direset!'))
            
            record.write({
                'state': 'draft',
            })
    
    # === Business Methods ===
    def get_quality_summary(self):
        """Get ringkasan kualitas"""
        self.ensure_one()
        return {
            'grade': self.final_grade,
            'score': self.grade_score,
            'deduction_kg': self.weight_deduction_kg,
            'net_weight': self.net_weight_after_deduction,
            'parameters': {
                'moisture': {'value': self.moisture_content, 'grade': self.moisture_grade},
                'impurities': {'value': self.impurities_percent, 'grade': self.impurities_grade},
                'unripe': {'value': self.unripe_percent, 'grade': self.unripe_grade},
                'rotten': {'value': self.rotten_percent, 'grade': self.rotten_grade},
                'empty_bunches': {'value': self.empty_bunches_percent, 'grade': self.empty_bunches_grade},
                'small_particles': {'value': self.small_particles_percent, 'grade': self.small_particles_grade},
            }
        }
    
    # === Name Get ===
    def name_get(self):
        result = []
        for record in self:
            name = f"[{record.name}] {record.supplier_id.name} - Grade {record.final_grade or '-'}"
            result.append((record.id, name))
        return result


class PKSQualityPhoto(models.Model):
    """Foto Sampling Quality"""
    _name = 'pks.quality.photo'
    _description = 'PKS Quality Photo'
    _order = 'sequence'
    
    quality_id = fields.Many2one('pks.quality', string='Quality', required=True, ondelete='cascade')
    sequence = fields.Integer(string='Sequence', default=10)
    name = fields.Char(string='Deskripsi')
    
    photo = fields.Image(
        string='Foto',
        max_width=1920,
        max_height=1920,
        required=True
    )
    
    photo_type = fields.Selection([
        ('sample', 'Sampel'),
        ('defect', 'Cacat'),
        ('overview', 'Overview'),
        ('other', 'Lainnya'),
    ], string='Tipe Foto', default='sample')
    
    taken_by = fields.Many2one('hr.employee', string='Diambil Oleh')
    taken_date = fields.Datetime(string='Tanggal', default=fields.Datetime.now)


class PKSQualityGradeConfig(models.Model):
    """Konfigurasi Grade Quality"""
    _name = 'pks.quality.grade.config'
    _description = 'PKS Quality Grade Configuration'
    _order = 'sequence'
    
    name = fields.Char(string='Nama Grade', required=True)
    code = fields.Char(string='Kode Grade', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    
    # Parameter ranges
    moisture_min = fields.Float(string='Kadar Air Min (%)', digits=(5, 2))
    moisture_max = fields.Float(string='Kadar Air Max (%)', digits=(5, 2))
    
    impurities_min = fields.Float(string='Kotoran Min (%)', digits=(5, 2))
    impurities_max = fields.Float(string='Kotoran Max (%)', digits=(5, 2))
    
    unripe_min = fields.Float(string='Buah Mentah Min (%)', digits=(5, 2))
    unripe_max = fields.Float(string='Buah Mentah Max (%)', digits=(5, 2))
    
    rotten_min = fields.Float(string='Buah Busuk Min (%)', digits=(5, 2))
    rotten_max = fields.Float(string='Buah Busuk Max (%)', digits=(5, 2))
    
    empty_bunches_min = fields.Float(string='Janjang Kosong Min (%)', digits=(5, 2))
    empty_bunches_max = fields.Float(string='Janjang Kosong Max (%)', digits=(5, 2))
    
    small_particles_min = fields.Float(string='Partikel Kecil Min (%)', digits=(5, 2))
    small_particles_max = fields.Float(string='Partikel Kecil Max (%)', digits=(5, 2))
    
    # Deduction
    deduction_percent = fields.Float(
        string='Potongan (%)',
        digits=(5, 2),
        help='Persentase potongan berat untuk grade ini'
    )
    
    active = fields.Boolean(string='Aktif', default=True)
    notes = fields.Text(string='Catatan')
    
    _sql_constraints = [
        ('unique_code', 'UNIQUE(code)', 'Kode grade harus unik!'),
    ]
