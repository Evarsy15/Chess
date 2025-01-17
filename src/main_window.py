import os
from PySide6.QtCore import QPoint, QPointF, QRect
from PySide6.QtWidgets import (QWidget, QMainWindow, QGridLayout, 
    QMenuBar, QMenu, QStatusBar,
    QGraphicsScene, QGraphicsView,
    QPushButton,
    QSizePolicy)                        
from PySide6.QtGui import QAction, QImage, QPainter

from image import ChessImage
from .chess_board import ChessBoard
from .chess_piece import ChessPiece
from .chess_clock import ChessClock

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.__load_resource()
        self.__setup_ui()
    
    def __setup_ui(self):
        self.__init_main_window()
        self.__init_menu_bar()
        self.__init_status_bar()
        self.__init_widgets()
    
    def __init_main_window(self):
    # Basic information
        self.setObjectName("main_window")
        self.setWindowTitle("Chess")
        self.setFixedSize(1200, 900)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    
    # Set central-widget
        self.__central_widget = QWidget(self)
        self.__central_widget.setObjectName("central_widget")

        self.__grid_layout_widget = QWidget(self.__central_widget)
        self.__grid_layout_widget.setObjectName("grid_layout_widget")
        self.__grid_layout_widget.setGeometry(QRect(25, 25, 800, 800))

        self.__grid_layout = QGridLayout(self.__grid_layout_widget)
        self.__grid_layout.setObjectName("grid_layout")
        self.__grid_layout.setContentsMargins(0, 0, 0, 0)

        self.setCentralWidget(self.__central_widget)
        
    def __init_menu_bar(self):
    # Menubar
        self.__menubar = QMenuBar(self)
        self.__menubar.setObjectName("menu_bar")
        self.__menubar.setGeometry(QRect(0, 0, 1200, 25))
        self.__menubar.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setMenuBar(self.__menubar)
    
    # Menus
        self.__menu_menu = QMenu(self.__menubar)
        self.__menu_menu.setObjectName("menu")
        self.__menu_menu.setTitle("Menu")

        self.__menu_new_game = QMenu(self.__menu_menu)
        self.__menu_new_game.setObjectName("new_game")
        self.__menu_new_game.setTitle("New Game")

    # Actions
        self.__action_new_3min = QAction(self)
        self.__action_new_3min.setObjectName("new_game_3_minutes")
        self.__action_new_3min.setText("3 Minutes")
        self.__action_new_3min.triggered.connect(self.__initTimer)

        self.__action_new_5min = QAction(self)
        self.__action_new_5min.setObjectName("new_game_5_minutes")
        self.__action_new_5min.setText("5 Minutes")
        self.__action_new_5min.triggered.connect(self.__initTimer)
        
        self.__action_new_10min = QAction(self)
        self.__action_new_10min.setObjectName("new_game_10_minutes")
        self.__action_new_10min.setText("10 Minutes")
        self.__action_new_10min.triggered.connect(self.__initTimer)

        self.__action_new_30min = QAction(self)
        self.__action_new_30min.setText("30 Minutes")
        self.__action_new_30min.setObjectName("new_game_30_minutes")
        self.__action_new_30min.triggered.connect(self.__initTimer)

        self.__action_new_60min = QAction(self)
        self.__action_new_60min.setObjectName("new_game_60_minutes")
        self.__action_new_60min.setText("60 Minutes")
        self.__action_new_60min.triggered.connect(self.__initTimer)

        self.__action_new_unlimit = QAction(self)
        self.__action_new_unlimit.setObjectName("new_game_unlimited")
        self.__action_new_unlimit.setText("Unlimited")

        self.__action_load = QAction(self)
        self.__action_load.setObjectName("load")
        self.__action_load.setText("Load")
        self.__action_load.triggered.connect(self.__loadChessRecord)

        self.__action_exit = QAction(self)
        self.__action_exit.setObjectName("exit")
        self.__action_exit.setText("Exit")
        self.__action_exit.triggered.connect(self.close)

        # Add actions into menu
        self.__menubar.addAction(self.__menu_menu.menuAction())

        self.__menu_menu.addAction(self.__menu_new_game.menuAction())
        self.__menu_menu.addSeparator()
        self.__menu_menu.addAction(self.__action_load)
        self.__menu_menu.addSeparator()
        self.__menu_menu.addAction(self.__action_exit)

        self.__menu_new_game.addAction(self.__action_new_3min)
        self.__menu_new_game.addAction(self.__action_new_5min)
        self.__menu_new_game.addSeparator()
        self.__menu_new_game.addAction(self.__action_new_10min)
        self.__menu_new_game.addAction(self.__action_new_30min)
        self.__menu_new_game.addAction(self.__action_new_60min)
        self.__menu_new_game.addSeparator()
        self.__menu_new_game.addAction(self.__action_new_unlimit)

    def __init_status_bar(self):
        self.__status_bar = QStatusBar(self)
        self.__status_bar.setObjectName("status_bar")
        self.__status_bar.setGeometry(QRect(0, 875, 1200, 25))
        self.setStatusBar(self.__status_bar)
    
    def __init_widgets(self):
        # Chess Board & Pieces
        self.chess_board = ChessBoard(self.__resource, self)
        self.chess_board.setGeometry(QRect(24, 49, 802, 802))
        self.chess_board.show()

        # Chess Clocks
        self.white_clock = ChessClock("white_clock", self)
        self.black_clock = ChessClock("black_clock", self)
        self.resign_button = QPushButton("Resign", self)
        self.tie_button    = QPushButton("Tie", self)

        self.white_clock.setGeometry(QRect(850, 800, 125, 50))
        self.white_clock.setTimer(0)

        self.black_clock.setGeometry(QRect(850, 50, 125, 50))
        self.black_clock.setTimer(30)

        self.resign_button.setObjectName("resign_button")
        self.resign_button.setGeometry(QRect(1000, 825, 75, 25))
        self.tie_button.setGeometry(QRect(1100, 825, 75, 25))

    def __load_resource(self):
        self.__resource = ChessImage()

    def __initTimer(self):
        __time_limit = 0

        match self.sender():
            case self.__action_new_3min:
                __time_limit = 3 * 60
            case self.__action_new_5min:
                __time_limit = 5 * 60
            case self.__action_new_10min:
                __time_limit = 10 * 60
            case self.__action_new_30min:
                __time_limit = 30 * 60
            case self.__action_new_60min:
                __time_limit = 60 * 60
        
        if self.sender() != self.__action_new_unlimit:
            self.white_clock.setTimer(__time_limit)
            self.black_clock.setTimer(__time_limit)
        else:
            pass

    def __loadChessRecord(self):
        # Unimplemented
        pass
    
    def __reverseBoard(self):
        # Unimplemented
        pass