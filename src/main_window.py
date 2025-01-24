from PySide6.QtCore import Qt, QRect, Slot
from PySide6.QtGui import QCursor, QAction
from PySide6.QtWidgets import (QWidget, QMainWindow,
    QMenuBar, QMenu, QStatusBar,
    QPushButton, QMessageBox,
    QSizePolicy)

from image import ChessImage
from .chess_board import ChessBoard, ReverseBoardButton
from .chess_piece import PieceType
from .chess_clock import ChessClock

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.__load_resource()
        self.__setup_ui()
        self.__connect_signal_and_slot()
    
    def __setup_ui(self):
        self.__init_main_window()
        self.__init_menu_bar()
        self.__init_status_bar()
        self.__init_widgets()
    
    def __init_main_window(self):
        # Basic properties of main window
        self.setObjectName("main_window")
        self.setWindowTitle("Chess")
        self.setFixedSize(1200, 900)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    
        # Central-widget
        self.__central_widget = QWidget(self)
        self.__central_widget.setObjectName("central_widget")
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
        self.__action_new_1min = QAction(self)
        self.__action_new_1min.setObjectName("new_game_1_minutes")
        self.__action_new_1min.setText("1 Minutes")
        self.__action_new_1min.triggered.connect(self.__new_game)

        self.__action_new_3min = QAction(self)
        self.__action_new_3min.setObjectName("new_game_3_minutes")
        self.__action_new_3min.setText("3 Minutes")
        self.__action_new_3min.triggered.connect(self.__new_game)

        self.__action_new_5min = QAction(self)
        self.__action_new_5min.setObjectName("new_game_5_minutes")
        self.__action_new_5min.setText("5 Minutes")
        self.__action_new_5min.triggered.connect(self.__new_game)
        
        self.__action_new_10min = QAction(self)
        self.__action_new_10min.setObjectName("new_game_10_minutes")
        self.__action_new_10min.setText("10 Minutes")
        self.__action_new_10min.triggered.connect(self.__new_game)

        self.__action_new_30min = QAction(self)
        self.__action_new_30min.setObjectName("new_game_30_minutes")
        self.__action_new_30min.setText("30 Minutes")
        self.__action_new_30min.triggered.connect(self.__new_game)

        self.__action_new_60min = QAction(self)
        self.__action_new_60min.setObjectName("new_game_60_minutes")
        self.__action_new_60min.setText("60 Minutes")
        self.__action_new_60min.triggered.connect(self.__new_game)

        self.__action_new_unlimit = QAction(self)
        self.__action_new_unlimit.setObjectName("new_game_unlimited")
        self.__action_new_unlimit.setText("Unlimited")
        self.__action_new_unlimit.triggered.connect(self.__new_game)

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

        self.__menu_new_game.addAction(self.__action_new_1min)
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
        self.white_clock = ChessClock(600, 0, self)
        self.black_clock = ChessClock(600, 0, self)
        
        self.white_clock.setObjectName("white_clock")
        self.white_clock.setGeometry(QRect(850, 800, 125, 50))
        
        self.black_clock.setObjectName("black_clock")
        self.black_clock.setGeometry(QRect(850, 50, 125, 50))

        # Resign & Tie Buttons
        self.start_button  = QPushButton("Start", self) 
        self.resign_button = QPushButton("Resign", self)
        self.tie_button    = QPushButton("Tie", self)

        self.start_button.setObjectName("start_button")
        self.start_button.setGeometry(QRect(850, 750, 75, 25))
        self.start_button.setVisible(False)

        self.resign_button.setObjectName("resign_button")
        self.resign_button.setGeometry(QRect(1000, 825, 75, 25))

        self.tie_button.setObjectName("tie_button")
        self.tie_button.setGeometry(QRect(1100, 825, 75, 25))

        # Reverse Board Buttons
        self.reverse_board_button = ReverseBoardButton(self.__resource, self)
        self.reverse_board_button.setGeometry(QRect(850, 125, 25, 25))
        self.reverse_board_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.__reversed = False

        # Pop-up window
        self.pop_up_window = QMessageBox()
        self.pop_up_window.setIcon(QMessageBox.Icon.Information)
        self.pop_up_window.setStandardButtons(QMessageBox.StandardButton.Ok)

    def __connect_signal_and_slot(self):
        self.chess_board.turnChanged.connect(self.__turn_change_handler)
        self.chess_board.gameOverWin.connect(self.__game_over_win_handler)
        self.chess_board.gameOverTie.connect(self.__game_over_tie_handler)

        self.white_clock.timeOut.connect(self.__timeout_handler)
        self.black_clock.timeOut.connect(self.__timeout_handler)

        self.start_button.pressed.connect(self.__start_game)
        self.resign_button.pressed.connect(self.__resign_handler)
        self.tie_button.pressed.connect(self.__tie_handler)
        self.reverse_board_button.buttonPressed.connect(self.__reverse_board_handler)

    def __load_resource(self):
        self.__resource = ChessImage()
    
    @Slot()
    def __new_game(self):
        # Reset chess board
        self.__turn = PieceType.WHITE
        self.__reversed = False
        self.chess_board.resetChessBoard()

        match self.sender():
            case self.__action_new_1min:
                __time_limit = 1 * 60
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
            self.white_clock.setUnlimited()
            self.black_clock.setUnlimited()
        
        self.start_button.setVisible(True)

    def __loadChessRecord(self):
        # Unimplemented
        pass
    
    def __start_game(self):
        # Unfreeze chess board
        self.chess_board.unfreezeChessBoard()

        # Launch chess clock
        self.__turn = PieceType.WHITE
        self.white_clock.startClock()

        # Deactivate start button
        self.start_button.setVisible(False)
    
    def __reset_game(self):
        # Reset chess board
        self.__turn == PieceType.WHITE
        self.chess_board.freezeChessBoard()
        self.chess_board.resetChessBoard()

        # Reset chess clocks
        self.white_clock.resetClock()
        self.black_clock.resetClock()

        # Activate start button
        self.start_button.setVisible(True)

    def __resign_handler(self):
        # Freeze chess board
        self.chess_board.freezeChessBoard()

        # Pause chess clocks
        self.white_clock.pauseClock()
        self.black_clock.pauseClock()

        # Check who's win and setup pop-up window
        _str_resign = 'White' if self.__turn == PieceType.WHITE else 'Black'
        _str_winner = 'White' if self.__turn == PieceType.BLACK else 'Black'

        # Show Pop-up window
        self.__show_pop_up_window(f'Resign by {_str_resign}', f'{_str_winner} won by Resignation')
        
        # Reset game
        self.__reset_game()

    def __tie_handler(self):
        # Freeze chess board
        self.chess_board.freezeChessBoard()

        # Pause chess clocks
        self.white_clock.pauseClock()
        self.black_clock.pauseClock()

        # Show Pop-up window
        self.__show_pop_up_window('Tie', 'Draw by agreement')

        # Reset game
        self.__reset_game()

    @Slot()
    def __turn_change_handler(self):
        # Change player turn
        self.__turn = PieceType.BLACK if self.__turn == PieceType.WHITE else PieceType.WHITE

        # Handle clock
        if self.__turn == PieceType.WHITE:
            self.black_clock.pauseClock()
            self.white_clock.resumeClock()
        else:
            self.white_clock.pauseClock()
            self.black_clock.resumeClock()

    def __reverse_board_handler(self):
        self.__reversed = not self.__reversed

        _upper_clock_rect = QRect(850, 50, 125, 50)
        _lower_clock_rect = QRect(850, 800, 125, 50)

        if self.__reversed == False:
            self.white_clock.setGeometry(_lower_clock_rect)
            self.black_clock.setGeometry(_upper_clock_rect)
        else:
            self.white_clock.setGeometry(_upper_clock_rect)
            self.black_clock.setGeometry(_lower_clock_rect)

        # Change place of all active pieces in chess board
        self.chess_board.reverseChessBoard()
    
    def __game_over_win_handler(self, winner : PieceType):
        # Freeze chess board
        self.chess_board.freezeChessBoard()

        # Pause chess clock
        self.white_clock.pauseClock()
        self.black_clock.pauseClock()

        # Check who's win by checkmate
        # White win by checkmate
        if winner == PieceType.WHITE:
            _str_winner = 'White'
            _str_loser  = 'Black'
        # Black win by checkmate
        elif winner == PieceType.BLACK:
            _str_winner = 'Black'
            _str_loser  = 'White'
        # Invalid case
        else:
            print(f'MainWindow.__game_over_win_handler() : ')
            print(f'Error : Invalid winner: {winner}')
            exit()
        
        # Show Pop-up window
        self.__show_pop_up_window('Checkmate', f'{_str_winner} won by Checkmate')
        
        # Reset game
        self.__reset_game()

    def __game_over_tie_handler(self):
        # Freeze chess board
        self.chess_board.freezeChessBoard()

        self.white_clock.pauseClock()
        self.black_clock.pauseClock()

        # Analyze Draw situation
        # ※ It is unimplemented for now since there is only way to reach here by stalemate.

        # Show Pop-up window
        self.__show_pop_up_window('Stalemate', 'Draw by Stalemate')

        # Reset game
        self.__reset_game()

    def __timeout_handler(self):
        # Freeze chess board
        self.chess_board.freezeChessBoard()

        self.white_clock.pauseClock()
        self.black_clock.pauseClock()

        # Check who's time limit is over
        _clock = self.sender()
        print(_clock)

        # White lose by time
        if _clock == self.white_clock:
            _str_loser  = 'White'
            _str_winner = 'Black'
        # Black lose by time
        elif _clock == self.black_clock:
            _str_loser  = 'Black'
            _str_winner = 'White'
        # Invalid case
        else:
            print(f'MainWindow.__timeout_handler() : ')
            print(f'Error : Invalid sender: {self.sender()}')
            exit()
        
        # Setup pop-up window
        self.__show_pop_up_window(f'Timeout', f'{_str_winner} won by time')
        
        # Reset game
        self.__reset_game()
    
    def __show_pop_up_window(self, title : str, text : str):
        self.pop_up_window.setWindowTitle(title)
        self.pop_up_window.setText(text)
        self.pop_up_window.exec()