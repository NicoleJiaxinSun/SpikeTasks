import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import tempfile
import unittest
from pathlib import Path
from PySide6.QtWidgets import QApplication, QPushButton
from PySide6.QtCore import QPointF, Qt, QTimer
from PySide6.QtTest import QTest
from spike_notes.storage import Store, new_task
from spike_notes.app import Window, STYLE, Note

app = QApplication.instance() or QApplication([])
app.setStyleSheet(STYLE)


class PrototypeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.tmp.name) / 'tasks.json')
        self.window = Window(self.store)
        self.window.show()
        QTest.qWait(30)

    def tearDown(self):
        QTest.qWait(1350 if self.window.board.animations else 0)
        self.window.close()
        self.tmp.cleanup()

    def test_drag_hover_complete_reload_delete(self):
        board = self.window.board
        note = next(iter(board.notes.values()))
        old = QPointF(note.pos())
        start = board.mapFromScene(old + QPointF(35, 35))
        QTest.mousePress(board.viewport(), Qt.MouseButton.LeftButton, pos=start)
        QTest.mouseMove(board.viewport(), start + QPointF(45, 25).toPoint(), delay=30)
        QTest.mouseRelease(board.viewport(), Qt.MouseButton.LeftButton, pos=start + QPointF(45, 25).toPoint())
        self.assertGreater(note.x(), old.x())
        note.fade(1.0)
        QTest.qWait(220)
        self.assertAlmostEqual(note.opacity(), 1.0, places=2)
        center = board.mapFromScene(note.pos() + QPointF(Note.W / 2, Note.H / 2))
        tip = board.mapFromScene(board.spike.pos() + QPointF(0, 12))
        QTest.mousePress(board.viewport(), Qt.MouseButton.LeftButton, pos=center)
        QTest.mouseMove(board.viewport(), tip, delay=30)
        self.assertTrue(board.at_tip(note))
        QTest.mouseRelease(board.viewport(), Qt.MouseButton.LeftButton, pos=tip)
        board.complete(note)  # Repeated release must not start another animation.
        self.assertEqual(len(board.animations), 1)
        QTest.qWait(540)
        self.assertTrue(note.pierced)
        self.assertFalse(note.task['completed'])
        QTest.qWait(810)
        self.assertTrue(note.task['completed'])
        self.assertFalse(note.busy)
        self.assertEqual(sum(t['completed'] for t in self.store.load()), 1)
        again = Window(self.store)
        again.show()
        QTest.qWait(30)
        restored = again.board.notes[note.task['id']]
        self.assertTrue(restored.pierced)
        self.assertEqual(restored.tilt, 1.0)
        self.assertLess(restored.shape().boundingRect().height(), 85)
        self.assertAlmostEqual(restored.rotation(), note.rotation())
        again.board.remove(restored)
        self.assertEqual(sum(t['completed'] for t in self.store.load()), 0)
        again.close()

    def test_create_edit_restore(self):
        board = self.window.board
        def fill(text, color):
            dialog = QApplication.activeModalWidget()
            dialog.text.setPlainText(text)
            dialog.color.setCurrentIndex(color)
            dialog.accept()
        QTimer.singleShot(20, lambda: fill('First idea', 3))
        board.create(QPointF(55, 70))
        note = board.notes[self.window.tasks[-1]['id']]
        QTimer.singleShot(20, lambda: fill('Edited idea', 5))
        board.edit(note)
        self.assertEqual(note.task['text'], 'Edited idea')
        self.assertEqual(note.task['color'], 5)
        board.complete(note)
        QTest.qWait(1350)
        def restore():
            dialog = QApplication.activeModalWidget()
            next(b for b in dialog.findChildren(QPushButton) if b.text() == 'Restore').click()
        QTimer.singleShot(20, restore)
        board.show_completed()
        self.assertFalse(note.task['completed'])
        self.assertFalse(note.pierced)
        self.assertEqual(note.tilt, 0.0)
        self.assertFalse(next(t for t in self.store.load() if t['id'] == note.task['id'])['completed'])

    def test_atomic_unicode_and_empty_state(self):
        task = new_task('完成一个小任务', 2)
        self.store.save([task])
        self.assertEqual(self.store.load(), [task])
        self.store.save([])
        self.assertEqual(self.store.load(), [])
        self.assertFalse(self.store.path.with_suffix('.tmp').exists())

    def test_corrupt_file_is_preserved(self):
        self.store.path.write_text('{ broken', encoding='utf-8')
        other = Window(self.store)
        self.assertIsNotNone(other.load_error)
        other.save()
        self.assertEqual(self.store.path.read_text(), '{ broken')
        other.close()

    def test_out_of_bounds_is_clamped(self):
        note = next(iter(self.window.board.notes.values()))
        note.setPos(10000, -500)
        self.window.board.clamp(note)
        self.assertGreaterEqual(note.y(), 15)
        self.assertLessEqual(note.x() + Note.W, self.window.board.sceneRect().width())

if __name__ == '__main__':
    unittest.main()
