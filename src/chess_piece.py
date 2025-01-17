import os
from enum import IntEnum

from PySide6.QtCore import Qt, QObject, QPoint, QPointF, QTimeLine
from PySide6.QtGui import QCursor, QPixmap
from PySide6.QtWidgets import QWidget, QGraphicsItem, QGraphicsPixmapItem, QGraphicsItemAnimation
from PySide6.QtGui import QAction, QImage, QPainter

class PieceType(IntEnum):
    WHITE = 0x00
    BLACK = 0x40

    KING   = 0x20
    QUEEN  = 0x10
    ROOK   = 0x08
    BISHOP = 0x04
    KNIGHT = 0x02
    PAWN   = 0x01
    EMPTY  = 0x00
    
    COLOR_MASK = 0x40
    PIECE_MASK = 0x3F

# Short-cut
    WHITE_KING   = WHITE | KING
    WHITE_QUEEN  = WHITE | QUEEN
    WHITE_ROOK   = WHITE | ROOK
    WHITE_BISHOP = WHITE | BISHOP
    WHITE_KNIGHT = WHITE | KNIGHT
    WHITE_PAWN   = WHITE | PAWN

    BLACK_KING   = BLACK | KING
    BLACK_QUEEN  = BLACK | QUEEN
    BLACK_ROOK   = BLACK | ROOK
    BLACK_BISHOP = BLACK | BISHOP
    BLACK_KNIGHT = BLACK | KNIGHT
    BLACK_PAWN   = BLACK | PAWN

class ChessPiece(QGraphicsPixmapItem):
    # Rank / File Converter
    rankDict = { 0 : '1', 1 : '2', 2 : '3', 3 : '4', 4 : '5', 5 : '6', 6 : '7', 7 : '8' }
    fileDict = { 0 : 'a', 1 : 'b', 2 : 'c', 3 : 'd', 4 : 'e', 5 : 'f', 6 : 'g', 7 : 'h' }

    def __init__(self, rank : int = -1, file : int = -1,
                       piecetype : PieceType = PieceType.EMPTY,
                       pixmap : QPixmap | None = None,
                       objname : str = '',
                       parent : QGraphicsItem | None = None):
        super().__init__(pixmap, parent)
        self.__rank = rank
        self.__file = file
        self.__piece_type = piecetype
        self.__object_name = objname
        self.__is_already_moved = False
        self.__update_pos()
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    # Characteristics setting methods
    def setObjectName(self, objname : str) -> None:
        self.__object_name = objname
    
    def setPieceType(self, piecetype : PieceType) -> None:
        self.__piece_type = piecetype

    def setSquare(self, rank : int, file : int) -> None:
        self.__rank = rank
        self.__file = file
        # self.__update_pos()
    
    def setMoved(self) -> None:
        self.__is_already_moved = True
    
    def unsetMoved(self) -> None:
        self.__is_already_moved = False
    
    # Characteristics access methods
    def ObjectName(self) -> str:
        return self.__object_name
    
    def Square(self) -> tuple[int, int]:
        return (self.__rank, self.__file)
    
    def PieceColor(self) -> PieceType:
        return self.__piece_type & PieceType.COLOR_MASK
    
    def PieceKind(self) -> PieceType:
        return self.__piece_type & PieceType.PIECE_MASK
    
    def PieceType(self) -> PieceType:
        return self.__piece_type
    
    def isAlreadyMoved(self) -> bool:
        return self.__is_already_moved

    @staticmethod
    def getPieceColor(piecetype : PieceType) -> PieceType:
        return (piecetype & PieceType.COLOR_MASK)
    
    @staticmethod
    def getPieceKind(piecetype : PieceType) -> PieceType:
        return (piecetype & PieceType.PIECE_MASK)
    
    @staticmethod
    def isWhitePiece(piecetype : PieceType) -> bool:
        return (piecetype != PieceType.EMPTY) \
           and (piecetype & PieceType.COLOR_MASK == PieceType.WHITE)
    
    @staticmethod
    def isBlackPiece(piecetype : PieceType) -> bool:
        return (piecetype != PieceType.EMPTY) \
           and (piecetype & PieceType.COLOR_MASK == PieceType.BLACK)
    
    @staticmethod
    def isEmpty(piecetype : PieceType) -> bool:
        return (piecetype == PieceType.EMPTY)

    @staticmethod
    def isOpponentPiece(piecetype : PieceType, turn : PieceType) -> bool:
        if turn == PieceType.WHITE:
            return ChessPiece.isBlackPiece(piecetype)
        else:
            return ChessPiece.isWhitePiece(piecetype)
    
    @staticmethod
    def getPosFromSquare(rank : int, file : int) -> tuple[float, float]:
        # if board is not reversed:
        return file * 100.0, (7 - rank) * 100.0

    def __update_pos(self) -> None:
        self.setPos(QPoint(self.__file * 100, (7 - self.__rank) * 100))
    

