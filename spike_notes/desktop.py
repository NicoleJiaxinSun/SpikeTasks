"""Independent transparent desktop notes, with a fixed corner collection dock."""
from PySide6.QtCore import Qt, QPointF, QRectF, QRect, QTimer
from PySide6.QtGui import QAction, QCursor, QIcon, QPixmap, QPainter, QColor, QRegion
from PySide6.QtWidgets import (QApplication, QGraphicsView, QGraphicsScene,
                              QMenu, QSystemTrayIcon)
from .app import Board, Window, Note


class NoteWindow(QGraphicsView):
    def __init__(self, owner, note):
        self.canvas = QGraphicsScene()
        super().__init__(self.canvas)
        self.owner, self.note = owner, note
        self.drag_origin = None
        self.setWindowTitle('Spike Notes · ' + note.task['text'][:40])
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet('background: transparent; border: none;')
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.canvas.addItem(note)
        self.follow_note()

    def follow_note(self):
        p = self.note.pos()
        self.setGeometry(round(p.x()) - 12, round(p.y()) - 12, Note.W + 24, Note.H + 42)
        self.setSceneRect(QRectF(self.x(), self.y(), self.width(), self.height()))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.itemAt(event.position().toPoint()) is self.note:
            self.drag_origin = event.globalPosition() - self.note.pos()
            self.note.fade(1)
            self.raise_()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.drag_origin is None:
            super().mouseMoveEvent(event)
            return
        self.note.setPos(event.globalPosition() - self.drag_origin)
        self.owner.board.clamp(self.note)
        self.follow_note()
        board = self.owner.board
        board.spike.hot = board.at_tip(self.note)
        board.spike.update()

    def mouseReleaseEvent(self, event):
        if self.drag_origin is None:
            super().mouseReleaseEvent(event)
            return
        self.drag_origin = None
        board = self.owner.board
        if board.at_tip(self.note):
            board.complete(self.note)
        else:
            self.note.task.update(x=self.note.x(), y=self.note.y())
            self.owner.save()
            self.note.fade(.62)
        board.spike.hot = False
        board.spike.update()

    def mouseDoubleClickEvent(self, event):
        self.drag_origin = None
        self.owner.board.edit(self.note)

    def closeEvent(self, event):
        # Closing an OS window hides it; the tray can show all notes again.
        event.accept()


class DesktopBoard(Board):
    def __init__(self, owner, tasks):
        super().__init__(owner, tasks)
        self.setWindowTitle('Spike Notes · Small wins')
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.viewport().setAutoFillBackground(False)
        self.setToolTip('Right-click for New note, Small wins and Quit')
        self.resize(300, 485)

    def place_dock(self):
        area = QApplication.primaryScreen().availableGeometry()
        self.move(area.right() - self.width() - 16, area.bottom() - self.height() - 16)
        self.relayout()

    def relayout(self):
        self.canvas.setSceneRect(QRectF(self.x(), self.y(), self.viewport().width(), self.viewport().height()))
        self.setSceneRect(self.canvas.sceneRect())
        self.spike.setPos(self.x() + self.viewport().width() / 2, self.y() + 60)
        self.stack()

    def resizeEvent(self, event):
        QGraphicsView.resizeEvent(self, event)
        self.relayout()

    def update_mask(self):
        # Only the collector and paper surfaces receive desktop clicks.
        cx = self.viewport().width() // 2
        region = QRegion(QRect(cx - 8, 60, 16, 390))
        region |= QRegion(QRect(cx - 65, 435, 130, 40), QRegion.RegionType.Ellipse)
        region |= QRegion(QRect(cx - 115, 22, 230, 62))
        for note in self.notes.values():
            if note.scene() is self.canvas:
                polygon = self.mapFromScene(note.mapToScene(note.shape()).toFillPolygon())
                region |= QRegion(polygon)
        self.setMask(region)

    def stack(self):
        super().stack()
        self.update_mask()

    def clamp(self, note):
        point = (note.pos() + QPointF(Note.W / 2, Note.H / 2)).toPoint()
        screen = QApplication.screenAt(point) or QApplication.primaryScreen()
        r = screen.availableGeometry()
        note.setPos(max(r.left() + 12, min(note.x(), r.right() - Note.W - 12)),
                    max(r.top() + 12, min(note.y(), r.bottom() - Note.H - 30)))

    def complete(self, note):
        if note.busy or note.task['completed']:
            return
        host = self.window.note_windows.pop(note.task['id'], None)
        self.canvas.addItem(note)
        if host:
            host.hide()
            host.deleteLater()
        self.raise_()
        super().complete(note)
        self.animations[note.task['id']].valueChanged.connect(lambda _: self.update_mask())
        self.update_mask()

    def mouseDoubleClickEvent(self, event):
        self.create(QPointF(QCursor.pos()) - QPointF(250, 120))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            # Handle this before a completed paper opens its modal wins dialog.
            self.window.menu.popup(event.globalPosition().toPoint())
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event):
        if not self.window.menu.isVisible():
            self.window.menu.popup(event.globalPos())
        event.accept()


