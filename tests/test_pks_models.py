# -*- coding: utf-8 -*-
from odoo.tests import common, TransactionCase
from odoo.exceptions import ValidationError, UserError
from odoo.tests.common import tagged
from datetime import datetime, date, timedelta


@tagged('pks', 'post_install', '-at_install')
class TestPKSSupplier(TransactionCase):
    """Test cases untuk PKS Supplier Model"""
    
    @classmethod
    def setUpClass(cls):
        super(TestPKSSupplier, cls).setUpClass()
        
        # Create test supplier
        cls.supplier = cls.env['pks.supplier'].create({
            'name': 'Test Supplier',
            'code': 'SUP001',
            'supplier_type': 'company',
            'phone': '08123456789',
            'email': 'test@supplier.com',
            'npwp': '09.254.294.3-407.000',
            'street': 'Jl. Test No. 1',
            'city': 'Jakarta',
        })
    
    def test_supplier_creation(self):
        """Test pembuatan supplier"""
        self.assertTrue(self.supplier)
        self.assertEqual(self.supplier.name, 'Test Supplier')
        self.assertEqual(self.supplier.code, 'SUP001')
        self.assertEqual(self.supplier.verification_state, 'draft')
    
    def test_supplier_npwp_validation(self):
        """Test validasi format NPWP"""
        # NPWP valid
        self.supplier.npwp = '09.254.294.3-407.000'
        self.assertEqual(self.supplier.npwp, '09.254.294.3-407.000')
        
        # NPWP tidak valid
        with self.assertRaises(ValidationError):
            self.supplier.npwp = 'invalid'
    
    def test_supplier_email_validation(self):
        """Test validasi format email"""
        # Email valid
        self.supplier.email = 'valid@email.com'
        self.assertEqual(self.supplier.email, 'valid@email.com')
        
        # Email tidak valid
        with self.assertRaises(ValidationError):
            self.supplier.email = 'invalid-email'
    
    def test_supplier_unique_code(self):
        """Test kode supplier harus unik"""
        with self.assertRaises(Exception):
            self.env['pks.supplier'].create({
                'name': 'Another Supplier',
                'code': 'SUP001',  # Kode yang sama
                'supplier_type': 'individual',
            })
    
    def test_supplier_submit_verification(self):
        """Test submit supplier untuk verifikasi"""
        self.assertEqual(self.supplier.verification_state, 'draft')
        self.supplier.action_submit_for_verification()
        self.assertEqual(self.supplier.verification_state, 'pending')
    
    def test_supplier_verify(self):
        """Test verifikasi supplier"""
        self.supplier.write({'verification_state': 'pending'})
        self.supplier.action_verify()
        self.assertEqual(self.supplier.verification_state, 'verified')
        self.assertTrue(self.supplier.verified_by)
        self.assertTrue(self.supplier.verified_date)


@tagged('pks', 'post_install', '-at_install')
class TestPKSTruck(TransactionCase):
    """Test cases untuk PKS Truck Model"""
    
    @classmethod
    def setUpClass(cls):
        super(TestPKSTruck, cls).setUpClass()
        
        # Create test truck
        cls.truck = cls.env['pks.truck'].create({
            'name': 'B 1234 ABC',
            'rfid_tag': 'RFID001',
            'truck_type': 'dump_truck',
            'brand': 'Hino',
            'capacity_kg': 20000,
            'ownership': 'own',
        })
    
    def test_truck_creation(self):
        """Test pembuatan truk"""
        self.assertTrue(self.truck)
        self.assertEqual(self.truck.name, 'B 1234 ABC')
        self.assertEqual(self.truck.rfid_tag, 'RFID001')
        self.assertEqual(self.truck.current_state, 'available')
    
    def test_truck_unique_rfid(self):
        """Test RFID tag harus unik"""
        with self.assertRaises(Exception):
            self.env['pks.truck'].create({
                'name': 'B 5678 DEF',
                'rfid_tag': 'RFID001',  # RFID yang sama
                'truck_type': 'pickup',
            })
    
    def test_truck_unique_plate(self):
        """Test nomor polisi harus unik"""
        with self.assertRaises(Exception):
            self.env['pks.truck'].create({
                'name': 'B 1234 ABC',  # Plat yang sama
                'rfid_tag': 'RFID002',
                'truck_type': 'pickup',
            })
    
    def test_truck_find_by_rfid(self):
        """Test pencarian truk berdasarkan RFID"""
        result = self.env['pks.truck'].find_by_rfid('RFID001')
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['truck_id'], self.truck.id)
        self.assertEqual(result['plate_number'], 'B 1234 ABC')
    
    def test_truck_find_by_rfid_not_found(self):
        """Test pencarian truk dengan RFID tidak ditemukan"""
        result = self.env['pks.truck'].find_by_rfid('NONEXISTENT')
        self.assertEqual(result['status'], 'error')
    
    def test_truck_set_maintenance(self):
        """Test set status truk ke maintenance"""
        self.assertEqual(self.truck.current_state, 'available')
        self.truck.action_set_maintenance()
        self.assertEqual(self.truck.current_state, 'maintenance')
    
    def test_truck_set_available(self):
        """Test set status truk ke tersedia"""
        self.truck.write({'current_state': 'maintenance'})
        self.truck.action_set_available()
        self.assertEqual(self.truck.current_state, 'available')


