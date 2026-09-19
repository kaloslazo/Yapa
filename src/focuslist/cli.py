"""CLI pequeña para demostrar un flujo SDD con una implementación verificable."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


MAX_TITLE_LENGTH = 80
VALID_STATUSES = {"all", "open", "done"}


class FocusListError(ValueError):
    """Error de dominio que la interfaz puede mostrar sin traceback."""


@dataclass
class Task:
    id: int
    title: str
    done: bool
    created_at: str


def _default_store() -> Path:
    return Path(os.environ.get("FOCUSLIST_DB", ".focuslist.json"))


def load_tasks(store: Path) -> tuple[int, list[Task]]:
    if not store.exists():
        return 1, []
    try:
        payload = json.loads(store.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise FocusListError("El archivo de datos no contiene JSON válido.") from exc
    tasks = [Task(**item) for item in payload.get("tasks", [])]
    next_id = int(payload.get("next_id", 1))
    return next_id, tasks


def save_tasks(store: Path, next_id: int, tasks: Iterable[Task]) -> None:
    store.parent.mkdir(parents=True, exist_ok=True)
    payload = {"next_id": next_id, "tasks": [asdict(task) for task in tasks]}
    temporary = store.with_suffix(store.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(store)


def add_task(title: str, store: Path) -> Task:
    clean_title = title.strip()
    if not clean_title:
        raise FocusListError("El título no puede estar vacío.")
    if len(clean_title) > MAX_TITLE_LENGTH:
        raise FocusListError(
            f"El título no puede superar {MAX_TITLE_LENGTH} caracteres."
        )
    next_id, tasks = load_tasks(store)
    task = Task(
        id=next_id,
        title=clean_title,
        done=False,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    save_tasks(store, next_id + 1, [*tasks, task])
    return task


def list_tasks(store: Path, status: str = "all") -> list[Task]:
    if status not in VALID_STATUSES:
        raise FocusListError("El estado debe ser all, open o done.")
    _, tasks = load_tasks(store)
    if status == "open":
        tasks = [task for task in tasks if not task.done]
    elif status == "done":
        tasks = [task for task in tasks if task.done]
    return sorted(tasks, key=lambda task: task.id)


def complete_task(task_id: int, store: Path) -> tuple[Task, bool]:
    next_id, tasks = load_tasks(store)
    for task in tasks:
        if task.id == task_id:
            changed = not task.done
            task.done = True
            if changed:
                save_tasks(store, next_id, tasks)
            return task, changed
    raise FocusListError(f"No existe la tarea #{task_id}.")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="focuslist")
    parser.add_argument(
        "--store",
        type=Path,
        default=_default_store(),
        help="Ruta del archivo JSON de persistencia.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    add_parser = commands.add_parser("add", help="Crear una tarea.")
    add_parser.add_argument("title")

    list_parser = commands.add_parser("list", help="Listar tareas.")
    list_parser.add_argument("--status", choices=sorted(VALID_STATUSES), default="all")

    done_parser = commands.add_parser("done", help="Completar una tarea.")
    done_parser.add_argument("id", type=int)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "add":
            task = add_task(args.title, args.store)
            print(f"Creada #{task.id}: {task.title}")
        elif args.command == "list":
            tasks = list_tasks(args.store, args.status)
            if not tasks:
                print("No hay tareas.")
            for task in tasks:
                marker = "x" if task.done else " "
                print(f"[{marker}] #{task.id} {task.title}")
        elif args.command == "done":
            task, changed = complete_task(args.id, args.store)
            suffix = "completada" if changed else "ya estaba completada"
            print(f"#{task.id} {suffix}: {task.title}")
        return 0
    except FocusListError as exc:
        print(f"Error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

