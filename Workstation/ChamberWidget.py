from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import pkgutil
import os
import csv
import importlib
from datetime import datetime
from Workstation.IconButton import IconButton
from Workstation.ScrollLabel import ScrollLabel
from Workstation.AddLoggerDialog import AddLoggerDialog
from Events.GUIEventLogger import GUIEventLogger
from Events.FileEventLogger import FileEventLogger


class ChamberWidget(QGroupBox):
    def __init__(self, wsg, chamber_index, task_index, sn="default", afp="", pfp="", event_loggers=([], []), parent=None):
        super(ChamberWidget, self).__init__(parent)
        self.workstation = wsg.workstation
        self.wsg = wsg
        chamber = QVBoxLayout(self)
        chamber_bar = QVBoxLayout(self)
        row1 = QHBoxLayout(self)

        # Widget corresponding to the chamber number that contains this task
        self.chamber_id = QLabel(chamber_index)
        self.chamber_id.setFont(QFont('Arial', 32))
        row1.addWidget(self.chamber_id)

        # Widget corresponding to the name of subject completing this task
        subject_box = QGroupBox('Subject')
        subject_box_layout = QHBoxLayout(self)
        subject_box.setLayout(subject_box_layout)
        self.subject = QLineEdit(sn)
        self.subject.textChanged.connect(self.subject_changed)
        subject_box_layout.addWidget(self.subject)
        row1.addWidget(subject_box)

        # Widget corresponding to the name of the task being completed
        task_box = QGroupBox('Task')
        task_box_layout = QHBoxLayout(self)
        task_box.setLayout(task_box_layout)
        self.task_name = QComboBox()
        tasks = []
        for f in pkgutil.iter_modules(['Tasks']):  # Get all classes in the Tasks folder
            if not f.name == "Task":  # Ignore the abstract class
                tasks.append(f.name)
        self.task_name.addItems(tasks)
        self.task_name.setCurrentIndex(task_index)
        task_box_layout.addWidget(self.task_name)
        row1.addWidget(task_box)

        chamber_bar.addLayout(row1)
        row2 = QHBoxLayout(self)

        # Widget corresponding to the path to the address file. A blank path indicates the default is being used
        address_file = QGroupBox('Address File')
        address_file_layout = QHBoxLayout(self)
        address_file.setLayout(address_file_layout)
        self.address_file_path = QLineEdit(afp)
        self.address_file_path.setReadOnly(True)
        address_file_layout.addWidget(self.address_file_path)
        self.address_file_browse = QPushButton()
        self.address_file_browse.setIcon(QIcon('Workstation/icons/folder.svg'))
        self.address_file_browse.setFixedWidth(30)
        self.address_file_browse.clicked.connect(lambda: self.get_file_path(self.address_file_path, "AddressFiles"))
        address_file_layout.addWidget(self.address_file_browse)
        row2.addWidget(address_file)

        # Widget corresponding to the path to the protocol file. A blank path indicates the default is being used
        protocol_file = QGroupBox('Protocol')
        protocol_file_layout = QHBoxLayout(self)
        protocol_file.setLayout(protocol_file_layout)
        self.protocol_path = QLineEdit(pfp)
        self.protocol_path.setReadOnly(True)
        protocol_file_layout.addWidget(self.protocol_path)
        self.protocol_file_browse = QPushButton()
        self.protocol_file_browse.setIcon(QIcon('Workstation/icons/folder.svg'))
        self.protocol_file_browse.setFixedWidth(30)
        self.protocol_file_browse.clicked.connect(lambda: self.get_file_path(self.protocol_path, "Protocols"))
        protocol_file_layout.addWidget(self.protocol_file_browse)
        row2.addWidget(protocol_file)

        chamber_bar.addLayout(row2)
        row3 = QHBoxLayout(self)

        # Widget corresponding to the path for the output folder for any file event loggers
        output_file = QGroupBox('Output Folder')
        output_file_layout = QHBoxLayout(self)
        output_file.setLayout(output_file_layout)
        desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
        self.output_file_path = QLineEdit(
            "{}/py-behav/{}/Data/{}/{}/".format(desktop, self.task_name.currentText(), self.subject.text(),
                                                datetime.now().strftime("%m-%d-%Y")))
        self.output_file_path.textChanged.connect(self.output_file_changed)
        output_file_layout.addWidget(self.output_file_path)
        row3.addWidget(output_file)

        # Widget corresponding to controls for playing/pausing/stopping the task
        session_box = QGroupBox('Session')
        session_layout = QHBoxLayout(self)
        session_box.setLayout(session_layout)
        self.play_button = IconButton('Workstation/icons/play.svg', 'Workstation/icons/play_hover.svg')
        self.play_button.setFixedWidth(30)
        self.play_button.clicked.connect(self.play_pause)
        session_layout.addWidget(self.play_button)
        self.stop_button = IconButton('Workstation/icons/stop.svg', 'Workstation/icons/stop_hover.svg',
                                      'Workstation/icons/stop_disabled.svg')
        self.stop_button.setFixedWidth(30)
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop)
        session_layout.addWidget(self.stop_button)
        row3.addWidget(session_box)

        chamber_bar.addLayout(row3)
        chamber.addLayout(chamber_bar)

        # Widget corresponding to a log of task events
        self.event_log = ScrollLabel()
        self.event_log.setMaximumHeight(100)
        self.event_log.setMinimumHeight(100)
        self.event_log.verticalScrollBar().rangeChanged.connect(
            lambda: self.event_log.verticalScrollBar().setValue(self.event_log.verticalScrollBar().maximum()))
        chamber.addWidget(self.event_log)

        self.setLayout(chamber)

        self.event_loggers = [GUIEventLogger(self.event_log)] + event_loggers[0]
        self.logger_params = event_loggers[1]
        self.workstation.add_task(int(chamber_index) - 1, self.task_name.currentText(),
                                  self.workstation.sources, self.address_file_path.text(),
                                  self.protocol_path.text(), self.event_loggers)
        self.task = self.workstation.tasks[int(chamber_index) - 1]
        self.output_file_changed()

    def refresh(self):
        self.workstation.remove_task(int(self.chamber_id.text()) - 1)
        self.workstation.add_task(int(self.chamber_id.text()) - 1, self.task_name.currentText(),
                                  self.workstation.sources, self.address_file_path.text(),
                                  self.protocol_path.text(), self.event_loggers)

    def get_file_path(self, le, dir_type):
        desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
        file_name = QFileDialog.getOpenFileName(self, 'Select File',
                                                "{}/py-behav/{}/{}/".format(desktop, self.task_name.currentText(),
                                                                            dir_type),
                                                '*.csv')
        if len(file_name[0]) > 0:
            le.setText(file_name[0])
            self.refresh()

    def play_pause(self):
        if not self.task.started:
            self.play_button.icon = 'Workstation/icons/pause.svg'
            self.play_button.hover_icon = 'Workstation/icons/pause_hover.svg'
            self.play_button.setIcon(QIcon(self.play_button.icon))
            self.stop_button.setEnabled(True)
            self.subject.setEnabled(False)
            self.task_name.setEnabled(False)
            self.address_file_browse.setEnabled(False)
            self.protocol_file_browse.setEnabled(False)
            self.output_file_path.setEnabled(False)
            self.event_log.setText("")
            self.workstation.start_task(int(self.chamber_id.text()) - 1)
        elif self.task.paused:
            self.play_button.icon = 'Workstation/icons/pause.svg'
            self.play_button.hover_icon = 'Workstation/icons/pause_hover.svg'
            self.play_button.setIcon(QIcon(self.play_button.icon))
            self.task.resume()
        else:
            self.play_button.icon = 'Workstation/icons/play.svg'
            self.play_button.hover_icon = 'Workstation/icons/play_hover.svg'
            self.play_button.setIcon(QIcon(self.play_button.icon))
            self.task.pause()

    def stop(self):
        self.play_button.icon = 'Workstation/icons/play.svg'
        self.play_button.hover_icon = 'Workstation/icons/play_hover.svg'
        self.play_button.setIcon(QIcon(self.play_button.icon))
        self.stop_button.setEnabled(False)
        self.subject.setEnabled(True)
        self.task_name.setEnabled(True)
        self.address_file_browse.setEnabled(True)
        self.protocol_file_browse.setEnabled(True)
        self.output_file_path.setEnabled(True)
        self.workstation.stop_task(int(self.chamber_id.text()) - 1)

    def subject_changed(self):
        self.task.metadata["subject"] = self.subject.text()
        desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
        self.output_file_path.setText(
            "{}/py-behav/{}/Data/{}/{}/".format(desktop, self.task_name.currentText(), self.subject.text(),
                                                datetime.now().strftime("%m-%d-%Y")))

    def output_file_changed(self):
        for el in self.event_loggers:
            if isinstance(el, FileEventLogger):
                el.output_folder = self.output_file_path.text()

    def contextMenuEvent(self, event):
        if not self.task.started:
            menu = QMenu(self)
            save_config = menu.addAction("Save Configuration")
            clear_chamber = menu.addAction("Clear Chamber")
            add_logger = menu.addAction("Add Event Logger")
            action = menu.exec_(self.mapToGlobal(event.pos()))
            if action == save_config:
                desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
                if not os.path.exists("{}/py-behav/Configurations/".format(desktop)):
                    os.makedirs("{}/py-behav/Configurations/".format(desktop))
                file_name = QFileDialog.getSaveFileName(self, 'Save Configuation',
                                                        "{}/py-behav/Configurations/{}-{}-{}.csv".format(desktop,
                                                                                                         self.chamber_id.text(),
                                                                                                         self.subject.text(),
                                                                                                         self.task_name.currentText()),
                                                        '*.csv')
                with open(file_name[0], "w", newline='') as out:
                    w = csv.writer(out)
                    w.writerow(["Chamber", self.chamber_id.text()])
                    w.writerow(["Subject", self.subject.text()])
                    w.writerow(["Task", self.task_name.currentText()])
                    w.writerow(["Address File", self.address_file_path.text()])
                    w.writerow(["Protocol", self.protocol_path.text()])
                    el_text = ""
                    for i in range(1, len(self.event_loggers)):
                        el_text += type(self.event_loggers[i]).__name__ + "((" + ''.join(f"||{w}||" for w in self.logger_params[i-1]) + "))"
                    w.writerow(["EventLoggers", el_text])
            elif action == clear_chamber:
                self.wsg.remove_task(self.chamber_id.text())
            elif action == add_logger:
                ld = AddLoggerDialog()
                if ld.exec():
                    logger_type = getattr(importlib.import_module("Events." + ld.logger.currentText()), ld.logger.currentText())
                    self.logger_params.append(ld.params)
                    self.event_loggers.append(logger_type(*ld.params))
                    self.output_file_changed()