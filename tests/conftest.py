from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import dash
import pytest
from sqlmodel import Session, SQLModel, create_engine

dash.register_page = MagicMock()  # type: ignore[invalid-assignment]

if TYPE_CHECKING:
    from collections.abc import Generator

    from sqlalchemy.engine import Engine


@pytest.fixture(name="mem_engine")
def mem_engine_fixture() -> Generator[Engine, None, None]:
    """Provide a fresh in-memory SQLite engine with all tables created."""
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    yield engine


@pytest.fixture(name="engine")
def engine_fixture(mem_engine: Engine) -> Engine:
    """Provide an alias of mem_engine for tests requesting engine."""
    return mem_engine


@pytest.fixture(autouse=True)
def mock_all_engines(mem_engine: Engine) -> Generator[None, None, None]:
    """Automatically patch all database engines globally across all modules to ensure complete test isolation."""
    with (
        patch("util.models.engine", mem_engine),
        patch("util.settings.engine", mem_engine),
        patch("pages.collection.engine", mem_engine),
        patch("api.bgg_api.collection.engine", mem_engine),
        patch("api.bgg_api.game_details.engine", mem_engine),
    ):
        yield


@pytest.fixture(name="session")
def session_fixture(mem_engine: Engine) -> Generator[Session, None, None]:
    """Provide a fresh SQLModel Session bound to the in-memory database engine."""
    with Session(mem_engine) as session:
        yield session
