# Benchmarking

Run `make benchmark ROWS=1000000 SEED=20260727` to generate, validate, feature-engineer, and write a
deterministic synthetic workload. The machine-readable report is written to
`artifacts/benchmarks/rows-1000000-seed-20260727/benchmark.json`.

## Report contract

The report schema version is `1.0.0`. It records the requested, processed, and rejected row counts;
generation, Spark-processing, and total wall-clock seconds; Parquet output bytes; input and output
dataset fingerprints; feature version; seed; Spark version, master and shuffle partitions; and the
host platform, Python version, processor description, and logical CPU count.

## Interpretation

Compare runs only when their row count, seed, code revision, Spark settings, and hardware context
are equivalent. Warm caches, concurrent workloads, storage speed, and local Spark scheduling can
materially affect elapsed time. A successful million-row local run proves that this implementation
completed that workload in the recorded environment; it is not a production throughput, latency,
capacity, or cost claim. Preserve a report alongside any published performance statement.
