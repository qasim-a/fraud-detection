# Data Model: Fraud Review Platform

## Conventions

- Identifiers are UUIDs supplied by the generator or ingestion client.
- All event and audit timestamps are timezone-aware UTC instants.
- Monetary amounts use fixed-point decimal values and retain ISO 4217 currency codes.
- Immutable event and prediction records are never updated in place; review workflow records keep
  explicit history.
- Flexible metadata is allowed only in named JSON objects with application-level schemas.

## Operational entities

### Account

| Field | Type | Rules |
|---|---|---|
| `id` | UUID | Primary key |
| `external_ref` | string | Unique synthetic reference; no real account number |
| `home_country` | string | ISO 3166-1 alpha-2 |
| `home_region` | string | Synthetic region code |
| `opened_at` | timestamp | Must not be after creation time |
| `segment` | enum | `consumer`, `small_business` |
| `created_at` | timestamp | Server assigned |

Relationships: one account has many transactions.

### Merchant

| Field | Type | Rules |
|---|---|---|
| `id` | UUID | Primary key |
| `external_ref` | string | Unique synthetic reference |
| `category_code` | string | Four-digit synthetic merchant category |
| `country` | string | ISO 3166-1 alpha-2 |
| `region` | string | Synthetic region code |
| `risk_tier` | enum | `low`, `medium`, `high`; generator context, not a fraud verdict |
| `created_at` | timestamp | Server assigned |

Relationships: one merchant has many transactions.

### Transaction

| Field | Type | Rules |
|---|---|---|
| `id` | UUID | Primary key and client idempotency identifier |
| `account_id` | UUID | Required account reference |
| `merchant_id` | UUID | Required merchant reference |
| `event_time` | timestamp | Required; future tolerance is configurable |
| `amount` | decimal(18,2) | Greater than zero and below configured demo maximum |
| `currency` | string | Three uppercase characters from supported demo set |
| `channel` | enum | `card_present`, `ecommerce`, `wallet`, `atm` |
| `country` | string | ISO 3166-1 alpha-2 |
| `region` | string | Synthetic region code |
| `device_id` | string | Synthetic opaque identifier |
| `ip_hash` | string | Synthetic stable token, not a real IP address |
| `status` | enum | `accepted`, `scored`, `scoring_failed` |
| `payload_hash` | string | Unique-request conflict detection |
| `ingested_at` | timestamp | Server assigned |

Constraints: the identifier is unique. A repeated identifier and equal payload hash is idempotent;
a repeated identifier with a different hash is a conflict. Core transaction fields are immutable.

State transition: `accepted -> scored` or `accepted -> scoring_failed`. A failed transaction may be
retried by an explicit future recovery workflow; it is not silently overwritten in the MVP.

### Feature Snapshot

| Field | Type | Rules |
|---|---|---|
| `id` | UUID | Primary key |
| `transaction_id` | UUID | Unique transaction reference |
| `feature_version` | string | Semantic version |
| `values` | JSON object | Validated finite scalar values keyed by registered feature name |
| `source_as_of` | timestamp | Latest historical instant used; not after transaction event time |
| `created_at` | timestamp | Server assigned |

### Model Version

| Field | Type | Rules |
|---|---|---|
| `id` | UUID | Primary key |
| `name` | string | Human-readable model family |
| `version` | string | Unique immutable semantic/build version |
| `feature_version` | string | Must match scoring feature definition |
| `dataset_id` | string | Training dataset manifest fingerprint |
| `artifact_uri` | string | Repository-external artifact location |
| `artifact_sha256` | string | Integrity hash |
| `metrics` | JSON object | Required precision, recall, PR-AUC, confusion counts, threshold, volume |
| `threshold` | decimal | Inclusive range 0 through 1 |
| `status` | enum | `candidate`, `active`, `retired` |
| `created_at` | timestamp | Training completion time |
| `activated_at` | timestamp | Nullable; required for active or retired versions |

Constraint: at most one version is active. Model version rows are immutable except controlled state
transitions `candidate -> active -> retired`.

### Fraud Score

