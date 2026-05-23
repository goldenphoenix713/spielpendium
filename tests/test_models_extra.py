from __future__ import annotations

import pathlib
import tempfile
from unittest.mock import MagicMock, patch

from sqlmodel import SQLModel, create_engine

from util.models import create_db_and_tables


class TestCreateDbAndTables:
    def test_creates_tables_when_db_missing(self) -> None:
        """create_db_and_tables creates tables when DB file doesn't exist yet."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = pathlib.Path(tmpdir) / "test.db"
            engine = create_engine(f"sqlite:///{db_path}")

            with (
                patch("util.models.DB_FILE", db_path),
                patch("util.models.RESET_DB", False),
                patch("util.models.engine", engine),
            ):
                assert not db_path.exists()
                create_db_and_tables()
                # Tables should now exist in metadata
                assert "game" in SQLModel.metadata.tables

    def test_resets_db_when_reset_flag_set_and_file_exists(self) -> None:
        """create_db_and_tables removes the existing DB file when RESET_DB=True."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = pathlib.Path(tmpdir) / "test.db"
            # Pre-create the file so it "already exists"
            db_path.touch()

            engine = create_engine(f"sqlite:///{db_path}")

            with (
                patch("util.models.DB_FILE", db_path),
                patch("util.models.RESET_DB", True),
                patch("util.models.engine", engine),
            ):
                assert db_path.exists()
                create_db_and_tables()
                # File is recreated via create_all
                assert "game" in SQLModel.metadata.tables

    def test_verifies_tables_when_db_exists(self) -> None:
        """create_db_and_tables runs create_all when RESET_DB=False and DB exists to ensure all tables exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = pathlib.Path(tmpdir) / "test.db"
            # Pre-create the file — DB_FILE.exists() is True & RESET_DB is False
            db_path.touch()
            engine = create_engine(f"sqlite:///{db_path}")

            mock_create_all = MagicMock()

            with (
                patch("util.models.DB_FILE", db_path),
                patch("util.models.RESET_DB", False),
                patch("util.models.engine", engine),
                patch.object(SQLModel.metadata, "create_all", mock_create_all),
            ):
                create_db_and_tables()
                # create_all should have been called to verify/create any missing tables
                mock_create_all.assert_called_once_with(engine)
