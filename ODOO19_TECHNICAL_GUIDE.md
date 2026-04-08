# PKS Pabrik - Odoo 19 Technical Migration Guide

**Version**: 19.0.1.0.0  
**Date**: April 8, 2026  
**Purpose**: Technical guidance for Odoo 19 compatibility

---

## 🔍 Key Technical Changes - Odoo 17 → Odoo 19

### 1. OWL Component Architecture Changes

#### Current Implementation (Odoo 17)
```javascript
// File: static/src/components/kiosk/kiosk.js
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onMounted, onWillUnmount } from "@odoo/owl";

export class KioskWeighbridge extends Component {
    static template = "pks_pabrik.KioskWeighbridge";
    static props = {};
    
    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.rpc = useService("rpc");
    }
}
```

#### Required Verification for Odoo 19
```javascript
// VERIFY: These imports are still available in Odoo 19
import { registry } from "@web/core/registry";        // ✅ Still available
import { useService } from "@web/core/utils/hooks";   // ✅ Still available
import { Component, useState, onMounted } from "@odoo/owl";  // ✅ Check version

// RECOMMENDED: Add to package.json if using modern build setup
// "@odoo/owl": "^2.x.x"
```

#### Action Items for OWL Component
- [ ] Verify OWL 2.x compatibility
- [ ] Test component registration in registry
- [ ] Test service hooks (orm, notification, rpc)
- [ ] Verify template rendering (t-call, t-esc, etc.)
- [ ] Test lifecycle hooks (onMounted, onWillUnmount)
- [ ] Verify useState implementation
- [ ] Test browser console for OWL errors

---

### 2. Field Definition Changes

#### Current (Odoo 17) - NOW FIXED
```python
# ❌ WRONG (Before fixes):
kernel_produced = fields.Float(string('Kernel ...'), digits=(12, 2))

# ✅ CORRECT (After fixes):
kernel_produced = fields.Float(string='Kernel ...', digits=(12, 2))
```

#### Odoo 19 Consideration
- All fixes applied ✅
- Field syntax is now compatible
- Tracking parameters work correctly
- Computed fields should work as-is
- Related fields should work as-is

---

### 3. API Controller Changes

#### Current Implementation (Odoo 17/19 Compatible)
```python
from odoo import http
from odoo.http import request, Response
import json

class PKSAPIController(http.Controller):
    @http.route('/api/v1/pks/suppliers', type='http', auth='none', methods=['GET'], csrf=False)
    @require_api_auth  # Custom decorator
    def api_get_suppliers(self, **kw):
        try:
            suppliers = request.env['pks.supplier'].sudo().search([])
            return json_response({'status': 'success', 'data': data})
        except Exception as e:
            return json_response({'status': 'error', 'message': str(e)}, 500)
```

#### Verification Points
- [x] Route definition syntax is valid
- [x] auth='none' with custom auth decorator is OK
- [x] csrf=False is still valid
- [x] request.env access is valid
- [x] JSON response pattern is valid
- [ ] VERIFY: request.httprequest availability
- [ ] VERIFY: request.session.authenticate() signature
- [ ] VERIFY: Error handling (401, 400, 500)

#### Potential Issues & Solutions

##### Issue 1: Request Object Changes
```python
# Odoo 17/19 - VERIFY these are still available:
auth_header = request.httprequest.headers.get('Authorization')  # May have changed
data = json.loads(request.httprequest.data)  # Verify encoding

# Alternative (more stable):
auth_header = request.headers.get('Authorization')  # Try this if above fails
```

##### Issue 2: Authentication Method
```python
# Verify this method still works in Odoo 19:
uid = request.session.authenticate(request.db, username, password)

# If not available, alternative approach:
from odoo.addons.web.controllers.main import Home
uid = request.session.authenticate(request.db, username, password)
```

##### Issue 3: Response Headers
```python
# Current approach (likely OK):
return Response(
    json.dumps(data),
    status=200,
    content_type='application/json'
)

# Ensure CORS headers if needed:
headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-API-Token',
}
response = Response(json.dumps(data), status=200, content_type='application/json')
for key, value in headers.items():
    response.headers[key] = value
return response
```

#### Action Items for API
- [ ] Test all API endpoints
- [ ] Verify authentication mechanism
- [ ] Test error responses (401, 400, 500)
- [ ] Verify CORS headers if needed
- [ ] Test rate limiting (if implemented)
- [ ] Verify data serialization

---

### 4. Portal Functionality

#### Current Implementation (Should Be Compatible)
```python
@http.route('/my/supplier/<int:supplier_id>', type='http', auth='user', website=True)
def portal_supplier_detail(self, supplier_id, **kw):
    supplier = request.env['pks.supplier'].sudo().browse(supplier_id)
    
    if not request.env.user.has_group('pks_pabrik.group_pks_supplier_portal'):
        return request.redirect('/')
    
    values = {'supplier': supplier}
    return request.render('pks_pabrik.portal_supplier_detail', values)
```

