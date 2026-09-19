from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from focuslist.cli import (
    FocusListError,
    add_task,
    complete_task,
    list_tasks,
)


class FocusListSpecTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Path(self.tmp.name) / "focuslist.json"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_add_trims_title_and_assigns_incrementing_ids(self) -> None:
        first = add_task("  Comprar café  ", self.store)
        second = add_task("Enviar correo", self.store)
        self.assertEqual(first.id, 1)
        self.assertEqual(first.title, "Comprar café")
        self.assertEqual(second.id, 2)

    def test_empty_title_is_rejected(self) -> None:
        with self.assertRaisesRegex(FocusListError, "no puede estar vacío"):
            add_task("   ", self.store)

    def test_title_longer_than_80_characters_is_rejected(self) -> None:
        with self.assertRaisesRegex(FocusListError, "80 caracteres"):
            add_task("a" * 81, self.store)

    def test_status_filters_are_deterministic(self) -> None:
        first = add_task("Primera", self.store)
        second = add_task("Segunda", self.store)
        complete_task(first.id, self.store)
        self.assertEqual([task.id for task in list_tasks(self.store, "open")], [second.id])
        self.assertEqual([task.id for task in list_tasks(self.store, "done")], [first.id])

    def test_done_is_idempotent(self) -> None:
        task = add_task("Revisar", self.store)
        _, first_change = complete_task(task.id, self.store)
        _, second_change = complete_task(task.id, self.store)
        self.assertTrue(first_change)
        self.assertFalse(second_change)

    def test_unknown_task_is_rejected(self) -> None:
        with self.assertRaisesRegex(FocusListError, "No existe"):
            complete_task(99, self.store)

    def test_json_file_is_human_readable(self) -> None:
        add_task("Documentar", self.store)
        payload = json.loads(self.store.read_text(encoding="utf-8"))
        self.assertEqual(payload["tasks"][0]["title"], "Documentar")


if __name__ == "__main__":
    unittest.main()

