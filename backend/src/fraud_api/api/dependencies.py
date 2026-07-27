"""Request dependency providers."""

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends

from fraud_api.core.config import Settings, get_settings
from fraud_api.models.loader import ModelBundle, load_model_bundle


def get_model_provider(
    settings: Annotated[Settings, Depends(get_settings)],
) -> Callable[[], ModelBundle]:
    return lambda: load_model_bundle(settings)
