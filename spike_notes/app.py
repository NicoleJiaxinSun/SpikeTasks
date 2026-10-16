import math
import random
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QRectF, QPointF, QVariantAnimation, QEasingCurve, QStandardPaths
from PySide6.QtGui import QColor, QPainter, QPen, QFont, QLinearGradient, QPainterPath, QKeySequence, QShortcut, QTransform
from PySide6.QtWidgets import (QApplication, QWidget, QGraphicsView, QGraphicsScene,
    QGraphicsObject, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QDialog,
    QTextEdit, QComboBox, QDialogButtonBox, QMessageBox, QMenu, QScrollArea, QFrame)
from .storage import Store, COLORS, COLOR_NAMES, new_task

STYLE = '''
QWidget { color: #484B47; font-family: 'Helvetica Neue', 'Segoe UI', sans-serif; font-size: 13px; }
QPushButton { background: #E9E7E0; border: 1px solid #D8D9D0; border-radius: 12px; padding: 9px 16px; }
QPushButton:hover { background: #DCDDD3; }
QPushButton:pressed { background: #CDD2C3; }
QTextEdit, QComboBox { background: #FAF9F5; border: 1px solid #D7D8CF; border-radius: 8px; padding: 10px; }
QDialog { background: #F2F1EB; }
QLabel { background: transparent; }
'''