@tagged('pks', 'post_install', '-at_install')
class TestPKSWeighbridge(TransactionCase):
    """Test cases untuk PKS Weighbridge Model"""
    
    @classmethod
    def setUpClass(cls):
        super(TestPKSWeighbridge, cls).setUpClass()
        
        # Create test data
        cls.supplier = cls.env['pks.supplier'].create({
            'name': 'Test Supplier',
            'code': 'SUP001',
            'supplier_type': 'company',
        })
        
        cls.truck = cls.env['pks.truck'].create({
            'name': 'B 1234 ABC',
            'rfid_tag': 'RFID001',
            'truck_type': 'dump_truck',
        })
        
        cls.weighbridge = cls.env['pks.weighbridge'].create({
            'supplier_id': cls.supplier.id,
            'truck_id': cls.truck.id,
            'tbs_type': 'external',
        })
    
    def test_weighbridge_creation(self):
        """Test pembuatan tiket timbangan"""
        self.assertTrue(self.weighbridge)
        self.assertTrue(self.weighbridge.name)
        self.assertEqual(self.weighbridge.state, 'draft')
        self.assertEqual(self.weighbridge.supplier_id, self.supplier)
        self.assertEqual(self.weighbridge.truck_id, self.truck)
    
    def test_weighbridge_sequence(self):
        """Test nomor tiket auto-generate"""
        self.assertTrue(self.weighbridge.name.startswith('WB/'))
    
    def test_weighbridge_weigh_in(self):
        """Test timbang masuk"""
        self.weighbridge.write({'weight_in': 25000})
        self.weighbridge.action_weigh_in()
        
        self.assertEqual(self.weighbridge.state, 'weighing_in')
        self.assertTrue(self.weighbridge.weight_in_datetime)
        self.assertTrue(self.weighbridge.weight_in_operator_id)
    
    def test_weighbridge_weigh_in_zero_weight(self):
        """Test timbang masuk dengan berat 0"""
        self.weighbridge.write({'weight_in': 0})
        with self.assertRaises(UserError):
            self.weighbridge.action_weigh_in()
    
    def test_weighbridge_weigh_out(self):
        """Test timbang keluar"""
        # Setup: timbang masuk dulu
        self.weighbridge.write({'weight_in': 25000})
        self.weighbridge.action_weigh_in()
        self.weighbridge.action_confirm_arrival()
        
        # Timbang keluar
        self.weighbridge.write({'weight_out': 8000})
        self.weighbridge.action_weigh_out()
        
        self.assertEqual(self.weighbridge.state, 'weighing_out')
        self.assertTrue(self.weighbridge.weight_out_datetime)
        self.assertEqual(self.weighbridge.netto_weight, 17000)
    
    def test_weighbridge_weigh_out_greater_than_in(self):
        """Test timbang keluar lebih besar dari timbang masuk"""
        self.weighbridge.write({'weight_in': 25000})
        self.weighbridge.action_weigh_in()
        self.weighbridge.action_confirm_arrival()
        
        self.weighbridge.write({'weight_out': 30000})
        with self.assertRaises(UserError):
            self.weighbridge.action_weigh_out()
    
    def test_weighbridge_netto_calculation(self):
        """Test perhitungan netto"""
        self.weighbridge.write({
            'weight_in': 25000,
            'weight_out': 8000,
        })
        self.assertEqual(self.weighbridge.netto_weight, 17000)
    
    def test_weighbridge_cancel(self):
        """Test pembatalan tiket"""
        self.weighbridge.write({'weight_in': 25000})
        self.weighbridge.action_weigh_in()
        
        # Cancel via wizard
        wizard = self.env['pks.weighbridge.cancel.wizard'].create({
            'weighbridge_id': self.weighbridge.id,
            'cancel_reason': 'Test cancel',
        })
        wizard.action_confirm_cancel()
        
        self.assertEqual(self.weighbridge.state, 'cancelled')
        self.assertEqual(self.weighbridge.cancel_reason, 'Test cancel')
    
    def test_weighbridge_processing_time(self):
        """Test perhitungan waktu proses"""
        self.weighbridge.write({
            'weight_in_datetime': datetime.now() - timedelta(hours=2, minutes=30),
            'weight_out_datetime': datetime.now(),
        })
        processing_time = self.weighbridge.get_processing_time()
        self.assertIn('02:', processing_time)