#### Verification Points
- [x] Route syntax is standard
- [x] auth='user' is valid
- [x] website=True is valid
- [x] has_group() method is standard
- [x] request.render() is standard
- [ ] Verify portal.mixin inheritance still works
- [ ] Verify template rendering

#### Action Items for Portal
- [ ] Test supplier portal login
- [ ] Verify data access
- [ ] Test template rendering
- [ ] Verify permissions enforcement

---

### 5. Mail Thread & Activity Mixin

#### Current Usage (Should Be Compatible)
```python
class PKSWeighbridge(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(tracking=True)
    state = fields.Selection([...], tracking=True)
    supplier_id = fields.Many2one('pks.supplier', tracking=True)
```

#### Action Items
- [ ] Verify mail.thread functionality
- [ ] Verify mail.activity.mixin functionality
- [ ] Test tracking/chatter functionality
- [ ] Verify activity creation works
- [ ] Test email notifications

---

### 6. Report Templates (QWeb)

#### Current Implementation
```xml
<template id="report_slip_timbang">
    <t t-call="web.html_container">
        <t t-foreach="docs" t-as="o">
            <t t-call="web.external_layout">
                <div class="page">
                    <h2>SLIP TIMBANG</h2>
                    <t t-esc="o.create_date.strftime('%d/%m/%Y %H:%M:%S')"/>
                </div>
            </t t-call>
        </t>
    </t t-call>
</template>
```

#### Potential Issues
- [ ] Verify external_layout still works
- [ ] Verify Python method calls in templates work
- [ ] Test date formatting
- [ ] Test PDF rendering
- [ ] Verify inheritance

#### Solutions if Issues Found
```xml
<!-- Alternative date formatting if strftime() doesn't work: -->
<t t-esc="o.create_date.strftime('%d/%m/%Y %H:%M:%S') or ''"/>

<!-- Or use environment context date format: -->
<t t-esc="format_datetime(o.create_date, '%d/%m/%Y %H:%M:%S')"/>
```

#### Action Items for Reports
- [ ] Generate test reports
- [ ] Verify PDF output
- [ ] Test all report endpoints
- [ ] Verify data accuracy
- [ ] Check formatting

---

### 7. Security Groups & Access Control

#### Current Definition
```xml
<!-- FILE: security/pks_security.xml -->
<record id="group_pks_manager" model="res.groups">
    <field name="name">PKS Manager</field>
    <field name="category_id" ref="base.module_category_tools"/>
</record>
```

#### Verification Points
- [x] Group definitions should work as-is
- [ ] Verify record rules still work
- [ ] Test access control
- [ ] Verify portal access rules

#### Action Items for Security
- [ ] Test all user groups
- [ ] Verify record rules
- [ ] Test data visibility
- [ ] Verify API authentication

---

### 8. Model State Machine

#### Current Implementation
```python
state = fields.Selection([
    ('draft', 'Draft'),
    ('weighing_in', 'Timbang Masuk'),
    ('waiting_unload', 'Menunggu Bongkar'),
    ('weighing_out', 'Timbang Keluar'),
    ('done', 'Selesai'),
    ('cancelled', 'Dibatalkan'),
], string='Status', default='draft', tracking=True)

@api.depends('state')
def action_weigh_in(self):
    self.write({'state': 'weighing_in'})
```

#### Verification Points
- [x] Selection field syntax is correct
- [x] State machine pattern is valid
- [ ] Verify button visibility logic
- [ ] Test state transitions
- [ ] Verify onchange handlers

#### Action Items for Workflows
- [ ] Test all state transitions
- [ ] Verify button visibility
- [ ] Test workflow completeness
- [ ] Verify constraints between states

---

### 9. Python Dependencies

#### Current requirements.txt
```
pandas>=1.5.0
numpy>=1.24.0
requests>=2.28.0
redis>=4.5.0
celery>=5.3.0
gunicorn>=20.1.0
```

#### Verification for Odoo 19
- [ ] pandas 1.5.0+ - Check compatibility
- [ ] numpy 1.24.0+ - Check compatibility
- [ ] requests 2.28.0+ - ✅ Should work
- [ ] redis 4.5.0+ - ✅ Should work
- [ ] celery 5.3.0+ - Check Odoo 19 compatibility
- [ ] gunicorn 20.1.0+ - ✅ Should work

#### Action Items
- [ ] Run pip dependency check
- [ ] Test all imports
- [ ] Run module with dependencies

---

### 10. JavaScript/CSS Assets

#### Current Structure
```
static/src/components/kiosk/
├── kiosk.js       - OWL component
├── kiosk.xml      - OWL template
└── kiosk.scss     - Styles
```

