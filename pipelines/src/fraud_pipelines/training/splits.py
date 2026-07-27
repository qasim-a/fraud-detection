# pyright: basic
"""Deterministic chronological train, validation, and test assignment."""

import pandas as pd


def chronological_split(
    frame: pd.DataFrame, train_fraction: float = 0.7, validation_fraction: float = 0.15
) -> pd.DataFrame:
    ordered = frame.sort_values(["event_time", "id"], kind="stable").reset_index(drop=True).copy()
    train_end = int(len(ordered) * train_fraction)
    validation_end = int(len(ordered) * (train_fraction + validation_fraction))
    ordered["split"] = "test"
    ordered.loc[: train_end - 1, "split"] = "train"
    ordered.loc[train_end : validation_end - 1, "split"] = "validation"
    return ordered
