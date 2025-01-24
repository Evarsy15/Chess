import os
from enum import StrEnum
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QImage, QPixmap

class BoardTheme(StrEnum):
    BASIC = 'basic'
    # probably be updated

class PieceTheme(StrEnum):
    BASIC = 'basic'
    # probably not be updated much...

class ChessImage(QObject):
    # Path for root of resource files
    resource_root = os.path.dirname(__file__)

    # Signals
    boardImageUpdated = Signal()
    pieceImageUpdated = Signal()

    def __init__(self, board_theme : BoardTheme = BoardTheme.BASIC, 
                       piece_theme : PieceTheme = PieceTheme.BASIC):
        self.board_theme = board_theme
        self.piece_theme = piece_theme
        self.__load_resource()
    
    def setBoardTheme(self, board_theme : BoardTheme):
        self.board_theme = board_theme
        self.__load_board_image()
        self.boardImageUpdated.emit()
    
    def setPieceTheme(self, piece_theme : PieceTheme):
        self.piece_theme = piece_theme
        self.__load_piece_image()
        self.pieceImageUpdated.emit()

    def __load_resource(self):
        self.__load_board_image()
        self.__load_piece_image()
        self.__load_misc()
    
    def __load_board_image(self):
        __board_img_path = os.path.join(
            ChessImage.resource_root,
            'board',
            self.board_theme,
            'chess-board.jpg'
        )
        self.chess_board = QPixmap(__board_img_path)
        
    def __load_piece_image(self):
        __piece_img_dir = os.path.join(
            ChessImage.resource_root,
            'piece',
            self.piece_theme
        )

        self.white_king   = QPixmap(os.path.join(__piece_img_dir, 'white-king.png'))
        self.white_queen  = QPixmap(os.path.join(__piece_img_dir, 'white-queen.png'))
        self.white_rook   = QPixmap(os.path.join(__piece_img_dir, 'white-rook.png'))
        self.white_bishop = QPixmap(os.path.join(__piece_img_dir, 'white-bishop.png'))
        self.white_knight = QPixmap(os.path.join(__piece_img_dir, 'white-knight.png'))
        self.white_pawn   = QPixmap(os.path.join(__piece_img_dir, 'white-pawn.png'))

        self.black_king   = QPixmap(os.path.join(__piece_img_dir, 'black-king.png'))
        self.black_queen  = QPixmap(os.path.join(__piece_img_dir, 'black-queen.png'))
        self.black_rook   = QPixmap(os.path.join(__piece_img_dir, 'black-rook.png'))
        self.black_bishop = QPixmap(os.path.join(__piece_img_dir, 'black-bishop.png'))
        self.black_knight = QPixmap(os.path.join(__piece_img_dir, 'black-knight.png'))
        self.black_pawn   = QPixmap(os.path.join(__piece_img_dir, 'black-pawn.png'))
    
    def __load_misc(self):
        __misc_img_dir = os.path.join(
            ChessImage.resource_root,
            'misc'
        )

        self.highlight_dot    = QPixmap(os.path.join(__misc_img_dir, 'highlight-dot.png'))
        self.highlight_circle = QPixmap(os.path.join(__misc_img_dir, 'highlight-circle.png'))
        self.promotion_bg_ver = QPixmap(os.path.join(__misc_img_dir, 'promotion-vertical.png'))
        self.promotion_bg_hor = QPixmap(os.path.join(__misc_img_dir, 'promotion-horizontal.png'))
        self.reverse_board    = QPixmap(os.path.join(__misc_img_dir, 'reverse-board.png'))