# Spike Notes

A quiet, desktop-first task prototype in Python + PySide6. Morandi paper notes fade into the background, become opaque on hover, and collect on a metallic spike when finished. No accounts or online services.

## Run

Requires Python 3.10+ and a desktop OS supported by PySide6 (recent macOS, Windows or Linux).

```sh
cd spike-notes
python3 -m venv .venv
source .venv/bin/activate
# Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python main.py
```

## Use

- **New note** or **⌘N / Ctrl+N** creates a task. Double-click blank canvas space to place it there.
- Drag notes to arrange them; hover reveals their full color.
- Double-click a note to edit its text and color. Right-click to edit or delete.
- Drag a note's **center near the spike tip**, then release when “RELEASE TO COMPLETE” appears. It snaps toward the tip, dents, tears, tilts into a shallow paper plane, flutters down the rod, and settles above the base. Curved edges, thin paper rims, layered shadows and random rotation give the stack a 2.5D appearance. The rod passes behind the near half of each paper and in front of its far half.
- Click **Small wins** or the paper stack to read completed notes, restore them, or delete them.
- **Overlay** enables a translucent, frameless, always-on-top canvas. Drag the empty header to move it; **Esc** returns to the normal window. The × button closes either mode.

The overlay is one movable application window: it does not replace the OS desktop or allow clicks through its canvas. Transparency depends on desktop compositing. The standard window is the reliable fallback. Large stacks have a capped visual height; all completed notes remain available in Small wins.

## Data

Notes, colors, positions, completion state, stack offset and rotation automatically save to `tasks.json` in Qt's per-user application data folder (`SpikeNotes/Spike Notes`). On macOS this is normally under `~/Library/Application Support/`; on Windows under `%APPDATA%`; on Linux under `~/.local/share/`.

First launch includes three editable demo notes. Deleting all notes keeps the board empty after restarting. Saves replace the previous JSON atomically. If the file is damaged, the original is preserved and saving is disabled until you repair or move it and restart. Avoid running multiple instances against the same data file. Window size and overlay mode are not persisted.

## Files and verification

- `main.py` — launch entry point
- `spike_notes/app.py` — canvas, note rendering, editing, overlay and animation
- `spike_notes/storage.py` — validated JSON storage and palette
- `tests/test_app.py` — interaction, animation and persistence checks

```sh
python -m unittest discover -s tests -v
```

Tests use Qt's offscreen platform. Native transparency and the feel of dragging should also be checked on your desktop.

Qt references: [translucent windows](https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QWidget.html), [animation framework](https://doc.qt.io/qtforpython-6/overviews/qtcore-animation-overview.html).