@tagged('pks', 'post_install', '-at_install')
class TestPKSQuality(TransactionCase):
    """Test cases untuk PKS Quality Model"""
    
    @classmethod
    def setUpClass(cls):
        super(TestPKSQuality, cls).setUpClass()
        
        # Create test data
        cls.supplier = cls.env['pks.supplier'].create({
            'name': 'Test Supplier',
            'code': 'SUP001',
            'supplier_type': 'company',
        })
        
        cls.truck = cls.env['pks.truck'].create({
            'name': 'B 1234 ABC',
            'rfid_tag': 'RFID001',
            'truck_type': 'dump_truck',
        })
        
        cls.weighbridge = cls.env['pks.weighbridge'].create({
            'supplier_id': cls.supplier.id,
            'truck_id': cls.truck.id,
            'tbs_type': 'external',
            'weight_in': 25000,
            'weight_out': 8000,
        })
        
        cls.quality = cls.env['pks.quality'].create({
            'weighbridge_id': cls.weighbridge.id,
            'sample_weight': 10,
        })
    
    def test_quality_creation(self):
        """Test pembuatan quality control"""
        self.assertTrue(self.quality)
        self.assertTrue(self.quality.name)
        self.assertEqual(self.quality.state, 'draft')
        self.assertEqual(self.quality.weighbridge_id, self.weighbridge)
    
    def test_quality_grading_moisture(self):
        """Test grading kadar air"""
        # Grade 1: <= 20%
        self.quality.moisture_content = 18
        self.quality._compute_grades()
        self.assertEqual(self.quality.moisture_grade, '1')
        
        # Grade 2: 21-25%
        self.quality.moisture_content = 23
        self.quality._compute_grades()
        self.assertEqual(self.quality.moisture_grade, '2')
        
        # Grade 3: 26-30%
        self.quality.moisture_content = 28
        self.quality._compute_grades()
        self.assertEqual(self.quality.moisture_grade, '3')
        
        # Grade 4: > 30%
        self.quality.moisture_content = 35
        self.quality._compute_grades()
        self.assertEqual(self.quality.moisture_grade, '4')
    
    def test_quality_final_grade(self):
        """Test grade final"""
        self.quality.write({
            'moisture_content': 18,
            'impurities_percent': 1,
            'unripe_percent': 3,
            'rotten_percent': 0.5,
            'empty_bunches_percent': 2,
            'small_particles_percent': 3,
        })
        self.quality._compute_grades()
        self.quality._compute_final_grade()
        
        self.assertEqual(self.quality.final_grade, 'A')
    
    def test_quality_deduction_factor(self):
        """Test faktor potongan"""
        self.quality.final_grade = 'B'
        self.quality._compute_deduction_factor()
        self.assertEqual(self.quality.deduction_factor, 0.02)
    
    def test_quality_weight_deduction(self):
        """Test perhitungan potongan berat"""
        self.quality.write({
            'final_grade': 'B',
            'deduction_factor': 0.02,
        })
        self.quality._compute_weight_deduction()
        
        expected_deduction = 17000 * 0.02  # netto * deduction
        self.assertEqual(self.quality.weight_deduction_kg, expected_deduction)
        self.assertEqual(self.quality.net_weight_after_deduction, 17000 - expected_deduction)
    
    def test_quality_constraints(self):
        """Test constraints quality"""
        # Moisture harus 0-100
        with self.assertRaises(Exception):
            self.quality.moisture_content = 150
        
        with self.assertRaises(Exception):
            self.quality.moisture_content = -5
    
    def test_quality_done(self):
        """Test selesaikan analisa quality"""
        self.quality.write({
            'state': 'in_progress',
            'moisture_content': 18,
            'impurities_percent': 1,
            'unripe_percent': 3,
            'rotten_percent': 0.5,
            'empty_bunches_percent': 2,
            'small_particles_percent': 3,
        })
        self.quality.action_done()
        self.assertEqual(self.quality.state, 'done')


