/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onMounted, onWillUnmount } from "@odoo/owl";

/**
 * Kiosk Weighbridge Component
 * ===========================
 * Mobile-responsive kiosk untuk timbangan PKS
 * Mendukung input via RFID, manual entry, dan integrasi dengan timbangan digital
 */

export class KioskWeighbridge extends Component {
    static template = "pks_pabrik.KioskWeighbridge";
    static props = {};

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.rpc = useService("rpc");
        
        this.state = useState({
            // Mode: 'idle', 'rfid_scan', 'weigh_in', 'weigh_out', 'confirmation'
            mode: 'idle',
            
            // RFID
            rfidInput: '',
            rfidScanning: false,
            
            // Truck info
            truck: null,
            
            // Weighbridge data
            weighbridgeId: null,
            ticketNumber: null,
            weight: 0,
            
            // Form data
            supplierId: null,
            truckId: null,
            tbsType: 'external',
            estateBlock: '',
            harvestDate: null,
            
            // Lists untuk dropdown
            suppliers: [],
            trucks: [],
            
            // Status
            loading: false,
            error: null,
            success: null,
            
            // Timer
            lastActivity: null,
        });
        
        onMounted(() => {
            this.loadInitialData();
            this.startInactivityTimer();
            
            // Focus RFID input jika ada
            this.focusRfidInput();
        });
        
