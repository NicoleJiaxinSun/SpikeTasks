import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import tempfile
import unittest
from pathlib import Path
from PySide6.QtWidgets import QApplication, QPushButton
from PySide6.QtCore import QTimer, QPointF, Qt
from PySide6.QtTest import QTest
from spike_notes.desktop import DesktopSession
from spike_notes.storage import Store, new_task

app = QApplication.instance() or QApplication([])

class DesktopTests(unittest.TestCase):
    def test_independent_notes_complete_restore_and_reload(self):
        with tempfile.TemporaryDirectory() as folder:
            store = Store(Path(folder) / 'tasks.json')
            store.save([new_task('Desktop task', x=120, y=130)])
            session = DesktopSession(store)
            session.start()
            QTest.qWait(30)
            note = next(iter(session.board.notes.values()))
            host = session.note_windows[note.task['id']]
            self.assertIsNot(note.scene(), session.board.canvas)
            self.assertTrue(host.isVisible())
            note.setPos(180, 160)
            host.follow_note()
            note.task.update(x=180, y=160)
            session.save()
            self.assertEqual(store.load()[0]['x'], 180)
            session.board.complete(note)
            self.assertNotIn(note.task['id'], session.note_windows)
            self.assertIs(note.scene(), session.board.canvas)
            QTest.qWait(1350)
            self.assertTrue(store.load()[0]['completed'])
            def restore():
                dialog = QApplication.activeModalWidget()
                next(b for b in dialog.findChildren(QPushButton) if b.text() == 'Restore').click()
            QTimer.singleShot(20, restore)
            session.board.show_completed()
            self.assertIn(note.task['id'], session.note_windows)
            self.assertIsNot(note.scene(), session.board.canvas)
            self.assertFalse(store.load()[0]['completed'])
            for host in session.note_windows.values():
                host.close()
            session.board.close()
            session.tray.hide()
            session.close()

    def test_ten_wins_have_visible_spacing(self):
        with tempfile.TemporaryDirectory() as folder:
            store = Store(Path(folder) / 'tasks.json')
            tasks = [new_task(str(i)) for i in range(10)]
            for task in tasks:
                task['completed'] = True
            store.save(tasks)
            session = DesktopSession(store)
            session.start()
            # A right press on a completed paper must open the creation menu,
            # without entering the modal Small wins dialog.
            note = session.board.notes[tasks[-1]['id']]
            point = session.board.mapFromScene(note.pos() + QPointF(106, 79))
            QTest.mousePress(session.board.viewport(), Qt.MouseButton.RightButton, pos=point)
            self.assertTrue(session.menu.isVisible())
            self.assertIsNone(QApplication.activeModalWidget())
            self.assertTrue(any('New note' in a.text() for a in session.menu.actions()))
            session.menu.hide()
            QTest.mouseRelease(session.board.viewport(), Qt.MouseButton.RightButton, pos=point)
            positions = [session.board.notes[t['id']].y() for t in tasks]
            self.assertGreater(positions[0] - positions[-1], 85)
            self.assertGreater(positions[-2] - positions[-1], 7)
            self.assertLess(session.board.stack_height(1000), 271)
            session.board.close()
            session.tray.hide()
            session.close()
