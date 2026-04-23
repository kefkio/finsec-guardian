# Backend — Data Model

**Status:** Current  
**Last Updated:** April 2026  
**Audience:** Developers, Architects

---

## Table of Contents

1. [Entity Relationship Diagram](#entity-relationship-diagram)
2. [Scanner Models](#scanner-models)
3. [Threats Models](#threats-models)
4. [Records Models](#records-models)
5. [Audit Models](#audit-models)
6. [Indexes & Performance](#indexes--performance)
7. [Constraints & Validation](#constraints--validation)

---

## Entity Relationship Diagram

```
┌─────────────────┐     1    ┌─────────────────────┐
│ User (Django)   │ ◀─────── │ ScanJob             │
│ id, username    │     user  │ id, source_code,    │
│ email, password │          │ contract_name,       │
└─────────────────┘          │ contract_address,    │
                             │ status, risk_score,  │
                             │ risk_verdict,        │
                             │ risk_assessment,     │
                             │ metadata, ...        │
                             └──────────┬──────────┘
                                  1  │  │  1
                    ┌────────────────┘  └────────────────┐
                    │ M                                   │ 1
            ┌───────┴──────┐                     ┌───────┴──────────┐
            │ Finding      │                     │ ScanReport       │
            │ id, swc_id,  │                     │ report_type,     │
            │ title,       │                     │ format, content, │
            │ severity,    │                     │ generated_at     │
            │ confidence,  │                     └──────────────────┘
            │ line_number, │
            │ status, ...  │
            └──────┬───────┘
                   │ M                 M
            ┌──────┴───────┐   ┌──────────────────┐
            │ FindingCategory│  │ SuppressionBaseline│
            │ name, swc_id  │  │ reason, expires_at │
            └───────────────┘  └──────────────────────┘

┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│ ThreatRecord     │   │ TamperRecord     │   │ AuditEvent       │
│ title, category, │   │ content,         │   │ event_type,      │
│ likelihood,      │   │ content_hash,    │   │ severity, actor, │
│ impact,          │   │ previous_hash,   │   │ resource,        │
│ mitigation       │   │ chain_valid      │   │ message, ip,     │
└──────────────────┘   └──────────────────┘   │ metadata         │
                                              └──────────────────┘
```

---

## Scanner Models

### ScanJob

Root entity representing a single contract scan execution.

```python
class ScanJob(models.Model):
    # Identity
    user = ForeignKey(User, on_delete=SET_NULL, null=True, blank=True)

    # Source
    source_code = TextField()
    source_code_hash = CharField(max_length=64, db_index=True)
    contract_name = CharField(max_length=255, blank=True)
    contract_address = CharField(max_length=42, blank=True, db_index=True)
    source_type = CharField(choices=['text', 'upload'], default='text')
    uploaded_filename = CharField(max_length=255, blank=True)
    uploaded_file_size = PositiveIntegerField(default=0)

    # Compilation
    syntax_valid = BooleanField(default=False)
    solidity_version = ForeignKey(SolidityVersion, null=True, blank=True)
    compiled_abi = JSONField(null=True, blank=True)
    compiled_bytecode = TextField(blank=True)
    compilation_error = TextField(blank=True)

    # Lifecycle
    status = CharField(choices=['pending', 'compiling', 'analyzing', 'complete', 'failed'])
    progress_percentage = IntegerField(default=0)
    created_at = DateTimeField(auto_now_add=True, db_index=True)
    started_at = DateTimeField(null=True, blank=True)
    completed_at = DateTimeField(null=True, blank=True)

    # Scan Results
    total_findings = IntegerField(default=0)
    critical_count = IntegerField(default=0)
    high_count = IntegerField(default=0)
    medium_count = IntegerField(default=0)
    low_count = IntegerField(default=0)
    info_count = IntegerField(default=0)

    # Risk
    risk_score = IntegerField(default=0)          # 0–100
    risk_verdict = CharField(max_length=30)        # CRITICAL/HIGH/MEDIUM/LOW/MINIMAL RISK
    risk_assessment = JSONField(default=dict)       # Full RiskScorer output

    # Context
    ip_address = GenericIPAddressField(null=True, blank=True)
    user_agent = TextField(blank=True)
    metadata = JSONField(default=dict)             # Includes onchain_data when available
```

**Status transitions:** `pending → compiling → analyzing → complete` (or `→ failed` at any stage)

**Auto-hash:** On save, if `source_code` is set and `source_code_hash` is empty, the model computes `SHA256(source_code)`.

**update_finding_counts():** Recomputes all severity counters from the related `Finding` queryset.

### Finding

Individual vulnerability reported by any analyzer.

```python
class Finding(models.Model):
    scan = ForeignKey(ScanJob, related_name='findings', on_delete=CASCADE)
    category = ForeignKey(FindingCategory, on_delete=SET_NULL, null=True, blank=True)

    swc_id = CharField(max_length=20, blank=True, db_index=True)
    title = CharField(max_length=255)
    severity = CharField(choices=['critical', 'high', 'medium', 'low', 'info'], db_index=True)
    description = TextField()
    code_snippet = TextField(blank=True)
    recommendation = TextField(blank=True)
    reference_url = URLField(blank=True)

    line_number = IntegerField(null=True, blank=True)
    line_start = IntegerField(null=True, blank=True)
    line_end = IntegerField(null=True, blank=True)
    column = IntegerField(null=True, blank=True)

    confidence = IntegerField(default=100)         # 0–100
    impact_score = IntegerField(default=0)          # 0–10

    status = CharField(choices=['new', 'acknowledged', 'suppressed', 'resolved'], default='new')
    is_false_positive = BooleanField(default=False)
    suppression_reason = TextField(blank=True)

    found_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    resolved_at = DateTimeField(null=True, blank=True)

    tags = JSONField(default=list)                 # ["slither", "reentrancy", "onchain-enriched"]
    metadata = JSONField(default=dict)             # {"tool": "slither", "check": "reentrancy-eth"}
```

**Ordering:** `-severity, -found_at`

**Unique constraint:** `(scan, swc_id, line_number, title)` — prevents duplicate findings in same scan.

**get_risk_score():** Computed as `severity_weight × (confidence / 100)`.

### FindingCategory

Vulnerability classification taxonomy.

```python
class FindingCategory(models.Model):
    name = CharField(max_length=100, unique=True)
    swc_id = CharField(max_length=20, blank=True)
    description = TextField(blank=True)
```

### SuppressionBaseline

Suppressed findings with optional expiry.

```python
class SuppressionBaseline(models.Model):
    scan = ForeignKey(ScanJob, related_name='baselines', on_delete=CASCADE)
    finding = ForeignKey(Finding, on_delete=CASCADE)
    suppressed_by = ForeignKey(User, on_delete=SET_NULL, null=True, blank=True)
    reason = TextField()
    created_at = DateTimeField(auto_now_add=True)
    expires_at = DateTimeField(null=True, blank=True)

    def is_expired(self):
        return self.expires_at and timezone.now() > self.expires_at
```

### ScanReport

Generated reports in various formats.

```python
class ScanReport(models.Model):
    scan = OneToOneField(ScanJob, on_delete=CASCADE, related_name='report')
    report_type = CharField(choices=['summary', 'detailed', 'executive'])
    format = CharField(choices=['json', 'pdf', 'html'])
    content = BinaryField()
    generated_at = DateTimeField(auto_now_add=True)
    generated_by = ForeignKey(User, on_delete=SET_NULL, null=True, blank=True)
```

### SolidityVersion

Supported compiler versions.

```python
class SolidityVersion(models.Model):
    version = CharField(max_length=20, unique=True)
    is_default = BooleanField(default=False)
    is_active = BooleanField(default=True)
```

---

## Threats Models

### ThreatRecord

STRIDE-based threat entry with risk scoring.

```python
class ThreatRecord(models.Model):
    CATEGORY_CHOICES = [
        ('spoofing', 'Spoofing'), ('tampering', 'Tampering'),
        ('repudiation', 'Repudiation'), ('info_disclosure', 'Information Disclosure'),
        ('dos', 'Denial of Service'), ('elevation', 'Elevation of Privilege'),
    ]

    title = CharField(max_length=255)
    category = CharField(max_length=30, choices=CATEGORY_CHOICES)
    description = TextField()
    likelihood = IntegerField(choices=1–5, default=3)
    impact = IntegerField(choices=1–5, default=3)
    mitigation = TextField(blank=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    @property
    def risk_score(self):
        return self.likelihood * self.impact  # 1–25
```

**Ordering:** `-impact, -likelihood`

---

## Records Models

### TamperRecord

SHA-256 hash-chained integrity record.

```python
class TamperRecord(models.Model):
    content = TextField()
    content_hash = CharField(max_length=64)       # SHA-256 hex digest
    previous_hash = CharField(max_length=64, default='0' * 64)  # Genesis: 64 zeros
    chain_valid = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)
```

**Hash computation:** `SHA256(previous_hash + content)`

**Chain verification:** Walk all records in order; recompute expected hash for each; flag mismatches.

---

## Audit Models

### AuditEvent

Append-only security event log entry.

```python
class AuditEvent(models.Model):
    SEVERITY_CHOICES = [
        ('critical', 'Critical'), ('high', 'High'), ('medium', 'Medium'),
        ('low', 'Low'), ('info', 'Info'),
    ]

    event_type = CharField(max_length=100)
    severity = CharField(max_length=20, choices=SEVERITY_CHOICES, default='info')
    actor = CharField(max_length=255, blank=True)
    resource = CharField(max_length=255, blank=True)
    ip_address = GenericIPAddressField(null=True, blank=True)
    message = TextField()
    metadata = JSONField(default=dict)
    timestamp = DateTimeField(auto_now_add=True)
```

**Ordering:** `-timestamp`

---

## Indexes & Performance

| Model | Index | Fields | Purpose |
|-------|-------|--------|---------|
| ScanJob | Composite | `-created_at, status` | Dashboard listing |
| ScanJob | Composite | `user, -created_at` | Per-user scan history |
| ScanJob | Single | `source_code_hash` | Deduplication check |
| ScanJob | Single | `contract_address` | Etherscan lookup |
| Finding | Composite | `scan, -severity` | Scan detail page |
| Finding | Single | `swc_id` | SWC-based queries |
| Finding | Single | `status` | Status-based filtering |

---

## Constraints & Validation

| Constraint | Model | Type | Description |
|-----------|-------|------|-------------|
| Unique together | Finding | DB constraint | `(scan, swc_id, line_number, title)` |
| Unique | FindingCategory | DB constraint | `name` |
| Unique | SolidityVersion | DB constraint | `version` |
| Source XOR file | ScanJobSerializer | Serializer | `source_code` or `uploaded_file`, not both |
| Risk score range | ScanJob | Convention | 0–100 (not enforced at DB level) |
| Severity enum | Finding | DB choices | `critical`, `high`, `medium`, `low`, `info` |
| Hash chain integrity | TamperRecord | Application logic | Verified by `verify()` action |