class Note(QGraphicsObject):
    W, H = 212, 158

    def __init__(self, board, task):
        super().__init__()
        self.board, self.task = board, task
        self.busy = False
        self.pierced = task['completed']
        self.dent = 0.0
        self.tilt = 1.0 if task['completed'] else 0.0
        self.flutter = 0.0
        self.hover_anim = None
        self.hovered = False
        self.setAcceptHoverEvents(True)
        self.setTransformOriginPoint(self.W / 2, self.H / 2)
        self.setFlag(QGraphicsObject.GraphicsItemFlag.ItemIsMovable, not task['completed'])
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setOpacity(0.62 if not task['completed'] else 0.94)
        self.setPos(task['x'], task['y'])
        self.setRotation(task['rotation'])

    def boundingRect(self):
        return QRectF(-12, -12, self.W + 24, self.H + 30)

    def paper_transform(self):
        transform = QTransform()
        transform.translate(self.W / 2, self.H / 2)
        transform.shear(self.tilt * (0.24 + self.task['offset'] * 0.015), 0)
        transform.scale(1, 1 - self.tilt * 0.66 + self.flutter * 0.025)
        transform.translate(-self.W / 2, -self.H / 2)
        return transform

    def paper_path(self):
        curl = self.tilt * (7 + abs(self.task['rotation']) * 0.3) + self.dent * 3
        path = QPainterPath()
        path.moveTo(0, 0)
        path.quadTo(self.W / 2, curl * 0.4, self.W, -curl * 0.3)
        path.quadTo(self.W - 4, self.H / 2, self.W + 2, self.H - curl)
        path.quadTo(self.W * 0.6, self.H + curl * 0.5, 0, self.H + curl)
        path.quadTo(4, self.H / 2, 0, 0)
        path.closeSubpath()
        return path

    def shape(self):
        return self.paper_transform().map(self.paper_path())

    def paint(self, p, option, widget=None):
        p.save()
        p.setTransform(self.paper_transform(), True)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        for spread, alpha in [(8, 4), (5, 7), (2, 13)]:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(48, 48, 40, alpha))
            p.drawRoundedRect(QRectF(-spread, 5, self.W + spread * 2, self.H + spread), 5, 5)
        paper = self.paper_path()
        p.save()
        p.translate(0, 3 + self.tilt * 4)
        p.setBrush(QColor(COLORS[self.task['color']]).darker(115))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawPath(paper)
        p.restore()
        p.setBrush(QColor(COLORS[self.task['color']]))
        p.setPen(QPen(QColor(255, 255, 255, 95), 1))
        p.drawPath(paper)
        p.setClipPath(paper)
        wash = QLinearGradient(0, 0, 0, self.H)
        wash.setColorAt(0, QColor(255, 255, 255, 35))
        wash.setColorAt(1, QColor(60, 50, 40, 8))
        p.fillRect(QRectF(1, 1, self.W - 2, self.H - 2), wash)
        p.setPen(QColor('#444942'))
        p.setFont(QFont('Helvetica Neue', 17))
        p.drawText(QRectF(20, 26, self.W - 40, self.H - 58), Qt.TextFlag.TextWordWrap, self.task['text'])
        p.setFont(QFont('Helvetica Neue', 9))
        p.setPen(QColor(66, 70, 63, 150))
        if self.tilt < 0.5 and self.hovered:
            p.drawText(QRectF(20, self.H - 28, self.W - 40, 16), 'DOUBLE-CLICK TO EDIT')
        if self.dent or self.pierced:
            center = QPointF(self.W / 2, self.H / 2)
            p.setPen(QPen(QColor(65, 62, 53, 140), 1))
            for angle in (0, 1.2, 2.7, 4.1, 5.2):
                p.drawLine(center, center + QPointF(math.cos(angle) * 11, math.sin(angle) * 9))
            p.setBrush(QColor('#505852'))
            p.drawEllipse(center, 3 + self.dent * 2, 3 + self.dent * 2)
            p.setPen(QPen(QColor(255, 255, 245, 145), 1))
            p.drawArc(QRectF(center.x() - 5, center.y() - 5, 10, 10), 20 * 16, 160 * 16)

        p.restore()
        if self.pierced:
            # The rod is behind the near half of the paper and in front of its far half.
            # Mapping from scene space keeps it vertical even while the paper flutters.
            p.save()
            p.setClipPath(self.shape())
            tip = self.mapFromScene(self.board.spike.pos() + QPointF(0, 24))
            hole = self.mapFromScene(self.board.spike.pos() + QPointF(0, self.y() + self.H / 2 - self.board.spike.y()))
            p.setPen(QPen(QColor('#899596'), 9))
            p.drawLine(tip, hole)
            p.setPen(QPen(QColor('#DCE3DF'), 2))
            p.drawLine(tip + QPointF(-2, 0), hole + QPointF(-2, 0))
            p.restore()

    def fade(self, value):
        if self.busy or self.task['completed']:
            return
        if self.hover_anim:
            self.hover_anim.stop()
        self.hover_anim = QVariantAnimation(self)
        self.hover_anim.setDuration(180)
        self.hover_anim.setStartValue(self.opacity())
        self.hover_anim.setEndValue(value)
        self.hover_anim.valueChanged.connect(self.setOpacity)
        self.hover_anim.start()

    def hoverEnterEvent(self, e):
        self.hovered = True
        self.update()
        self.fade(1.0)
        super().hoverEnterEvent(e)

    def hoverLeaveEvent(self, e):
        self.hovered = False
        self.update()
        self.fade(0.62)
        super().hoverLeaveEvent(e)

    def mousePressEvent(self, e):
        if self.busy:
            e.ignore()
            return
        if self.task['completed']:
            self.board.show_completed()
            e.accept()
            return
        self.setZValue(self.board.next_z())
        self.setCursor(Qt.CursorShape.ClosedHandCursor)
        self.fade(1.0)
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self.busy:
            return
        super().mouseMoveEvent(e)
        self.board.clamp(self)
        self.board.spike.hot = self.board.at_tip(self)
        self.board.spike.update()

    def mouseReleaseEvent(self, e):
        if self.busy or self.task['completed']:
            return
        super().mouseReleaseEvent(e)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        if self.board.at_tip(self):
            self.board.complete(self)
        else:
            self.task.update(x=self.x(), y=self.y())
            self.board.save()
            self.fade(0.62)
        self.board.spike.hot = False
        self.board.spike.update()

    def mouseDoubleClickEvent(self, e):
        if not self.busy and not self.task['completed']:
            self.board.edit(self)
        e.accept()

    def contextMenuEvent(self, e):
        if self.busy:
            return
        menu = QMenu()
        edit = menu.addAction('Edit note')
        delete = menu.addAction('Delete note')
        chosen = menu.exec(e.screenPos())
        if chosen == edit:
            self.board.edit(self)
        elif chosen == delete:
            self.board.remove(self)


