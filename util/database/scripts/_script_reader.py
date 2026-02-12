"""Class that reads and holds sql scripts."""

from __future__ import annotations

import glob
import os
import pathlib
from typing import TYPE_CHECKING, Any

import log

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

__author__ = "Eduardo Ruiz"

__all__ = ["SQLScripts"]


class _SQLScriptReader:
    def __init__(self, directory: str | pathlib.Path):
        file_list = glob.glob(f"{directory}{os.sep}*.sql")
        self._script_dict: dict[str, str | tuple[str, ...]] = {}

        for script_file in file_list:
            # Open and read the file
            log.logger.debug(
                f"Reading SQL file: {os.path.basename(script_file)}"
            )
            with open(script_file) as file:
                sql = file.read()

            log.logger.debug("Successfully read SQL file.")

            script_name = os.path.splitext(os.path.basename(script_file))[0]

            # Separate all SQL commands by splitting on ';'
            sql_commands = tuple(x for x in sql.split(";") if x.strip() != "")
            if len(sql_commands) == 1:
                self._script_dict[script_name] = sql_commands[0]
            else:
                self._script_dict[script_name] = sql_commands

    def __str__(self) -> str:
        keys = [f"'{x}'" for x in self.keys()]
        return f"SQLScripts([{', '.join(keys)}])"

    def __getattr__(self, item: str) -> str | tuple[str, ...]:
        if item in self._script_dict:
            script = self._script_dict[item]
            return script
        else:
            raise AttributeError(f"{item} is a nonexistent script.")

    def __getitem__(self, item: str) -> str | tuple[str, ...]:
        return self._script_dict[item]

    def keys(self) -> _SQLScriptKeys:
        return _SQLScriptKeys(self._script_dict.keys())

    def commands(self) -> list[str]:
        return list(self._script_dict.values())  # type: ignore[arg-type]

    def items(self) -> list[Any]:
        return list(zip(self.keys(), self.commands(), strict=False))

    def to_dict(self) -> dict[_SQLScriptKeys, Any]:
        return dict(self.items())

    def to_list(self) -> list[tuple[_SQLScriptKeys, Any]]:
        return [(k, v) for k, v in self.items()]

    def __len__(self) -> int:
        return len(self._script_dict)


class _SQLScriptKeys:
    def __init__(self, keys: Iterable[str]):
        self.keys = list(keys)

    def __str__(self) -> str:
        keys = [f"'{x}'" for x in self.keys]
        return f"SQLScriptKeys({', '.join(keys)})"

    def __getitem__(self, item: int) -> str:
        return self.keys[item]

    def __iter__(self) -> Iterator[str]:
        return iter(self.keys)


SQLScripts = _SQLScriptReader(pathlib.Path(__file__).parent.absolute())

if __name__ == "__main__":
    print(SQLScripts.create_database)
    print(SQLScripts.keys())
    print(SQLScripts["create_database"])

    print(SQLScripts[SQLScripts.keys()[0]])

    print(SQLScripts.to_dict())
    print(SQLScripts)