        onWillUnmount(() => {
            this.stopInactivityTimer();
        });
    }
    
    // ============================================================
    // INITIAL DATA LOADING
    // ============================================================
    
    async loadInitialData() {
        try {
            // Load suppliers
            const suppliers = await this.orm.searchRead(
                'pks.supplier',
                [['active', '=', true], ['verification_state', '=', 'verified']],
                ['id', 'name', 'code']
            );
            this.state.suppliers = suppliers;
            
            // Load trucks
            const trucks = await this.orm.searchRead(
                'pks.truck',
                [['active', '=', true]],
                ['id', 'name', 'rfid_tag', 'driver_id']
            );
            this.state.trucks = trucks;
            
        } catch (error) {
            console.error('Error loading initial data:', error);
            this.state.error = 'Gagal memuat data awal';
        }
    }
    
    // ============================================================
    // RFID HANDLING
    // ============================================================
    
    focusRfidInput() {
        setTimeout(() => {
            const rfidInput = document.getElementById('rfid-input');
            if (rfidInput) {
                rfidInput.focus();
            }
        }, 100);
    }
    
    onRfidInputChange(ev) {
        this.state.rfidInput = ev.target.value;
        
        // Auto-submit jika panjang RFID cukup (biasanya 10-20 karakter)
        if (this.state.rfidInput.length >= 8) {
            this.processRfidScan();
        }
    }
    
    async processRfidScan() {
        if (!this.state.rfidInput || this.state.rfidScanning) {
            return;
        }
        
        this.state.rfidScanning = true;
        this.state.loading = true;
        this.state.error = null;
        
        try {
            // Cari truk berdasarkan RFID
            const result = await this.rpc('/pks/kiosk/rfid-scan', {
                rfid_tag: this.state.rfidInput
            });
            
            if (result.status === 'success') {
                this.state.truck = result;
                this.state.truckId = result.truck_id;
                
                // Cek apakah ada tiket aktif
                if (result.has_active_ticket) {
                    // Ada tiket aktif, lanjutkan timbang keluar
                    this.state.weighbridgeId = result.active_ticket_id;
                    this.state.mode = 'weigh_out';
                    this.notification.add('Tiket aktif ditemukan. Silakan timbang keluar.', {
                        type: 'info'
                    });
                } else {
                    // Tidak ada tiket aktif, buat tiket baru (timbang masuk)
                    this.state.mode = 'weigh_in';
                    this.notification.add('Truk teridentifikasi. Silakan timbang masuk.', {
                        type: 'success'
                    });
                }
                
                this.resetInactivityTimer();
            } else {
                this.state.error = result.message || 'RFID tidak ditemukan';
                this.notification.add(this.state.error, { type: 'danger' });
            }
            
        } catch (error) {
            console.error('RFID scan error:', error);
            this.state.error = 'Error saat memproses RFID';
            this.notification.add(this.state.error, { type: 'danger' });
        } finally {
            this.state.rfidScanning = false;
            this.state.loading = false;
            this.state.rfidInput = '';
        }
    }
    
    // ============================================================
    // WEIGH IN
    // ============================================================
    
    async createWeighbridgeTicket() {
        if (!this.state.supplierId || !this.state.truckId) {
            this.state.error = 'Supplier dan Truk harus diisi';
            return;
        }
        
        this.state.loading = true;
        this.state.error = null;
        
        try {
            const result = await this.orm.create('pks.weighbridge', [{
                supplier_id: this.state.supplierId,
                truck_id: this.state.truckId,
                tbs_type: this.state.tbsType,
                estate_block: this.state.estateBlock,
                harvest_date: this.state.harvestDate,
            }]);
            
            if (result) {
                this.state.weighbridgeId = result[0];
                this.notification.add('Tiket timbangan berhasil dibuat', { type: 'success' });
                this.resetInactivityTimer();
            }
            
        } catch (error) {
            console.error('Error creating weighbridge ticket:', error);
            this.state.error = 'Gagal membuat tiket timbangan';
            this.notification.add(this.state.error, { type: 'danger' });
        } finally {
            this.state.loading = false;
        }
    }
    
    async submitWeighIn() {
        if (!this.state.weight || this.state.weight <= 0) {
            this.state.error = 'Berat masuk harus lebih dari 0';
            return;
        }
        
        this.state.loading = true;
        this.state.error = null;
        
        try {
            // Update weight in
            await this.orm.write('pks.weighbridge', [this.state.weighbridgeId], {
                weight_in: this.state.weight
            });
            
            // Execute weigh in action
            await this.orm.call('pks.weighbridge', 'action_weigh_in', [[this.state.weighbridgeId]]);
            
            this.notification.add('Timbang masuk berhasil', { type: 'success' });
            this.state.success = 'Timbang masuk berhasil. Truk dapat masuk ke area bongkar.';
            this.state.mode = 'confirmation';
            this.resetInactivityTimer();
            
        } catch (error) {
            console.error('Error weigh in:', error);
            this.state.error = 'Gagal melakukan timbang masuk';
            this.notification.add(this.state.error, { type: 'danger' });
        } finally {
            this.state.loading = false;
        }
    }
    
    // ============================================================
    // WEIGH OUT
    // ============================================================
    
    async submitWeighOut() {
        if (!this.state.weight || this.state.weight <= 0) {
            this.state.error = 'Berat keluar harus lebih dari 0';
            return;
        }
        
        this.state.loading = true;
        this.state.error = null;
        
        try {
            // Update weight out
            await this.orm.write('pks.weighbridge', [this.state.weighbridgeId], {
                weight_out: this.state.weight
            });
            
            // Execute weigh out action
            await this.orm.call('pks.weighbridge', 'action_weigh_out', [[this.state.weighbridgeId]]);
            
            this.notification.add('Timbang keluar berhasil', { type: 'success' });
            this.state.success = 'Timbang keluar berhasil. Tiket selesai.';
            this.state.mode = 'confirmation';
            this.resetInactivityTimer();
            
        } catch (error) {
            console.error('Error weigh out:', error);
            this.state.error = 'Gagal melakukan timbang keluar';
            this.notification.add(this.state.error, { type: 'danger' });
        } finally {
            this.state.loading = false;
        }
    }
    
    // ============================================================
    // UTILITY METHODS
    // ============================================================
    
    resetForm() {
        this.state.mode = 'idle';
        this.state.rfidInput = '';
        this.state.truck = null;
        this.state.weighbridgeId = null;
        this.state.ticketNumber = null;
        this.state.weight = 0;
        this.state.supplierId = null;
        this.state.truckId = null;
        this.state.tbsType = 'external';
        this.state.estateBlock = '';
        this.state.harvestDate = null;
        this.state.error = null;
        this.state.success = null;
        
        this.focusRfidInput();
    }
    
    printTicket() {
        if (this.state.weighbridgeId) {
            this.orm.call('pks.weighbridge', 'print_slip_timbang', [[this.state.weighbridgeId]]);
        }
    }
    
    getWeightFromScale() {
        // Simulasi pembacaan dari timbangan digital
        // Dalam implementasi nyata, ini akan membaca dari serial port atau API timbangan
        this.state.loading = true;
        
        setTimeout(() => {
            // Simulasi berat acak untuk demo
            const simulatedWeight = Math.floor(Math.random() * 5000) + 15000; // 15000 - 20000 kg
            this.state.weight = simulatedWeight;
            this.state.loading = false;
            this.notification.add('Berat berhasil dibaca dari timbangan', { type: 'success' });
        }, 1000);
    }
    
    // ============================================================
    // INACTIVITY TIMER
    // ============================================================
    
    startInactivityTimer() {
        this.inactivityTimeout = 60000; // 60 detik
        this.inactivityTimer = null;
        this.resetInactivityTimer();
        
        // Reset timer pada setiap aktivitas
        document.addEventListener('click', () => this.resetInactivityTimer());
        document.addEventListener('keypress', () => this.resetInactivityTimer());
        document.addEventListener('touchstart', () => this.resetInactivityTimer());
    }
    
    stopInactivityTimer() {
        if (this.inactivityTimer) {
            clearTimeout(this.inactivityTimer);
        }
    }
    
    resetInactivityTimer() {
        if (this.inactivityTimer) {
            clearTimeout(this.inactivityTimer);
        }
        
        this.inactivityTimer = setTimeout(() => {
            this.onInactivityTimeout();
        }, this.inactivityTimeout);
        
        this.state.lastActivity = new Date();
    }
    
    onInactivityTimeout() {
        // Reset ke idle setelah tidak ada aktivitas
        if (this.state.mode !== 'idle') {
            this.notification.add('Sesi berakhir karena tidak ada aktivitas', { type: 'warning' });
            this.resetForm();
        }
    }
    
    // ============================================================
    // GETTERS
    // ============================================================
    
    get isIdle() {
        return this.state.mode === 'idle';
    }
    
    get isWeighIn() {
        return this.state.mode === 'weigh_in';
    }
    
    get isWeighOut() {
        return this.state.mode === 'weigh_out';
    }
    
    get isConfirmation() {
        return this.state.mode === 'confirmation';
    }
    
    get nettoWeight() {
        // Untuk demo, asumsikan weight in - weight out
        // Dalam implementasi nyata, ini akan dihitung dari data tiket
        return 0;
    }
    
    get formattedWeight() {
        return new Intl.NumberFormat('id-ID').format(this.state.weight);
    }
}

// Register component
registry.category("actions").add("pks_kiosk_weighbridge", KioskWeighbridge);