| Field | Type | Rules |
|---|---|---|
| `id` | UUID | Primary key |
| `transaction_id` | UUID | Unique transaction reference |
| `feature_snapshot_id` | UUID | Required immutable feature snapshot |
| `model_version_id` | UUID | Required model version |
| `probability` | decimal | Inclusive range 0 through 1 |
| `risk_band` | enum | `low`, `medium`, `high`, `critical` |
| `threshold` | decimal | Active threshold at scoring time |
| `explanation_status` | enum | `available`, `unavailable` |
| `explanation_factors` | JSON array | Ranked signed contributions and display labels |
| `scored_at` | timestamp | Server assigned |

Relationships: a score may create zero or one alert. Score rows are immutable.

### Alert

| Field | Type | Rules |
|---|---|---|
| `id` | UUID | Primary key |
| `fraud_score_id` | UUID | Unique score reference |
| `status` | enum | `open`, `in_review`, `closed` |
| `created_at` | timestamp | Time score met threshold |
| `updated_at` | timestamp | Latest workflow change |

State transitions: `open -> in_review -> closed`; `open -> closed`; `in_review -> open` is allowed
for release back to the queue. Closed alerts are reopened only through a recorded new history event.

### Review Decision

| Field | Type | Rules |
|---|---|---|
| `id` | UUID | Primary key |
| `alert_id` | UUID | Required alert reference |
| `outcome` | enum | `confirmed_fraud`, `legitimate`, `needs_review` |
| `note` | string | Optional, maximum 2,000 characters |
| `reviewer_ref` | string | Synthetic/demo analyst identity |
| `created_at` | timestamp | Server assigned |

Review decisions are append-only. The latest decision determines the displayed outcome; prior
decisions remain visible in history.

### Alert History

| Field | Type | Rules |
|---|---|---|
| `id` | UUID | Primary key |
| `alert_id` | UUID | Required alert reference |
| `event_type` | enum | `created`, `status_changed`, `decision_recorded`, `reopened` |
| `from_status` | enum | Nullable for creation |
| `to_status` | enum | Required for status changes |
| `review_decision_id` | UUID | Nullable; set for decision event |
| `actor_ref` | string | System or synthetic analyst reference |
| `created_at` | timestamp | Server assigned |

## Analytical entities

### Processing Run

Stored as a manifest and optionally mirrored into PostgreSQL for dashboard status.

| Field | Type | Rules |
|---|---|---|
| `id` | UUID | Unique run identifier |
| `job_name` | string | Registered pipeline job |
| `job_version` | string | Source/configuration version |
| `status` | enum | `running`, `succeeded`, `failed` |
| `input_uris` | array | Ordered immutable inputs |
| `input_fingerprints` | object | SHA-256 or manifest identity per input |
| `schema_version` | string | Input and output contract version |
| `configuration` | object | Seed, time range, partitions, feature version |
| `processed_count` | integer | Non-negative |
| `rejected_count` | integer | Non-negative |
| `output_uri` | string | Present only for successful output |
| `output_fingerprint` | string | Present only for successful output |
| `started_at` | timestamp | Required |
| `completed_at` | timestamp | Required for terminal states |
| `error_summary` | string | Sanitized; required for failed state |

### Feature Dataset Row

Parquet schema consists of transaction identity and event time, label and label provenance, split
name, registered feature columns with fixed types, and `feature_version`. It excludes raw notes,
credentials, direct identifiers, future review values, and any post-event aggregate.

### Dataset Manifest

Records dataset identifier, schema version, feature version, ordered source fingerprints, split
boundaries, row counts by split and label, quality counts, partitions, output files, aggregate file
hash, generator seed when applicable, and producing run identifier.

## Indexes and reconciliation

- Transaction indexes: `(event_time)`, `(account_id, event_time)`, `(merchant_id, event_time)`.
- Fraud score indexes: `(probability desc, scored_at desc)` and `(model_version_id, scored_at)`.
- Alert indexes: `(status, created_at desc)` plus join access through unique `fraud_score_id`.
- Review decision index: `(alert_id, created_at desc)`.
- Dashboard aggregates are computed from operational facts using one inclusive-start/exclusive-end UTC
  range contract. Cached or materialized summaries, if later added, must reconcile exactly.
