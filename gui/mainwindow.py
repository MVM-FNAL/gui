#!/usr/bin/env python3
from PyQt5 import QtWidgets, uic
from PyQt5 import QtCore, QtGui, QtWidgets


from maindisplay.maindisplay import MainDisplay
from settings.settings import Settings
from settings.settingsfile import SettingsFile

from toolbar.toolbar import Toolbar
from menu.menu import Menu
from settings.settingsbar import SettingsBar
from alarms.alarms import Alarms
from alarms.guialarms import GuiAlarms
from alarms.alarmsbar import AlarmsBar

from toolsettings.toolsettings import ToolSettings
from monitor.monitor import Monitor
from data_filler import DataFiller
from data_handler import DataHandler
from start_stop_worker import StartStopWorker
from alarm_handler import AlarmHandler

import pyqtgraph as pg
import sys
import time

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, config, esp32, *args, **kwargs):
        """
        Initializes the main window for the MVM GUI. See below for subfunction setup description.
        """

        super(MainWindow, self).__init__(*args, **kwargs)
        uic.loadUi('mainwindow.ui', self) # Load the .ui file

        self.config = config
        self.esp32 = esp32

        '''
        Start the alarm handler, which will check for ESP alarms
        '''
        self.alarm_h = AlarmHandler(self.config, self.esp32)

        '''
        Get the toppane and child pages
        '''
        self.toppane    = self.findChild(QtWidgets.QStackedWidget, "toppane")
        self.main       = self.findChild(QtWidgets.QWidget,        "main")
        self.initial    = self.findChild(QtWidgets.QWidget,        "initial")
        self.startup    = self.findChild(QtWidgets.QWidget,        "startup")
        self.settings   = self.findChild(QtWidgets.QWidget,        "settings")


        '''
        Get the center pane (plots) widgets
        '''
        self.centerpane         = self.findChild(QtWidgets.QStackedWidget, "centerpane")
        self.plots_all          = self.findChild(QtWidgets.QWidget,        "plots_all")
        self.alarms_settings    = self.findChild(QtWidgets.QWidget,        "alarms_settings")

        '''
        Get the bottombar and child pages
        '''
        self.bottombar       = self.findChild(QtWidgets.QStackedWidget, "bottombar")
        self.toolbar         = self.findChild(QtWidgets.QWidget,        "toolbar")
        self.menu            = self.findChild(QtWidgets.QWidget,        "menu")
        self.frozen_bot      = self.findChild(QtWidgets.QWidget,        "frozenplots_bottom")
        self.settingsbar     = self.findChild(QtWidgets.QWidget,        "settingsbar")
        self.blank           = self.findChild(QtWidgets.QWidget,        "blank")
        self.settingsfork    = self.findChild(QtWidgets.QWidget,        "settingsforkbar")
        self.alarmsbar       = self.findChild(QtWidgets.QWidget,        "alarmsbar")

        '''
        Get the stackable bits on the right
        '''
        self.rightbar       = self.main.findChild(QtWidgets.QStackedWidget, "rightbar")
        self.monitors_bar   = self.main.findChild(QtWidgets.QWidget,        "monitors_bar")
        self.frozen_right   = self.main.findChild(QtWidgets.QWidget,        "frozenplots_right")
        self.monitor_filler = self.main.findChild(QtWidgets.QWidget,        "monitor_filler")
        self.set_colors()

        '''
        Get initial and startup buttons
        '''
        self.button_new_patient    = self.initial.findChild(QtWidgets.QPushButton, "button_new_patient")
        self.button_resume_patient = self.initial.findChild(QtWidgets.QPushButton, "button_resume_patient")
        self.button_start_settings = self.startup.findChild(QtWidgets.QPushButton, "button_start_settings")
        self.button_start_vent     = self.startup.findChild(QtWidgets.QPushButton, "button_start_vent")
        self.button_start_test     = self.startup.findChild(QtWidgets.QPushButton, "button_start_test")

        '''
        Get toolbar widgets
        '''
        self.button_menu  = self.toolbar.findChild(QtWidgets.QPushButton, "button_menu")
        self.label_status = self.toolbar.findChild(QtWidgets.QLabel,      "label_status")

        toolsettings_names = {"toolsettings_1", "toolsettings_2", "toolsettings_3"}
        self.toolsettings = {};

        for name in toolsettings_names:
            toolsettings = self.toolbar.findChild(QtWidgets.QWidget, name)
            toolsettings.connect_config(config)
            self.toolsettings[name] = toolsettings

        '''
        Get menu widgets and connect settings for the menu widget
        '''
        self.button_back         = self.menu.findChild(QtWidgets.QPushButton, "button_back")
        self.button_settingsfork = self.menu.findChild(QtWidgets.QPushButton, "button_settingsfork")
        self.button_freeze       = self.menu.findChild(QtWidgets.QPushButton, "button_freeze")
        self.button_startstop    = self.menu.findChild(QtWidgets.QPushButton, "button_startstop")
        self.button_autoassist   = self.menu.findChild(QtWidgets.QPushButton, "button_autoassist")
        self.button_inspause     = self.menu.findChild(QtWidgets.QPushButton, "button_inspause")
        self.button_expause      = self.menu.findChild(QtWidgets.QPushButton, "button_expause")

        self.button_alarms       = self.settingsfork.findChild(QtWidgets.QPushButton, "button_alarms")
        self.button_settings     = self.settingsfork.findChild(QtWidgets.QPushButton, "button_settings")
        self.button_backsettings = self.settingsfork.findChild(QtWidgets.QPushButton, "button_backsettings")


        self.button_backalarms = self.alarmsbar.findChild(QtWidgets.QPushButton, "button_backalarms")
        self.button_applyalarm = self.alarmsbar.findChild(QtWidgets.QPushButton, "button_applyalarm")
        self.button_resetalarm = self.alarmsbar.findChild(QtWidgets.QPushButton, "button_resetalarm")
        self.button_topalarm   = self.alarmsbar.findChild(QtWidgets.QPushButton, "button_topalarm")
        self.button_midalarm   = self.alarmsbar.findChild(QtWidgets.QPushButton, "button_midalarm")
        self.button_botalarm   = self.alarmsbar.findChild(QtWidgets.QPushButton, "button_botalarm")

        '''
        Get frozen plots bottom bar widgets and connect
        '''
        self.button_unfreeze =   self.frozen_bot.findChild(QtWidgets.QPushButton, "button_unfreeze")

        '''
        Connect initial startup buttons
        '''
        self.button_resume_patient.pressed.connect(self.goto_resume_patient)
        self.button_new_patient.pressed.connect(self.goto_new_patient)
        self.button_start_vent.pressed.connect(self.goto_main)
        # TODO: connect to circuit test on ESP
        # self.button_start_test.pressed.connect()
        self.button_start_settings.pressed.connect(self.goto_settings)

        '''
        Connect back and menu buttons to toolbar and menu

        This effectively defines navigation from the bottombar.
        '''
        self.button_back.pressed.connect(self.show_toolbar)
        self.button_menu.pressed.connect(self.show_menu)
        self.button_freeze.pressed.connect(self.freeze_plots)
        self.button_unfreeze.pressed.connect(self.unfreeze_plots)
        self.button_alarms.pressed.connect(self.goto_alarms)
        self.button_settingsfork.pressed.connect(self.show_settingsfork)

        self.button_settings.pressed.connect(self.goto_settings)
        self.button_backsettings.pressed.connect(self.show_menu)

        self.button_backalarms.pressed.connect(self.exit_alarms)

        '''
        Instantiate the DataFiller, which takes
        care of filling plots data
        '''
        self.data_filler = DataFiller(config)

        '''
        Instantiate DataHandler, which will start a new
        thread to read data from the ESP32. We also connect
        the DataFiller to it, so the thread will pass the
        data directly to the DataFiller, which will
        then display them.
        '''
        self._data_h = DataHandler(config, self.esp32, self.data_filler)

        self.menu.connect_datahandler_config(self._data_h, self.config)



        '''
        Set up tool settings (bottom bar)

        self.toolsettings[..] are the objects that hold min, max values for a given setting as
        as the current value (displayed as a slider and as a number).
        '''
        toolsettings_names = {"toolsettings_1", "toolsettings_2", "toolsettings_3"}
        self.toolsettings = {};

        for name in toolsettings_names:
            toolsettings = self.toolbar.findChild(QtWidgets.QWidget, name)
            toolsettings.connect_config(config)
            self.toolsettings[name] = toolsettings

        '''
        Set up data monitor/alarms (side bar) and plots

        self.monitors[..] are the objects that hold monitor values and thresholds for alarm min
        and max. The current value and optional stats for the monitored value (mean, max) are set
        here.
        '''
        # plot slot widget names
        self.plots = {};
        for name in config['plots']:
            plot = self.main.findChild(QtWidgets.QWidget, name)
            plot.setFixedHeight(130)
            self.data_filler.connect_plot(name, plot)
            self.plots[name] = plot
        
        # The monitored fields from the default_settings.yaml config file
        self.monitors = {}
        for name in config['monitors']:
            monitor = Monitor(name, config)
            self.monitors[name] = monitor
            self.data_filler.connect_monitor(monitor)

        # The alarms are from the default_settings.yaml config file
        # self.alarms = {}
        # for name in config['alarms']:
        #     alarm = GuiAlarm(name, config, self.monitors, self.alarm_h)
        #     self.alarms[name] = alarm
        self.alarm_gui = GuiAlarms(config, self.esp32, self.monitors)


        # Get displayed monitors
        self.monitors_slots = self.main.findChild(QtWidgets.QVBoxLayout, "monitors_slots")
        self.alarms_settings.connect_monitors(self)
        self.alarms_settings.populate_monitors()
        self.button_applyalarm.pressed.connect(self.alarms_settings.apply_selected)
        self.button_resetalarm.pressed.connect(self.alarms_settings.reset_selected)
        '''
        TODO: functionality to add and remove monitors from monitor bar replaces this
        self.button_topalarm.pressed.connect(lambda slotname=slot_names[0]:
                self.alarms_settings.display_selected(slotname))
        self.button_midalarm.pressed.connect(lambda slotname=slot_names[1]:
                self.alarms_settings.display_selected(slotname))
        self.button_botalarm.pressed.connect(lambda slotname=slot_names[2]:
                self.alarms_settings.display_selected(slotname))
        '''

        # Connect the frozen plots
        # Requires building of an ordered array to associate the correct controls with the plot.
        active_plots = []
        for slotname in self.plots:
            active_plots.append(self.plots[slotname])
        self.frozen_bot.connect_workers(self.data_filler, active_plots)
        self.frozen_right.connect_workers(active_plots)
        '''
        Set up start/stop auto/min mode buttons.

        Connect each to their respective mode toggle functions.
        The StartStopWorker class takes care of starting and stopping a run
        '''

        self._start_stop_worker = StartStopWorker(
                self,
                self.config,
                self.esp32,
                self.button_startstop,
                self.button_autoassist,
                self.toolbar)

        self.button_startstop.released.connect(self._start_stop_worker.toggle_start_stop)
        self.button_autoassist.released.connect(self._start_stop_worker.toggle_mode)

        '''
        Connect settings button to Settings overlay.
        '''
        self.settings = Settings(self)
        self.toppane.insertWidget(self.toppane.count(), self.settings)

    def set_colors(self):
        # Monitors bar background
        palette = self.monitor_filler.palette()
        role = self.monitor_filler.backgroundRole()
        palette.setColor(role, QtGui.QColor(QtGui.QColor("#000000")))
        self.monitor_filler.setPalette(palette)

    def goto_new_patient(self):
        # TODO : implement start from default_settings
        self.show_startup()

    def goto_resume_patient(self):
        settings_file = SettingsFile(self.config["settings_file_path"])
        settings = settings_file.load()
        self.settings.update_config(settings)

        self.show_startup()

    def goto_settings(self):
        self.show_settings()
        self.show_settingsbar()

    def goto_main(self):
        self.show_main()
        self.show_toolbar()

    def exit_settings(self):
        self.show_main()
        self.show_menu()

    def goto_alarms(self):
        self.show_alarms()
        self.show_alarmsbar()
        self.alarms_settings.config_monitors()

    def exit_alarms(self):
        self.show_menu()
        self.show_plots()
        self.alarms_settings.deconfig_monitors()

    def show_settings(self):
        self.toppane.setCurrentWidget(self.settings)
        self.settings.tabWidget.setFocus()

    def show_startup(self):
        self.toppane.setCurrentWidget(self.startup)

    def show_menu(self):
        self.bottombar.setCurrentWidget(self.menu)

    def show_toolbar(self):
        self.bottombar.setCurrentWidget(self.toolbar)

    def show_settingsbar(self):
        self.bottombar.setCurrentWidget(self.settingsbar)

    def show_main(self):
        self.toppane.setCurrentWidget(self.main)

    def show_settingsfork(self):
        self.bottombar.setCurrentWidget(self.settingsfork)

    def show_alarms(self):
        self.centerpane.setCurrentWidget(self.alarms_settings)

    def show_plots(self):
        self.centerpane.setCurrentWidget(self.plots_all)

    def show_alarmsbar(self):
        self.bottombar.setCurrentWidget(self.alarmsbar)

    def freeze_plots(self):
        self.data_filler.freeze()
        self.rightbar.setCurrentWidget(self.frozen_right)
        self.bottombar.setCurrentWidget(self.frozen_bot)


    def unfreeze_plots(self):
        self.data_filler.unfreeze()
        self.rightbar.setCurrentWidget(self.monitors_bar)
        self.show_menu()