class DesktopSession(Window):
    def __init__(self, store):
        super().__init__(store)
        self.note_windows = {}
        self.pinned = False
        old = self.board
        self.layout().removeWidget(old)
        old.setParent(None)
        old.deleteLater()
        self.board = DesktopBoard(self, self.tasks)
        self.menu = QMenu()
        self.menu.addAction('＋ New note', lambda: self.board.create())
        self.wins_action = self.menu.addAction('Small wins', self.board.show_completed)
        self.menu.addAction('Show all notes', self.show_notes)
        pin = self.menu.addAction('Keep above other windows')
        pin.setCheckable(True)
        pin.toggled.connect(self.set_pinned)
        self.menu.addSeparator()
        self.menu.addAction('Quit Spike Notes', self.quit)
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setBrush(QColor('#B5C0AC'))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(3, 3, 26, 26, 5, 5)
        painter.setPen(QColor('#484B47'))
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, 'S')
        painter.end()
        self.tray = QSystemTrayIcon(QIcon(pixmap), self)
        self.tray.setToolTip('Spike Notes')
        self.tray.setContextMenu(self.menu)
        QApplication.primaryScreen().availableGeometryChanged.connect(lambda _: self.board.place_dock())
        QApplication.instance().screenRemoved.connect(lambda _: self.recover_positions())

    def start(self):
        QApplication.instance().setQuitOnLastWindowClosed(False)
        self.board.place_dock()
        self.board.show()
        self.tray.show()
        self.sync_notes()
        self.refresh_count()

    def sync_notes(self):
        if not hasattr(self, 'note_windows'):
            return
        active = {t['id'] for t in self.tasks if not t['completed']}
        for key in list(self.note_windows):
            if key not in active:
                self.note_windows.pop(key).deleteLater()
        for key in active:
            note = self.board.notes[key]
            if note.busy:
                continue
            if key not in self.note_windows:
                self.board.clamp(note)
                note.task.update(x=note.x(), y=note.y())
                host = NoteWindow(self, note)
                host.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, self.pinned)
                self.note_windows[key] = host
                host.show()

    def save(self):
        self.sync_notes()
        saved = super().save()
        if hasattr(self, 'wins_action'):
            count = sum(t['completed'] for t in self.tasks)
            self.wins_action.setText(f'Small wins · {count}')
            self.board.setToolTip(f'{count} small wins · Right-click for menu')
        if not saved and hasattr(self, 'tray'):
            self.tray.setToolTip('Spike Notes · Saving failed; keep the app open')
            self.tray.showMessage('Spike Notes', self.status.text())
        return saved

    def show_notes(self):
        for host in self.note_windows.values():
            host.show()
            host.raise_()
        self.board.show()
        self.board.raise_()

    def set_pinned(self, enabled):
        self.pinned = enabled
        for host in [self.board, *self.note_windows.values()]:
            host.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, enabled)
            host.show()

    def recover_positions(self):
        self.board.place_dock()
        for host in self.note_windows.values():
            self.board.clamp(host.note)
            host.follow_note()
            host.note.task.update(x=host.note.x(), y=host.note.y())
        self.save()

    def quit(self):
        if self.board.animations:
            QTimer.singleShot(1400, self.quit)
            return
        if self.close():
            self.tray.hide()
            QApplication.instance().quit()
