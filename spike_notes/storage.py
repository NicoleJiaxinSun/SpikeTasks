"""Versioned, atomic local persistence; no network services."""
import json
import os
from pathlib import Path
from uuid import uuid4

COLORS = ['#F3BCC6', '#F6C29A', '#F5E69F', '#C8EFC1', '#B8D8F5', '#D8C5EE']
COLOR_NAMES = ['Rose pink', 'Peach orange', 'Cream yellow', 'Fresh green', 'Mist blue', 'Soft violet']
LEGACY_COLORS = [0, 3, 4, 5, 1, 2, 1, 4]


def new_task(text, color=0, x=80, y=100):
    return dict(id=uuid4().hex, text=text.strip(), color=color, x=x, y=y,
                completed=False, rotation=0, offset=0)


class Store:
    def __init__(self, path):
        self.path = Path(path)

    def load(self):
        if not self.path.exists():
            return None
        data = json.loads(self.path.read_text(encoding='utf-8'))
        if not isinstance(data, dict) or data.get('version') not in (1, 2):
            raise ValueError('Unsupported task file version')
        tasks = data.get('tasks')
        if not isinstance(tasks, list):
            raise ValueError('Invalid task list')
        seen = set()
        for t in tasks:
            if not isinstance(t, dict) or not isinstance(t.get('id'), str) or t['id'] in seen:
                raise ValueError('Invalid or duplicate task ID')
            seen.add(t['id'])
            if not isinstance(t.get('text'), str) or not 0 < len(t['text'].strip()) <= 280:
                raise ValueError('Invalid task text')
            palette_size = len(LEGACY_COLORS) if data['version'] == 1 else len(COLORS)
            if type(t.get('color')) is not int or not 0 <= t['color'] < palette_size:
                raise ValueError('Invalid color')
            if type(t.get('completed')) is not bool:
                raise ValueError('Invalid completion state')
            for key in ('x', 'y', 'rotation', 'offset'):
                v = t.get(key)
                if type(v) not in (int, float) or not -10000 < v < 10000:
                    raise ValueError('Invalid note position')
        if data['version'] == 1:
            for t in tasks:
                t['color'] = LEGACY_COLORS[t['color']]
        return tasks

    def save(self, tasks):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix('.tmp')
        with temporary.open('w', encoding='utf-8') as f:
            json.dump(dict(version=2, tasks=tasks), f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        temporary.replace(self.path)