class Spike(QGraphicsObject):
    def __init__(self):
        super().__init__()
        self.hot = False
        self.setZValue(10)
        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)

    def boundingRect(self):
        return QRectF(-120, -32, 240, 470)

    def paint(self, p, option, widget=None):
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        if self.hot:
            p.setBrush(QColor(170, 185, 157, 65))
            p.drawEllipse(QPointF(0, 12), 38, 38)
        p.setBrush(QColor(70, 72, 61, 18))
        p.drawEllipse(QRectF(-65, 395, 130, 20))
        metal = QLinearGradient(-30, 0, 30, 0)
        metal.setColorAt(0, QColor('#747D7E'))
        metal.setColorAt(0.35, QColor('#DCE1DF'))
        metal.setColorAt(0.6, QColor('#AEB7B7'))
        metal.setColorAt(1, QColor('#636E70'))
        p.setBrush(metal)
        p.drawRoundedRect(QRectF(-50, 381, 100, 20), 10, 10)
        rod = QPainterPath()
        rod.moveTo(0, 0)
        rod.lineTo(5, 24)
        rod.lineTo(5, 387)
        rod.lineTo(-5, 387)
        rod.lineTo(-5, 24)
        rod.closeSubpath()
        p.drawPath(rod)
        p.setPen(QPen(QColor(255, 255, 255, 180), 1))
        p.drawLine(QPointF(-2, 27), QPointF(-2, 378))
        p.setPen(QColor('#8C9386'))
        p.setFont(QFont('Helvetica Neue', 10))
        p.drawText(QRectF(-110, -32, 220, 22), Qt.AlignmentFlag.AlignCenter,
                   'RELEASE TO COMPLETE' if self.hot else 'A PLACE FOR SMALL WINS')


class Editor(QDialog):
    def __init__(self, parent, task=None):
        super().__init__(parent)
        self.setWindowTitle('Edit note' if task else 'A new little task')
        self.resize(380, 260)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel('One thing at a time.'))
        self.text = QTextEdit()
        self.text.setPlaceholderText('What would you like to do?')
        self.text.setPlainText(task['text'] if task else '')
        layout.addWidget(self.text)
        self.color = QComboBox()
        for name, hex_color in zip(COLOR_NAMES, COLORS):
            self.color.addItem(name)
            self.color.setItemData(self.color.count() - 1, QColor(hex_color), Qt.ItemDataRole.DecorationRole)
        self.color.setCurrentIndex(task['color'] if task else random.randrange(len(COLORS)))
        layout.addWidget(self.color)
        self.hint = QLabel('Up to 280 characters · short notes feel best')
        layout.addWidget(self.hint)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.text.setFocus()

    def accept(self):
        if not 0 < len(self.text.toPlainText().strip()) <= 280:
            self.hint.setText('Please write between 1 and 280 characters.')
            return
        super().accept()