@tagged('pks', 'post_install', '-at_install')
class TestPKSLHP(TransactionCase):
    """Test cases untuk PKS LHP Model"""
    
    @classmethod
    def setUpClass(cls):
        super(TestPKSLHP, cls).setUpClass()
        
        cls.lhp = cls.env['pks.lhp'].create({
            'date': date.today(),
            'shift': 'daily',
            'target_oer': 22.0,
            'target_ker': 5.0,
        })
    
    def test_lhp_creation(self):
        """Test pembuatan LHP"""
        self.assertTrue(self.lhp)
        self.assertTrue(self.lhp.name)
        self.assertEqual(self.lhp.state, 'draft')
    
    def test_lhp_tbs_totals(self):
        """Test perhitungan total TBS"""
        self.lhp.write({
            'tbs_in_internal': 50000,
            'tbs_in_external': 30000,
            'tbs_in_plasma': 20000,
        })
        self.lhp._compute_tbs_totals()
        self.assertEqual(self.lhp.tbs_in_total, 100000)
    
    def test_lhp_oer_calculation(self):
        """Test perhitungan OER"""
        self.lhp.write({
            'tbs_processed': 100000,
            'cpo_produced': 22000,
            'kernel_produced': 5000,
        })
        self.lhp._compute_oer_ker()
        
        self.assertEqual(self.lhp.oer_percent, 22.0)
        self.assertEqual(self.lhp.ker_percent, 5.0)
        self.assertEqual(self.lhp.total_er_percent, 27.0)
    
    def test_lhp_variance_calculation(self):
        """Test perhitungan variance"""
        self.lhp.write({
            'oer_percent': 21.0,
            'ker_percent': 4.5,
            'target_oer': 22.0,
            'target_ker': 5.0,
        })
        self.lhp._compute_variance()
        
        self.assertEqual(self.lhp.oer_variance, -1.0)
        self.assertEqual(self.lhp.ker_variance, -0.5)
    
    def test_lhp_throughput(self):
        """Test perhitungan throughput"""
        self.lhp.write({
            'shift': 'daily',
            'tbs_processed': 240000,
        })
        self.lhp._compute_performance()
        
        self.assertEqual(self.lhp.throughput_per_hour, 10000)  # 240000 / 24
    
    def test_lhp_confirm(self):
        """Test konfirmasi LHP"""
        self.assertEqual(self.lhp.state, 'draft')
        self.lhp.action_confirm()
        self.assertEqual(self.lhp.state, 'confirmed')
        self.assertTrue(self.lhp.confirmed_by)
        self.assertTrue(self.lhp.confirmed_date)
    
    def test_lhp_approve(self):
        """Test approve LHP"""
        self.lhp.write({'state': 'confirmed'})
        self.lhp.action_approve()
        self.assertEqual(self.lhp.state, 'approved')
        self.assertTrue(self.lhp.approved_by)
        self.assertTrue(self.lhp.approved_date)
    
    def test_lhp_done(self):
        """Test selesaikan LHP"""
        self.lhp.write({'state': 'approved'})
        self.lhp.action_done()
        self.assertEqual(self.lhp.state, 'done')
    
    def test_lhp_cancel(self):
        """Test batalkan LHP"""
        self.lhp.write({'state': 'confirmed'})
        self.lhp.action_cancel()
        self.assertEqual(self.lhp.state, 'cancelled')


