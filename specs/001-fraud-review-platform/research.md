# Research: Fraud Review Platform

## Spark runtime

**Decision**: Use Python 3.12, PySpark 4.2.x, Java 17, Spark SQL DataFrames, window functions, and
Parquet in local mode for development and tests.

**Rationale**: Spark 4.2 supports Python 3.10+ and requires Java 17 or later. The DataFrame API maps
directly to validation, joins, aggregation, and partitioned Parquet without Python-row UDF overhead.
The same jobs can run locally and later on a real cluster. See the official [PySpark installation
requirements](https://spark.apache.org/docs/latest/api/python/getting_started/install.html).

**Alternatives considered**: Spark 3.5 LTS-style compatibility would broaden older environments but
adds no benefit to a new portfolio project. Pandas or Polars would simplify a small demo but would
undercut the explicit distributed-processing goal. Spark Connect adds a server process without
helping the initial local pipeline.

## Operational versus analytical storage

**Decision**: Store transactional workflow state in PostgreSQL and immutable analytical snapshots
in Parquet with manifest files containing hashes, schemas, counts, configuration, and lineage.

**Rationale**: PostgreSQL provides constraints and transactions for idempotent ingestion, alert
review, and audit history. Columnar Parquet is a natural Spark interchange for repeatable feature
and training datasets. Keeping the two roles distinct avoids turning the operational database into a
data lake or using files for mutable workflows.

**Alternatives considered**: PostgreSQL-only processing makes Spark's role artificial and scales
poorly for historical scans. Parquet-only operational state complicates updates and concurrency.
Object storage is production-realistic but unnecessary locally; a mounted directory retains a clean
upgrade path.

## Fraud model

**Decision**: Start with XGBoost binary classification, chronological train/validation/test splits,
class weighting, early stopping, PR-AUC model selection, and a versioned JSON model artifact.

**Rationale**: Gradient-boosted trees perform well on heterogeneous tabular features, support fast
single-row inference, and expose per-row contribution values. XGBoost's JSON format preserves model
structure portably. Precision, recall, confusion counts, and alert volume make threshold trade-offs
visible in a highly imbalanced problem.

**Alternatives considered**: LightGBM is a valid later experiment but supporting both initially
doubles artifact and explanation paths. Logistic regression is an important benchmark and will be
retained as a test baseline, not the primary demo model. Spark ML gradient boosting would keep
training distributed but provides a less convenient low-latency Python serving and explanation path.

## Offline and online feature consistency

**Decision**: Define feature names, types, defaults, bounds, and semantic versions in one small
Python package imported by both pipelines and the API. Spark implementations and scalar online
implementations receive golden parity tests.

**Rationale**: The two runtimes cannot share identical execution code without placing Spark in the
request path. Sharing definitions and fixtures while testing implementations against the same
expected rows makes drift detectable and preserves low latency.

**Alternatives considered**: Recomputing all history synchronously is too slow. Serving Spark output
directly works only for batch scores. A feature-store product is unjustified for the MVP.

## API and idempotency

**Decision**: Use a versioned JSON HTTP contract. The client supplies a UUID transaction identifier;
the database enforces uniqueness. A repeated identical request returns the existing result, while a
conflicting payload for the same identifier returns a conflict response.

**Rationale**: Network retries are normal and must not create duplicate financial events. Persisting
the transaction and its terminal scoring state in one database transaction provides a clear audit
boundary. OpenAPI supports generated frontend types and contract tests.

**Alternatives considered**: Server-generated identifiers cannot make client retries idempotent.
Separate idempotency keys add another mapping without value for the demonstration.

## Explainability

**Decision**: Store the top positive and negative tree contribution values for each score, mapped to
plain-language factor labels and accompanied by a non-causality disclaimer.

**Rationale**: Per-prediction factors let analysts inspect why a case ranked highly and remain tied
to the immutable score. Storing the compact explanation makes later model changes unable to rewrite
history.

**Alternatives considered**: Global importance cannot explain one transaction. Full explanation
vectors increase storage and expose internal features unnecessarily. Natural-language generation
could hallucinate causality and is excluded.

## Local orchestration

**Decision**: Docker Compose runs PostgreSQL, the API, and frontend. Spark batch commands run in a
dedicated pipeline image or locally through the package environment, using Java 17. Kafka is absent
from the MVP.

**Rationale**: Separating the API and Spark environments keeps the serving image small and avoids a
JVM in every API worker. Compose gives a repeatable one-command application environment while
allowing pipeline jobs to run on demand.

**Alternatives considered**: Kubernetes is operationally disproportionate. Running everything in
one container obscures boundaries and produces a large, brittle image. Kafka adds failure modes
before the batch and request flows are proven.