class Board(QGraphicsView):
    def __init__(self, window, tasks):
        self.canvas = QGraphicsScene()
        super().__init__(self.canvas)
        self.window, self.tasks = window, tasks
        self.z_counter = 100
        self.animations = {}
        self.notes = {}
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet('background: transparent; border: none;')
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.spike = Spike()
        self.canvas.addItem(self.spike)
        for t in tasks:
            self.add_item(t)

    def next_z(self):
        self.z_counter += 1
        return self.z_counter

    def add_item(self, task):
        note = Note(self, task)
        note.setZValue(self.next_z() if not task['completed'] else 20)
        self.canvas.addItem(note)
        self.notes[task['id']] = note
        return note

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.canvas.setSceneRect(0, 0, self.viewport().width(), self.viewport().height())
        self.spike.setPos(self.viewport().width() - 155, max(85, self.viewport().height() - 465))
        self.stack()
        for note in self.notes.values():
            if not note.task['completed'] and not note.busy:
                self.clamp(note)
                note.task.update(x=note.x(), y=note.y())

    def clamp(self, note):
        r = self.canvas.sceneRect()
        note.setPos(max(15, min(note.x(), r.width() - Note.W - 15)),
                    max(15, min(note.y(), r.height() - Note.H - 15)))

    def at_tip(self, note):
        center = note.pos() + QPointF(Note.W / 2, Note.H / 2)
        tip = self.spike.pos() + QPointF(0, 12)
        return abs(center.x() - tip.x()) < 68 and abs(center.y() - tip.y()) < 70

    @staticmethod
    def stack_height(index):
        # Leave visible air between the first wins, then fit larger collections.
        return 270 * (1 - math.exp(-index / 22.5))

    def stack_position(self, task, index):
        return self.spike.pos() + QPointF(-Note.W / 2, 350 - Note.H / 2 - self.stack_height(index))

    def stack(self):
        for index, t in enumerate(t for t in self.tasks if t['completed']):
            note = self.notes[t['id']]
            note.setPos(self.stack_position(t, index))
            note.setRotation(t['rotation'])
            note.tilt, note.flutter = 1.0, 0.0
            note.update()
            note.setZValue(20 + min(index, 50) * 0.1)

    def complete(self, note):
        if note.busy or note.task['completed']:
            return
        if note.hover_anim:
            note.hover_anim.stop()
        note.busy = True
        note.setOpacity(1)
        note.setFlag(QGraphicsObject.GraphicsItemFlag.ItemIsMovable, False)
        start = QPointF(note.pos())
        target = self.spike.pos() - QPointF(Note.W / 2, Note.H / 2 - 12)
        index = sum(t['completed'] for t in self.tasks)
        note.task.update(rotation=random.uniform(-16, 16), offset=random.uniform(-5, 5))
        finish = self.stack_position(note.task, index)
        anim = QVariantAnimation(self)
        anim.setDuration(1250)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)

        def frame(t):
            if t < 0.24:
                f = 1 - (1 - t / 0.24) ** 3
                note.setPos(start + (target - start) * f)
            elif t < 0.40:
                note.dent = (t - 0.24) / 0.16
                note.setPos(target + QPointF(0, note.dent * 8))
            else:
                note.pierced = True
                f = min(1.0, (t - 0.40) / 0.46)
                pos = target + (finish - target) * f ** 2
                if t > 0.86:
                    u = (t - 0.86) / 0.14
                    pos = finish + QPointF(0, -9 * math.sin(u * math.pi) * (1 - u))
                note.setPos(pos)
                flatten = min(1.0, (t - 0.40) / 0.30)
                note.tilt = flatten * flatten * (3 - 2 * flatten)
                note.flutter = math.sin(f * math.pi * 4) * (1 - f)
                note.setRotation(note.task['rotation'] * f + note.flutter * 7)
                # Switch behind the active notes once it has passed through the tip.
                note.setZValue(30 + min(index, 50) * 0.1)
            note.update()

        def settled():
            note.task.update(completed=True, x=note.x(), y=note.y())
            self.tasks.remove(note.task)
            self.tasks.append(note.task)
            note.busy = False
            note.setOpacity(0.94)
            self.animations.pop(note.task['id'], None)
            self.stack()
            self.save()
            anim.deleteLater()

        anim.valueChanged.connect(frame)
        anim.finished.connect(settled)
        self.animations[note.task['id']] = anim
        anim.start()

    def save(self):
        self.window.save()

    def create(self, pos=None):
        dialog = Editor(self.window)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        pos = pos or QPointF(60 + random.randrange(200), 45 + random.randrange(150))
        task = new_task(dialog.text.toPlainText(), dialog.color.currentIndex(), pos.x(), pos.y())
        self.tasks.append(task)
        note = self.add_item(task)
        self.clamp(note)
        task.update(x=note.x(), y=note.y())
        self.save()

    def edit(self, note):
        dialog = Editor(self.window, note.task)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            note.task.update(text=dialog.text.toPlainText().strip(), color=dialog.color.currentIndex())
            note.update()
            self.save()

    def remove(self, note):
        if note.busy:
            return
        self.tasks.remove(note.task)
        self.notes.pop(note.task['id'])
        note.scene().removeItem(note)
        note.deleteLater()
        self.stack()
        self.save()

    def mouseDoubleClickEvent(self, e):
        if not self.itemAt(e.position().toPoint()):
            self.create(self.mapToScene(e.position().toPoint()))
        else:
            super().mouseDoubleClickEvent(e)

    def show_completed(self):
        dialog = QDialog(self.window)
        dialog.setWindowTitle('Your small wins')
        dialog.resize(460, 430)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel('Every finished note stays here.'))
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        contents = QWidget()
        rows = QVBoxLayout(contents)
        done = [t for t in self.tasks if t['completed']]
        if not done:
            rows.addWidget(QLabel('Your first small win is waiting.'))
        for t in reversed(done):
            row = QHBoxLayout()
            text = QLabel(t['text'])
            text.setWordWrap(True)
            row.addWidget(text, 1)
            restore = QPushButton('Restore')
            delete = QPushButton('Delete')
            row.addWidget(restore)
            row.addWidget(delete)
            def restore_task(checked=False, task=t):
                note = self.notes[task['id']]
                task.update(completed=False, rotation=0, x=65, y=65)
                note.pierced, note.dent = False, 0
                note.tilt, note.flutter = 0.0, 0.0
                note.update()
                note.setPos(65, 65)
                note.setRotation(0)
                note.setOpacity(0.62)
                note.setZValue(self.next_z())
                note.setFlag(QGraphicsObject.GraphicsItemFlag.ItemIsMovable, True)
                self.stack()
                self.save()
                dialog.accept()
            restore.clicked.connect(restore_task)
            delete.clicked.connect(lambda checked=False, task=t: (self.remove(self.notes[task['id']]), dialog.accept()))
            rows.addLayout(row)
        rows.addStretch()
        scroll.setWidget(contents)
        layout.addWidget(scroll)
        close = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close.rejected.connect(dialog.reject)
        layout.addWidget(close)
        dialog.exec()