@tagged('pks', 'post_install', '-at_install')
class TestPKSIntegration(TransactionCase):
    """Test cases untuk integrasi antar model PKS"""
    
    @classmethod
    def setUpClass(cls):
        super(TestPKSIntegration, cls).setUpClass()
        
        # Create complete test scenario
        cls.supplier = cls.env['pks.supplier'].create({
            'name': 'Integration Test Supplier',
            'code': 'INT001',
            'supplier_type': 'company',
        })
        
        cls.truck = cls.env['pks.truck'].create({
            'name': 'B 9999 ZZZ',
            'rfid_tag': 'RFID999',
            'truck_type': 'dump_truck',
        })
    
    def test_complete_weighbridge_flow(self):
        """Test alur lengkap timbangan"""
        # 1. Create weighbridge ticket
        weighbridge = self.env['pks.weighbridge'].create({
            'supplier_id': self.supplier.id,
            'truck_id': self.truck.id,
            'tbs_type': 'external',
        })
        self.assertEqual(weighbridge.state, 'draft')
        
        # 2. Weigh in
        weighbridge.write({'weight_in': 25000})
        weighbridge.action_weigh_in()
        self.assertEqual(weighbridge.state, 'weighing_in')
        
        # 3. Confirm arrival
        weighbridge.action_confirm_arrival()
        self.assertEqual(weighbridge.state, 'waiting_unload')
        
        # 4. Create quality
        quality = self.env['pks.quality'].create({
            'weighbridge_id': weighbridge.id,
            'sample_weight': 10,
            'moisture_content': 20,
            'impurities_percent': 2,
            'unripe_percent': 5,
            'rotten_percent': 1,
            'empty_bunches_percent': 3,
            'small_particles_percent': 5,
        })
        quality.action_start_analysis()
        quality.action_done()
        self.assertEqual(quality.state, 'done')
        
        # 5. Weigh out
        weighbridge.write({'weight_out': 8000})
        weighbridge.action_weigh_out()
        self.assertEqual(weighbridge.state, 'weighing_out')
        
        # 6. Done
        weighbridge.action_done()
        self.assertEqual(weighbridge.state, 'done')
        
        # Verify netto
        self.assertEqual(weighbridge.netto_weight, 17000)
    
    def test_supplier_statistics_update(self):
        """Test update statistik supplier setelah timbangan"""
        initial_deliveries = self.supplier.total_deliveries
        
        # Create and complete weighbridge
        weighbridge = self.env['pks.weighbridge'].create({
            'supplier_id': self.supplier.id,
            'truck_id': self.truck.id,
            'tbs_type': 'external',
            'weight_in': 25000,
            'weight_out': 8000,
        })
        weighbridge.action_weigh_in()
        weighbridge.action_confirm_arrival()
        weighbridge.action_weigh_out()
        weighbridge.action_done()
        
        # Refresh supplier
        self.supplier._compute_total_deliveries()
        
        self.assertEqual(self.supplier.total_deliveries, initial_deliveries + 1)
        self.assertEqual(self.supplier.total_weight, 17000)
    
    def test_truck_statistics_update(self):
        """Test update statistik truk setelah timbangan"""
        initial_trips = self.truck.total_trips
        
        # Create and complete weighbridge
        weighbridge = self.env['pks.weighbridge'].create({
            'supplier_id': self.supplier.id,
            'truck_id': self.truck.id,
            'tbs_type': 'external',
            'weight_in': 25000,
            'weight_out': 8000,
        })
        weighbridge.action_weigh_in()
        weighbridge.action_confirm_arrival()
        weighbridge.action_weigh_out()
        weighbridge.action_done()
        
        # Refresh truck
        self.truck._compute_statistics()
        
        self.assertEqual(self.truck.total_trips, initial_trips + 1)