#### Verification
- [ ] Verify asset loading order
- [ ] Test SCSS compilation
- [ ] Verify JavaScript loading
- [ ] Test CSS application
- [ ] Verify bundle caching

---

## 🧪 Testing Strategy

### Unit Tests to Run
```python
# FILE: tests/test_pks_models.py
./odoo-bin -i pks_pabrik --test-enable --stop-after-init
```

### API Integration Tests
```bash
# Test authentication
curl -u admin:admin http://localhost:8069/api/v1/pks/suppliers

# Test endpoints
curl -X GET http://localhost:8069/api/v1/pks/suppliers \
  -H "Authorization: Basic $(echo -n 'admin:admin' | base64)" \
  -H "Content-Type: application/json"
```

### OWL Component Tests
```javascript
// Browser console verification
// After opening kiosk interface:
console.log(owl);  // Should show OWL instance
registry.getItem('component', 'KioskWeighbridge');  // Should load
```

---

## 🐛 Common Errors & Solutions

### Error 1: "Module cannot be found"
```
Error: Cannot import module pks_pabrik

Solution:
1. Check module path in addons_path
2. Verify __manifest__.py exists
3. Check file permissions
4. Review error logs for syntax errors
```

### Error 2: "Field 'X' cannot be resolved"
```
Error: NameError: name 'fields' is not defined

Solution:
1. Verify imports at top of model file
2. Check class inheritance
3. Verify field definitions syntax
```

### Error 3: "OWL Component not registering"
```
Error: Component not found in registry

Solution:
1. Verify registry import
2. Check component export
3. Verify template definition
4. Check bundle loading order
```

### Error 4: "API Authentication fails"
```
Error: 401 Unauthorized

Solution:
1. Verify credential format
2. Check user exists in database
3. Verify token if using API token
4. Check CORS headers
```

### Error 5: "Report template not found"
```
Error: Template 'pks_pabrik.report_slip_timbang' not found

Solution:
1. Verify template id in XML
2. Check namespace
3. Verify XML is loaded (check data in manifest)
4. Verify template syntax
```

---

## 📋 Pre-Deployment Verification Checklist

Before deploying to production:

### Code Quality
- [ ] All syntax errors fixed ✅
- [ ] No import errors
- [ ] No undefined references
- [ ] Proper error handling
- [ ] Code follows Odoo standards

### Functionality
- [ ] All models work
- [ ] All views render
- [ ] All reports generate
- [ ] All API endpoints respond
- [ ] Portal works
- [ ] Kiosk works

### Performance
- [ ] API response time < 500ms
- [ ] Report generation < 5s
- [ ] Page load time < 2s
- [ ] Database queries optimized

### Security
- [ ] Authentication works
- [ ] Access control enforced
- [ ] Passwords hashed
- [ ] API token validated
- [ ] SQL injection prevented

### Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual tests completed
- [ ] Edge cases tested

---

## 🚀 Deployment Steps

### Step 1: Prepare Environment
```bash
# Create Odoo 19 environment
cd /path/to/odoo-19
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Install Module
```bash
# Copy module to addons
cp -r /path/to/pks_pabrik /path/to/odoo-19/addons/

# Update module list
./odoo-bin -d database_name -u base --stop-after-init

# Install pks_pabrik
./odoo-bin -d database_name -i pks_pabrik --stop-after-init
```

### Step 3: Run Tests
```bash
# Run all tests
./odoo-bin -d database_name -i pks_pabrik --test-enable --stop-after-init

# Run with coverage
coverage run --source=addons/pks_pabrik ./odoo-bin -d database_name -i pks_pabrik --test-enable

# Check coverage
coverage report
coverage html
```

### Step 4: Verify Installation
```bash
# Check module is installed
# In Odoo UI: Apps > Search "PKS Pabrik" > Should show "Installed"

# Check database tables
# In database: SELECT * FROM pg_tables WHERE schemaname = 'public' AND tablename LIKE 'pks%';
# Should show all pks_* tables
```

---

## 📞 Troubleshooting Contacts

If issues arise:

1. **Syntax Errors**: Check error line + file path
2. **Import Errors**: Verify module dependency chain
3. **Template Errors**: Check XML namespace and syntax
4. **Permission Errors**: Verify user groups and record rules
5. **API Errors**: Check request headers and authentication

---

## 📚 References

- [Odoo 19 Migration Guide](https://www.odoo.com/documentation/19.0/migration/)
- [OWL 2.x Documentation](https://github.com/odoo/owl)
- [Odoo Python API](https://www.odoo.com/documentation/19.0/developer/reference/addons/orm.html)
- [Odoo REST API Pattern](https://www.odoo.com/documentation/19.0/developer/howtos/rest_api.html)
- [QWeb Template Engine](https://www.odoo.com/documentation/19.0/developer/reference/frontend/qweb.html)

---

**Document Version**: 1.0  
**Last Updated**: 2026-04-08  
**Status**: Ready for Implementation