class Window(QWidget):
    def __init__(self, store):
        super().__init__()
        self.store = store
        self.overlay = False
        self.drag_offset = None
        self.load_error = None
        try:
            tasks = store.load()
        except (ValueError, OSError, KeyError, TypeError) as error:
            tasks = []
            self.load_error = str(error)
        if tasks is None:
            tasks = [new_task('Make room for one good idea', 3, 70, 85),
                     new_task('Take a little breathing break', 0, 340, 175),
                     new_task('Drag this note to the spike tip', 4, 100, 310)]
        self.tasks = tasks
        self.setWindowTitle('Spike Notes')
        self.resize(1120, 760)
        self.setMinimumSize(820, 620)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 20, 28, 18)
        header = QHBoxLayout()
        title = QLabel('spike notes  /  one thing at a time')
        title.setStyleSheet('font-size: 17px; font-weight: 500;')
        header.addWidget(title, 1)
        new = QPushButton('+ New note')
        new.clicked.connect(lambda: self.board.create())
        header.addWidget(new)
        self.done = QPushButton('Small wins · 0')
        self.done.clicked.connect(lambda: self.board.show_completed())
        header.addWidget(self.done)
        overlay = QPushButton('Overlay')
        overlay.setCheckable(True)
        overlay.toggled.connect(self.toggle_overlay)
        header.addWidget(overlay)
        close = QPushButton('×')
        close.setToolTip('Close Spike Notes')
        close.clicked.connect(self.close)
        header.addWidget(close)
        layout.addLayout(header)
        self.board = Board(self, tasks)
        layout.addWidget(self.board, 1)
        self.status = QLabel('Double-click empty space to add · double-click a note to edit · right-click to delete')
        self.status.setStyleSheet('color: #858C7E; font-size: 11px;')
        layout.addWidget(self.status)
        self.refresh_count()
        QShortcut(QKeySequence.StandardKey.New, self, activated=lambda: self.board.create())
        QShortcut(QKeySequence('Escape'), self, activated=lambda: overlay.setChecked(False))
        if self.load_error:
            self.status.setText('Could not read saved notes. Original file preserved; saving is disabled.')

    def refresh_count(self):
        self.done.setText(f"Small wins · {sum(t['completed'] for t in self.tasks)}")

    def save(self):
        self.refresh_count()
        if self.load_error:
            return False
        try:
            self.store.save(self.tasks)
            return True
        except OSError as error:
            self.status.setText(f'Could not save notes: {error}. Keep this window open and retry.')
            return False

    def toggle_overlay(self, enabled):
        self.overlay = enabled
        geometry = self.geometry()
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, enabled)
        flags = Qt.WindowType.Window
        if enabled:
            flags |= Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.setGeometry(geometry)
        self.show()
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(244, 244, 237, 195 if self.overlay else 255))
        p.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 18 if self.overlay else 0, 18 if self.overlay else 0)

    def mousePressEvent(self, e):
        if self.overlay and e.button() == Qt.MouseButton.LeftButton and e.position().y() < 74:
            self.drag_offset = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self.drag_offset is not None:
            self.move(e.globalPosition().toPoint() - self.drag_offset)

    def mouseReleaseEvent(self, e):
        self.drag_offset = None

    def closeEvent(self, e):
        if self.board.animations:
            self.status.setText('Let the note settle for a moment before closing.')
            e.ignore()
            return
        if not self.save() and not self.load_error:
            choice = QMessageBox.question(self, 'Notes are not saved', 'Saving failed. Close and lose unsaved changes?',
                QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel)
            if choice != QMessageBox.StandardButton.Discard:
                e.ignore()
                return
        e.accept()


def main():
    app = QApplication(sys.argv)
    app.setOrganizationName('SpikeNotes')
    app.setApplicationName('Spike Notes')
    app.setStyleSheet(STYLE)
    path = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)) / 'tasks.json'
    from .desktop import DesktopSession
    window = DesktopSession(Store(path))
    window.start()
    if window.load_error:
        QMessageBox.warning(window, 'Saved notes need attention',
            f'Your saved file was preserved at:\n{path}\n\n{window.load_error}\n\nMove or repair that file, then restart to enable saving.')
    sys.exit(app.exec())
