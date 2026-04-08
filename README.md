# PKS Pabrik - Odoo Palm Oil Mill Management System

![Odoo Version](https://img.shields.io/badge/Odoo-17.0-blue.svg)
![License](https://img.shields.io/badge/License-LGPL--3-green.svg)
![PKS Version](https://img.shields.io/badge/PKS-1.0.0-orange.svg)

Modul **PKS Pabrik** adalah sistem manajemen pabrik kelapa sawit (Palm Oil Mill) yang lengkap, dibangun di atas platform Odoo 17. Modul ini dirancang untuk mengelola seluruh proses operasional pabrik kelapa sawit dari penerimaan TBS (Tandan Buah Segar) hingga pelaporan produksi harian (LHP).

## Fitur Utama

### 1. Manajemen Timbangan (Weighbridge) dengan State Machine
- **State Machine**: Draft → Weighing In → Waiting Unload → Weighing Out → Done
- **RFID Integration**: Scan kartu RFID untuk identifikasi truk otomatis
- **Dual Weighing**: Timbang masuk dan timbang keluar dengan perhitungan netto otomatis
- **Slip Timbang**: Cetak slip timbangan dalam format PDF

### 2. Manajemen Supplier dengan Portal
- **Portal Supplier**: Supplier dapat mengakses portal untuk melihat history pengiriman
- **Verifikasi Supplier**: Alur verifikasi supplier (Draft → Pending → Verified/Rejected)
- **Manajemen Kebun**: Pengelolaan data kebun per supplier
- **Statistik Supplier**: Total pengiriman, total berat, rata-rata kualitas

### 3. Manajemen Truk dengan RFID
- **RFID Tracking**: Setiap truk memiliki RFID tag unik
- **Real-time Status**: Monitoring status truk (Available, In Weighbridge, In Mill, Maintenance)
- **GPS Integration**: Tracking lokasi truk (opsional)
- **Maintenance Schedule**: Penjadwalan dan tracking maintenance truk

### 4. Quality Control dengan Grading Otomatis
- **Parameter Quality**:
  - Kadar Air (Moisture Content)
  - Kotoran (Impurities)
  - Buah Mentah (Unripe Fruits)
  - Buah Busuk (Rotten Fruits)
  - Janjang Kosong (Empty Bunches)
  - Partikel Kecil (Small Particles)
- **Grading Otomatis**: Grade A, B, C, D, E, atau Reject
- **Deduction Factor**: Perhitungan potongan berat otomatis berdasarkan grade
- **Foto Sampling**: Upload foto sampel TBS

### 5. LHP (Laporan Harian Pabrik) dengan OER/KER
- **OER (Oil Extraction Rate)**: Persentase ekstraksi minyak dari TBS
- **KER (Kernel Extraction Rate)**: Persentase ekstraksi kernel dari TBS
- **Input TBS**: Pencatatan TBS masuk (Internal, Eksternal, Plasma)
- **Output Produk**: CPO, Kernel, Fiber, Cangkang, Effluent
- **Variance Analysis**: Perbandingan aktual vs target OER/KER
- **Approval Workflow**: Draft → Confirmed → Approved → Done

### 6. REST API dengan Authentication
- **Authentication**: Basic Auth dan API Token
- **Endpoints**:
  - `/api/v1/pks/suppliers` - CRUD Supplier
  - `/api/v1/pks/trucks` - CRUD Truk
  - `/api/v1/pks/weighbridges` - CRUD Timbangan
  - `/api/v1/pks/qualities` - CRUD Quality Control
  - `/api/v1/pks/lhps` - CRUD LHP
  - `/api/v1/pks/dashboard` - Dashboard Data
- **Rate Limiting**: Proteksi terhadap abuse

### 7. OWL Component Mobile-Responsive untuk Kiosk Timbangan
- **Kiosk Mode**: Interface khusus untuk timbangan
- **RFID Scan**: Input via RFID scanner
- **Touch-friendly**: Optimized untuk layar sentuh
- **Responsive**: Mendukung desktop, tablet, dan mobile
- **Auto-logout**: Session timeout untuk keamanan

### 8. QWeb Reports
- **Slip Timbang**: Format PDF untuk slip timbangan
- **Laporan LHP**: Format PDF untuk laporan harian pabrik
- **Customizable**: Template dapat disesuaikan

## Struktur Modul

```
pks_pabrik/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── pks_weighbridge.py      # Model Timbangan dengan State Machine
│   ├── pks_supplier.py         # Model Supplier dengan Portal
│   ├── pks_truck.py            # Model Truk dengan RFID
│   ├── pks_quality.py          # Model Quality Control dengan Grading
│   └── pks_lhp.py              # Model LHP dengan OER/KER
├── views/
│   ├── pks_weighbridge_views.xml
│   ├── pks_supplier_views.xml
│   ├── pks_truck_views.xml
│   ├── pks_quality_views.xml
│   ├── pks_lhp_views.xml
│   ├── dashboard_views.xml
│   └── menu_views.xml
├── controllers/
│   ├── __init__.py
│   ├── main.py                 # Portal & Kiosk Controllers
│   └── api.py                  # REST API Controllers
├── security/
│   ├── pks_security.xml        # Groups & Record Rules
│   └── ir.model.access.csv     # Access Rights
├── reports/
│   ├── slip_timbang.xml        # QWeb Report Slip Timbang
│   └── lhp_report.xml          # QWeb Report LHP
├── static/
│   └── src/
│       └── components/
│           └── kiosk/
│               ├── kiosk.js    # OWL Component
│               ├── kiosk.xml   # OWL Template
│               └── kiosk.scss  # OWL Styles
├── data/
│   ├── pks_sequence.xml        # Sequences
│   └── pks_grade_data.xml      # Grade Configuration Data
├── tests/
│   ├── __init__.py
│   └── test_pks_models.py      # Unit Tests
└── docker/
    ├── Dockerfile
    ├── docker-compose.yml
    ├── nginx.conf
    ├── odoo.conf
    └── .env.example
```

## Instalasi

### Prerequisites
- Odoo 17.0
- PostgreSQL 13+
- Python 3.10+
- Redis (opsional, untuk caching)

### Instalasi Manual

1. Clone repository ke direktori addons Odoo:
```bash
cd /path/to/odoo/addons
git clone https://github.com/hdamanik98/pks_pabrik.git
```

2. Install dependencies Python:
```bash
pip install -r requirements.txt
```

3. Update app list di Odoo dan install modul **PKS Pabrik**.

### Instalasi dengan Docker

1. Copy dan sesuaikan environment variables:
```bash
cd docker
cp .env.example .env
# Edit .env sesuai konfigurasi Anda
```

2. Build dan jalankan container:
```bash
docker-compose up -d
```

3. Akses Odoo di `http://localhost:8069`

## Konfigurasi

### 1. Buat Database Baru
- Database Name: `pks_production`
- Email: admin
- Password: (sesuai konfigurasi)

### 2. Install Modul PKS Pabrik
- Buka Apps menu
- Cari "PKS Pabrik"
- Klik Install

### 3. Konfigurasi User Groups
- **PKS Manager**: Akses penuh ke semua fitur
- **PKS Supervisor**: Mengelola LHP dan quality
- **PKS User**: Operasional timbangan
- **PKS Quality Control**: Mengelola quality control
- **PKS Weighbridge Operator**: Mengoperasikan timbangan
- **PKS Supplier Portal**: Akses portal untuk supplier

### 4. Konfigurasi Grade Quality
- Buka menu: Quality Control → Konfigurasi Grade
- Sesuaikan range parameter untuk setiap grade (A, B, C, D, E)
- Atur deduction factor untuk setiap grade

## Penggunaan

### Alur Timbangan

1. **Scan RFID**: Truk scan RFID tag di kiosk timbangan
2. **Timbang Masuk**: Input berat masuk truk
3. **Bongkar**: Truk bongkar TBS di area unloading
4. **Quality Control**: Petugas QC analisa sampel TBS
5. **Timbang Keluar**: Input berat keluar truk
6. **Selesai**: Tiket timbangan selesai

### Alur LHP

1. **Create LHP**: Buat LHP untuk tanggal/shift tertentu
2. **Import Data**: Import data dari timbangan
3. **Input Produksi**: Input hasil produksi (CPO, Kernel, dll)
4. **Confirm**: Supervisor konfirmasi LHP
5. **Approve**: Manager approve LHP
6. **Done**: LHP selesai dan dapat dicetak

## REST API Usage

### Authentication
```bash
# Basic Auth
curl -u username:password http://localhost:8069/api/v1/pks/suppliers

# API Token
curl -H "X-API-Token: your_token" http://localhost:8069/api/v1/pks/suppliers
```

### Contoh Endpoints

#### Get Suppliers
```bash
curl -u admin:admin http://localhost:8069/api/v1/pks/suppliers
```

#### Create Weighbridge Ticket
```bash
curl -X POST -u admin:admin \
  -H "Content-Type: application/json" \
  -d '{"supplier_id": 1, "truck_id": 1, "tbs_type": "external"}' \
  http://localhost:8069/api/v1/pks/weighbridges
```

#### Weigh In
```bash
curl -X POST -u admin:admin \
  -H "Content-Type: application/json" \
  -d '{"weight_in": 25000}' \
  http://localhost:8069/api/v1/pks/weighbridges/1/weigh-in
```

## Testing

### Run Unit Tests
```bash
# Test semua modul PKS
./odoo-bin -i pks_pabrik --test-enable --stop-after-init

# Test spesifik
./odoo-bin -i pks_pabrik --test-enable --test-tags pks --stop-after-init
```

### Test Coverage
```bash
coverage run --source=addons/pks_pabrik ./odoo-bin -i pks_pabrik --test-enable --stop-after-init
coverage report
coverage html
```

## Deployment

### Production Checklist

- [ ] Ganti default passwords (admin, database)
- [ ] Generate API token yang aman
- [ ] Konfigurasi SSL/TLS
- [ ] Setup backup otomatis
- [ ] Konfigurasi monitoring (optional)
- [ ] Setup email notifications
- [ ] Test disaster recovery

### Docker Production

```bash
# Production mode
docker-compose -f docker-compose.yml up -d

# Dengan monitoring
docker-compose --profile monitoring up -d

# Dengan backup
docker-compose --profile backup up -d
```

## Troubleshooting

### Masalah Umum

#### Database Connection Error
```
Pastikan PostgreSQL berjalan dan kredensial benar di odoo.conf
```

#### Module Not Found
```
Pastikan addons_path di odoo.conf mencakup direktori pks_pabrik
```

#### Permission Denied
```bash
sudo chown -R odoo:odoo /path/to/pks_pabrik
sudo chmod -R 755 /path/to/pks_pabrik
```

## Contributing

1. Fork repository
2. Buat branch feature (`git checkout -b feature/amazing-feature`)
3. Commit perubahan (`git commit -m 'Add amazing feature'`)
4. Push ke branch (`git push origin feature/amazing-feature`)
5. Buat Pull Request

## License

Distributed under the LGPL-3 License. See `LICENSE` for more information.

## Support

- Email: support@sawitnusantara.co.id
- Website: https://www.sawitnusantara.co.id
- Documentation: https://docs.sawitnusantara.co.id/pks

## Acknowledgments

- Odoo Community
- PT. Sawit Nusantara
- Seluruh tim PKS yang telah berkontribusi

---

**Catatan**: Modul ini dikembangkan khusus untuk kebutuhan industri kelapa sawit. Sesuaikan konfigurasi dan parameter sesuai dengan kebijakan dan standar perusahaan Anda.
