import os

from PySide6.QtCore import Qt, QObject
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QGraphicsItemGroup, QGraphicsPixmapItem

from image import ChessImage
from .chess_piece import PieceType

class PromotionItem(QGraphicsItemGroup):
    VERTICAL   = 0
    HORIZONTAL = 1

    def __init__(self, orientation : int,
                       color : PieceType,
                       resource : ChessImage,
                       parent : QObject | None = None):
        super().__init__(parent)

        self.item_background = QGraphicsPixmapItem(self)
        self.orient = orientation
        if orientation == PromotionItem.VERTICAL:
            self.item_background.setPixmap(resource.promotion_bg_ver)
        elif orientation == PromotionItem.HORIZONTAL:
            self.item_background.setPixmap(resource.promotion_bg_hor)
        else:
            # Invalid orientation
            print('PromotionItem.__init__() :')
            print('Error : Invalid argument for \'orientation\'')
            exit()
        
        # Set some properties
        self.setVisible(False) # Deactivate
        self.setPos(300, 0)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        # Generate item for choosing piece to promote
        self.item_choice_queen  = QGraphicsPixmapItem(self)
        self.item_choice_rook   = QGraphicsPixmapItem(self)
        self.item_choice_bishop = QGraphicsPixmapItem(self)
        self.item_choice_knight = QGraphicsPixmapItem(self)

        # Set color
        self.color = color
        if self.color == PieceType.WHITE:
            self.item_choice_queen .setPixmap(resource.white_queen)
            self.item_choice_rook  .setPixmap(resource.white_rook)
            self.item_choice_bishop.setPixmap(resource.white_bishop)
            self.item_choice_knight.setPixmap(resource.white_knight)
        elif self.color == PieceType.BLACK:
            self.item_choice_queen .setPixmap(resource.black_queen)
            self.item_choice_rook  .setPixmap(resource.black_rook)
            self.item_choice_bishop.setPixmap(resource.black_bishop)
            self.item_choice_knight.setPixmap(resource.black_knight)
        else:
            # Invalid color
            print('PromotionItem.__init__() :')
            print('Error : Invalid argument for \'color\'')
            exit()
        
        # Place each piece in proper position
        if orientation == PromotionItem.VERTICAL:
            self.item_choice_queen .setPos(0, 0)
            self.item_choice_rook  .setPos(0, 100)
            self.item_choice_bishop.setPos(0, 200)
            self.item_choice_knight.setPos(0, 300)
        elif orientation == PromotionItem.HORIZONTAL:
            self.item_choice_queen .setPos(0, 0)
            self.item_choice_rook  .setPos(100, 0)
            self.item_choice_bishop.setPos(200, 0)
            self.item_choice_knight.setPos(300, 0)

        # Set Z-value
        self.item_background.setZValue(1)
        self.item_choice_queen.setZValue(2)
        self.item_choice_rook.setZValue(2)
        self.item_choice_bishop.setZValue(2)
        self.item_choice_knight.setZValue(2)
    
    