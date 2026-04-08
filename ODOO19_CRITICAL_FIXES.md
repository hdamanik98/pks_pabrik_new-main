# PKS Pabrik - Odoo 19 Migration - Critical Fixes

## Overview
**Date**: April 8, 2026
**Total Issues Found**: 12 Critical Syntax Errors
**Files Affected**: 3 (pks_lhp.py, pks_quality.py, __manifest__.py)
**Severity**: 🔴 CRITICAL - Module won't install

---

## Critical Fixes Required

### Issue #1-9: Invalid Field String Parameter Syntax
**Location**: `models/pks_lhp.py`
**Pattern**: `fields.Float(string('...')` should be `fields.Float(string='...')`

#### Fixes in pks_lhp.py:

1. **Line 148** - kernel_produced field
   - FROM: `kernel_produced = fields.Float(string('Kernel Dihasilkan (kg)'),`
   - TO: `kernel_produced = fields.Float(string='Kernel Dihasilkan (kg)',`

2. **Line 155** - empty_bunch_produced field
   - FROM: `empty_bunch_produced = fields.Float(string('Janjang Kosong (kg)'),`
   - TO: `empty_bunch_produced = fields.Float(string='Janjang Kosong (kg)',`

3. **Line 160** - effluent_produced field
   - FROM: `effluent_produced = fields.Float(string('Effluent/POME (kg)',`
   - TO: `effluent_produced = fields.Float(string='Effluent/POME (kg)',`

4. **Line 212** - downtime_hours field
   - FROM: `downtime_hours = fields.Float(string('Downtime (jam)'),`
   - TO: `downtime_hours = fields.Float(string='Downtime (jam)',`

5. **Line 548** - tbs_weight field
   - FROM: `tbs_weight = fields.Float(string('Berat TBS (kg)'), digits=(12, 2))`
   - TO: `tbs_weight = fields.Float(string='Berat TBS (kg)', digits=(12, 2))`

6. **Line 552** - deduction_kg field
   - FROM: `deduction_kg = fields.Float(string('Potongan (kg)', digits=(12, 2))`
   - TO: `deduction_kg = fields.Float(string='Potongan (kg)', digits=(12, 2))`

7. **Line 553** - net_weight field
   - FROM: `net_weight = fields.Float(string('Berat Bersih (kg)', digits=(12, 2))`
   - TO: `net_weight = fields.Float(string='Berat Bersih (kg)', digits=(12, 2))`

8. **Line 556** - cpo_allocated field
   - FROM: `cpo_allocated = fields.Float(string('CPO Allocation (kg)', digits=(12, 2))`
   - TO: `cpo_allocated = fields.Float(string='CPO Allocation (kg)', digits=(12, 2))`

9. **Line 557** - kernel_allocated field
   - FROM: `kernel_allocated = fields.Float(string('Kernel Allocation (kg)', digits=(12, 2))`
   - TO: `kernel_allocated = fields.Float(string='Kernel Allocation (kg)', digits=(12, 2))`

---

### Issue #10: Invalid Field String Parameter in pks_quality.py
**Location**: `models/pks_quality.py`
**Line 524** - small_particles_max field

- FROM: `small_particles_max = fields.Float(string('Partikel Kecil Max (%)'), digits=(5, 2))`
- TO: `small_particles_max = fields.Float(string='Partikel Kecil Max (%)', digits=(5, 2))`

---

### Issue #11: Missing Manifest Version Update
**Location**: `__manifest__.py`
**Severity**: 🔴 CRITICAL

Update version from Odoo 17 to Odoo 19:

```python
# FROM:
'version': '17.0.1.0.0',

# TO:
'version': '19.0.1.0.0',
```

---

## Summary Table

| # | File | Line | Error Type | Status |
|---|------|------|-----------|--------|
| 1 | pks_lhp.py | 148 | string() → string= | Fix Applied |
| 2 | pks_lhp.py | 155 | string() → string= | Fix Applied |
| 3 | pks_lhp.py | 160 | string() → string= | Fix Applied |
| 4 | pks_lhp.py | 212 | string() → string= | Fix Applied |
| 5 | pks_lhp.py | 548 | string() → string= | Fix Applied |
| 6 | pks_lhp.py | 552 | string() → string= | Fix Applied |
| 7 | pks_lhp.py | 553 | string() → string= | Fix Applied |
| 8 | pks_lhp.py | 556 | string() → string= | Fix Applied |
| 9 | pks_lhp.py | 557 | string() → string= | Fix Applied |
| 10 | pks_quality.py | 524 | string() → string= | Fix Applied |
| 11 | __manifest__.py | 3 | Odoo 17→19 Version | Fix Applied |

---

## Next Steps After Fixes

1. ✅ Apply All 11 Fixes
2. ✅ Run Syntax Check
3. ✅ Update README.md version references
4. ✅ Test module installation
5. ✅ Run test suite
6. ✅ Test all features

---

**All fixes are critical for Odoo 19 compatibility**
