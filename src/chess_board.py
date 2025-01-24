import os, math, time
from enum import IntEnum
from copy import deepcopy
from PySide6.QtCore import (Qt, QObject, QPoint, QPointF, QRect, QRectF, QTimeLine, Signal)
from PySide6.QtGui import QPixmap, QPainter, QTransform
from PySide6.QtWidgets import (QGraphicsScene, QGraphicsView, QGraphicsPixmapItem, QGraphicsItemAnimation, QLabel)

from image import ChessImage
from .chess_piece import ChessPiece, PieceType, MoveType, PieceMove
from .promotion import PromotionItem

class MoveDir(IntEnum):
    UP        = 0
    DOWN      = 1
    LEFT      = 2
    RIGHT     = 3
    LEFTUP    = 4
    RIGHTUP   = 5
    LEFTDOWN  = 6
    RIGHTDOWN = 7
    KNIGHT    = 8

class ReverseBoardButton(QLabel):
    def __init__(self, resource : ChessImage,
                       parent : QObject | None):
        super().__init__(parent)
        self.setPixmap(resource.reverse_board)
    
    buttonPressed = Signal()

    def mousePressEvent(self, event):
        self.buttonPressed.emit()

class ChessBoardScene(QGraphicsScene):
    def __init__(self, resource : ChessImage,
                       parent : QObject | None = None):
        super().__init__(parent)
        self.resource = resource
        self.item_chess_board = self.addPixmap(self.resource.chess_board)
        self.item_chess_board.setZValue(-1)
    
class ChessBoardView(QGraphicsView):
    def __init__(self, scene : QGraphicsScene | None = None,
                       parent : QObject | None = None):
        super().__init__(scene, parent)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    
    boardClicked = Signal(QPoint)
    pieceClicked = Signal(ChessPiece)
    promotionItemClicked = Signal(PromotionItem, QPoint)

    def mousePressEvent(self, event):
        __pos  = event.pos()
        __item = self.itemAt(__pos)

        # Determine which item is clicked: piece or board.
        if isinstance(__item, ChessPiece):
            self.pieceClicked.emit(__item)
        elif isinstance(__item.parentItem(), PromotionItem):
            self.promotionItemClicked.emit(__item.parentItem(), __pos)
        else:
            self.boardClicked.emit(__pos)

class ChessBoard(QObject):
    def __init__(self, resource : ChessImage,
                       parent : QObject | None = None):
        
        super().__init__(parent)
        self.debug_mode = True

        self.resource = resource
        self.board_scene = ChessBoardScene(resource, parent)
        self.board_view  = ChessBoardView(self.board_scene, parent)

        self.animation = QGraphicsItemAnimation(self)
        self.timeline = QTimeLine(100)
        self.timeline.setUpdateInterval(1)
        self.animation.setTimeLine(self.timeline)

        self.__init_chess_piece()
        self.__init_chess_board()
        self.__init_promotion_item()

        self.__connect_signal_and_slot()
    
    def setGeometry(self, rect : QRect | QRectF):
        self.board_view.setGeometry(rect)
    
    def show(self):
        self.board_view.show()

    turnChanged = Signal()
    gameOverWin = Signal(PieceType)
    gameOverTie = Signal()
    
    # Chess-board event handler
    def boardClickHandler(self, pos : QPoint) -> None:
        if self.debug_mode == True:
            print(f'ChessBoard.boardClickHandler() : ')
            print(f' - pos : ({pos.x()}, {pos.y()})')
        
        # Ignore input when promotion item is opened
        if self.__promotion_mode == True:
            return

        # When there is a piece in focus
        if self.__is_in_focus == True:
            # Get rank/file coordinate for clicked square
            _new_rank, _new_file = ChessBoard.__get_square_from_pos(pos, self.__reversed)
            if self.debug_mode == True:
                if (_new_rank, _new_file) != (-1, -1):
                    print(f'{ChessPiece.fileDict[_new_file]}{ChessPiece.rankDict[_new_rank]} square')
                else:
                    print(f'Boundary')
            
            # When a square is clicked for legal move : Process as the rule
            _selected_move = self.__find_available_move(_new_rank, _new_file)
            if _selected_move != None:
                # Process the corresponding move
                self.__process_move(_selected_move)
            
            # Otherwise : Mouse event for freeing focus : Do nothing
            else:
                pass

        # Free focus
        self.__free_focus()

    def pieceClickHandler(self, piece : ChessPiece) -> None:
        if self.debug_mode == True:
            _rank, _file = piece.Square()
            print(f'ChessBoard.pieceClickHandler() : ')
            print(f' - Clicked Piece : {piece.ObjectName()} at {ChessPiece.fileDict[_file]}{ChessPiece.rankDict[_rank]} square')

        # Ignore input when promotion item is opened
        if self.__promotion_mode == True:
            return

        # Check if any piece is in focus.
        # If so, check whether current piece is clicked for capturing or not.
        if self.__is_in_focus == True:
            if self.debug_mode == True:
                print(f" - Current focused piece : {self.__piece_in_focus.ObjectName()}")
            
            # Opponent piece : Check if piece is clicked for capturing
            if ChessPiece.isOpponentPiece(piece.PieceType(), self.__turn):
                # Get square information
                _new_rank, _new_file = piece.Square()

                # When a square is clicked for legal move : Process as the rule
                _selected_move = self.__find_available_move(_new_rank, _new_file)
                if _selected_move != None:
                    # Process the corresponding move on the board
                    self.__process_move(_selected_move)

                # Free focus
                self.__free_focus()
            
            # My piece : Change focus of piece
            else:
                self.__set_focus_on_piece(piece)
        
        # Otherwise, set a focus on clicked piece if it is of current turn.
        else:
            # Check whether the piece is of current turn.
            # If so, set focus on clicked piece.
            if ChessPiece.isMyPiece(piece.PieceType(), self.__turn):
                self.__set_focus_on_piece(piece)
            
            # Otherwise, ignore the mouse input.
            else:
                pass

    def promotionItemClickHandler(self, item : PromotionItem, pos : QPoint) -> None:
        if self.debug_mode == True:
            print(f'ChessBoard.promotionItemClickHandler()')
        
        _base_pos = item.pos().toPoint()
        _rel_pos  = pos - _base_pos

        _item_promoting_pawn = self.__move_history[-1].PieceToMove()
        _rank, _file = _item_promoting_pawn.Square()

        if item.orient == PromotionItem.VERTICAL:
            _n = math.floor(_rel_pos.y() / 100)

            match _n:
                # Queen
                case 0:
                    _item_promoting_pawn.Promote(PieceType.QUEEN)
                # Rook
                case 1:
                    _item_promoting_pawn.Promote(PieceType.ROOK)
                # Bishop
                case 2:
                    _item_promoting_pawn.Promote(PieceType.BISHOP)
                # Knight
                case 3:
                    _item_promoting_pawn.Promote(PieceType.KNIGHT)

        self.board_status[_rank][_file] = _item_promoting_pawn.PieceType()

        self.__promotion_mode = False
        item.setVisible(False)

        # Hand the turn and check if game is over
        self.__hand_player_turn()
        self.__check_game_over()

    def __init_chess_piece(self):
        self.item_white_king     = ChessPiece(0, 4, PieceType.WHITE_KING,   self.resource, 'white-king')
        self.item_white_queen    = ChessPiece(0, 3, PieceType.WHITE_QUEEN,  self.resource, 'white-queen')
        self.item_white_rook_a   = ChessPiece(0, 0, PieceType.WHITE_ROOK,   self.resource, 'white-rook-a')
        self.item_white_rook_h   = ChessPiece(0, 7, PieceType.WHITE_ROOK,   self.resource, 'white-rook-h')
        self.item_white_bishop_c = ChessPiece(0, 2, PieceType.WHITE_BISHOP, self.resource, 'white-bishop-c')
        self.item_white_bishop_f = ChessPiece(0, 5, PieceType.WHITE_BISHOP, self.resource, 'white-bishop-f')
        self.item_white_knight_b = ChessPiece(0, 1, PieceType.WHITE_KNIGHT, self.resource, 'white-knight-b')
        self.item_white_knight_g = ChessPiece(0, 6, PieceType.WHITE_KNIGHT, self.resource, 'white-knight-g')
        self.item_white_pawn_a   = ChessPiece(1, 0, PieceType.WHITE_PAWN,   self.resource, 'white-pawn-a')
        self.item_white_pawn_b   = ChessPiece(1, 1, PieceType.WHITE_PAWN,   self.resource, 'white-pawn-b')
        self.item_white_pawn_c   = ChessPiece(1, 2, PieceType.WHITE_PAWN,   self.resource, 'white-pawn-c')
        self.item_white_pawn_d   = ChessPiece(1, 3, PieceType.WHITE_PAWN,   self.resource, 'white-pawn-d')
        self.item_white_pawn_e   = ChessPiece(1, 4, PieceType.WHITE_PAWN,   self.resource, 'white-pawn-e')
        self.item_white_pawn_f   = ChessPiece(1, 5, PieceType.WHITE_PAWN,   self.resource, 'white-pawn-f')
        self.item_white_pawn_g   = ChessPiece(1, 6, PieceType.WHITE_PAWN,   self.resource, 'white-pawn-g')
        self.item_white_pawn_h   = ChessPiece(1, 7, PieceType.WHITE_PAWN,   self.resource, 'white-pawn-h')

        self.item_black_king     = ChessPiece(7, 4, PieceType.BLACK_KING,   self.resource, 'black-king')
        self.item_black_queen    = ChessPiece(7, 3, PieceType.BLACK_QUEEN,  self.resource, 'black-queen')
        self.item_black_rook_a   = ChessPiece(7, 0, PieceType.BLACK_ROOK,   self.resource, 'black-rook-a')
        self.item_black_rook_h   = ChessPiece(7, 7, PieceType.BLACK_ROOK,   self.resource, 'black-rook-h')
        self.item_black_bishop_c = ChessPiece(7, 2, PieceType.BLACK_BISHOP, self.resource, 'black-bishop-c')
        self.item_black_bishop_f = ChessPiece(7, 5, PieceType.BLACK_BISHOP, self.resource, 'black-bishop-f')
        self.item_black_knight_b = ChessPiece(7, 1, PieceType.BLACK_KNIGHT, self.resource, 'black-knight-b')
        self.item_black_knight_g = ChessPiece(7, 6, PieceType.BLACK_KNIGHT, self.resource, 'black-knight-g')
        self.item_black_pawn_a   = ChessPiece(6, 0, PieceType.BLACK_PAWN,   self.resource, 'black-pawn-a')
        self.item_black_pawn_b   = ChessPiece(6, 1, PieceType.BLACK_PAWN,   self.resource, 'black-pawn-b')
        self.item_black_pawn_c   = ChessPiece(6, 2, PieceType.BLACK_PAWN,   self.resource, 'black-pawn-c')
        self.item_black_pawn_d   = ChessPiece(6, 3, PieceType.BLACK_PAWN,   self.resource, 'black-pawn-d')
        self.item_black_pawn_e   = ChessPiece(6, 4, PieceType.BLACK_PAWN,   self.resource, 'black-pawn-e')
        self.item_black_pawn_f   = ChessPiece(6, 5, PieceType.BLACK_PAWN,   self.resource, 'black-pawn-f')
        self.item_black_pawn_g   = ChessPiece(6, 6, PieceType.BLACK_PAWN,   self.resource, 'black-pawn-g')
        self.item_black_pawn_h   = ChessPiece(6, 7, PieceType.BLACK_PAWN,   self.resource, 'black-pawn-h')

        self.board_scene.addItem(self.item_white_king);     self.board_scene.addItem(self.item_black_king)
        self.board_scene.addItem(self.item_white_queen);    self.board_scene.addItem(self.item_black_queen)
        self.board_scene.addItem(self.item_white_rook_a);   self.board_scene.addItem(self.item_black_rook_a)
        self.board_scene.addItem(self.item_white_rook_h);   self.board_scene.addItem(self.item_black_rook_h)
        self.board_scene.addItem(self.item_white_bishop_c); self.board_scene.addItem(self.item_black_bishop_c)
        self.board_scene.addItem(self.item_white_bishop_f); self.board_scene.addItem(self.item_black_bishop_f)
        self.board_scene.addItem(self.item_white_knight_b); self.board_scene.addItem(self.item_black_knight_b)
        self.board_scene.addItem(self.item_white_knight_g); self.board_scene.addItem(self.item_black_knight_g)
        self.board_scene.addItem(self.item_white_pawn_a);   self.board_scene.addItem(self.item_black_pawn_a)
        self.board_scene.addItem(self.item_white_pawn_b);   self.board_scene.addItem(self.item_black_pawn_b)
        self.board_scene.addItem(self.item_white_pawn_c);   self.board_scene.addItem(self.item_black_pawn_c)
        self.board_scene.addItem(self.item_white_pawn_d);   self.board_scene.addItem(self.item_black_pawn_d)
        self.board_scene.addItem(self.item_white_pawn_e);   self.board_scene.addItem(self.item_black_pawn_e)
        self.board_scene.addItem(self.item_white_pawn_f);   self.board_scene.addItem(self.item_black_pawn_f)
        self.board_scene.addItem(self.item_white_pawn_g);   self.board_scene.addItem(self.item_black_pawn_g)
        self.board_scene.addItem(self.item_white_pawn_h);   self.board_scene.addItem(self.item_black_pawn_h)

        self.active_white_piece = [
            self.item_white_king,     self.item_white_queen,    self.item_white_rook_a,   self.item_white_rook_h,
            self.item_white_bishop_c, self.item_white_bishop_f, self.item_white_knight_b, self.item_white_knight_g,
            self.item_white_pawn_a,   self.item_white_pawn_b,   self.item_white_pawn_c,   self.item_white_pawn_d,
            self.item_white_pawn_e,   self.item_white_pawn_f,   self.item_white_pawn_g,   self.item_white_pawn_h
        ]
        self.active_black_piece = [
            self.item_black_king,     self.item_black_queen,    self.item_black_rook_a,   self.item_black_rook_h,
            self.item_black_bishop_c, self.item_black_bishop_f, self.item_black_knight_b, self.item_black_knight_g,
            self.item_black_pawn_a,   self.item_black_pawn_b,   self.item_black_pawn_c,   self.item_black_pawn_d,
            self.item_black_pawn_e,   self.item_black_pawn_f,   self.item_black_pawn_g,   self.item_black_pawn_h
        ]
    
    def __init_chess_board(self):
        self.__turn = PieceType.WHITE      # Turn
        self.__is_in_focus = False         # Focus
        self.__piece_in_focus = None       # Piece in Focus
        self.__reversed = False
        self.__item_highlight : list[QGraphicsPixmapItem] = []
        self.__move_history : list[PieceMove] = [] # Sequence of piece moves
        self.__promotion_mode = False      # Promotion mode
        self.board_status = [
            [PieceType.WHITE_ROOK, PieceType.WHITE_KNIGHT, PieceType.WHITE_BISHOP, PieceType.WHITE_QUEEN, 
             PieceType.WHITE_KING, PieceType.WHITE_BISHOP, PieceType.WHITE_KNIGHT, PieceType.WHITE_ROOK],
            [PieceType.WHITE_PAWN, PieceType.WHITE_PAWN,   PieceType.WHITE_PAWN,   PieceType.WHITE_PAWN,
             PieceType.WHITE_PAWN, PieceType.WHITE_PAWN,   PieceType.WHITE_PAWN,   PieceType.WHITE_PAWN],
            [PieceType.EMPTY,      PieceType.EMPTY,        PieceType.EMPTY,        PieceType.EMPTY, 
             PieceType.EMPTY,      PieceType.EMPTY,        PieceType.EMPTY,        PieceType.EMPTY],
            [PieceType.EMPTY,      PieceType.EMPTY,        PieceType.EMPTY,        PieceType.EMPTY, 
             PieceType.EMPTY,      PieceType.EMPTY,        PieceType.EMPTY,        PieceType.EMPTY],
            [PieceType.EMPTY,      PieceType.EMPTY,        PieceType.EMPTY,        PieceType.EMPTY, 
             PieceType.EMPTY,      PieceType.EMPTY,        PieceType.EMPTY,        PieceType.EMPTY],
            [PieceType.EMPTY,      PieceType.EMPTY,        PieceType.EMPTY,        PieceType.EMPTY, 
             PieceType.EMPTY,      PieceType.EMPTY,        PieceType.EMPTY,        PieceType.EMPTY],
            [PieceType.BLACK_PAWN, PieceType.BLACK_PAWN,   PieceType.BLACK_PAWN,   PieceType.BLACK_PAWN,
             PieceType.BLACK_PAWN, PieceType.BLACK_PAWN,   PieceType.BLACK_PAWN,   PieceType.BLACK_PAWN],
            [PieceType.BLACK_ROOK, PieceType.BLACK_KNIGHT, PieceType.BLACK_BISHOP, PieceType.BLACK_QUEEN, 
             PieceType.BLACK_KING, PieceType.BLACK_BISHOP, PieceType.BLACK_KNIGHT, PieceType.BLACK_ROOK]
        ]

    def __init_promotion_item(self):
        self.item_promotion_white = PromotionItem(PromotionItem.VERTICAL, PieceType.WHITE, self.resource)
        self.item_promotion_black = PromotionItem(PromotionItem.VERTICAL, PieceType.BLACK, self.resource)
        
        self.board_scene.addItem(self.item_promotion_white)
        self.board_scene.addItem(self.item_promotion_black)

        # self.item_promotion_white.setVisible(True)

    def __connect_signal_and_slot(self):
        self.board_view.boardClicked.connect(self.boardClickHandler)
        self.board_view.pieceClicked.connect(self.pieceClickHandler)
        self.board_view.promotionItemClicked.connect(self.promotionItemClickHandler)
        self.timeline.finished.connect(self.__process_after_move)

    # Wrapper methods
    def resetChessBoard(self) -> None:
        self.__reset_chess_board()
    
    def reverseChessBoard(self) -> None:
        self.__reverse_chess_board()

    # Methods for game management

    @staticmethod
    def __apply_move_to_board_status(move : PieceMove, boardStatus : list[list[PieceType]]) -> None:
        match move.MoveType():
            # Basic move
            case MoveType.BASIC | MoveType.PROMOTION:
                _old_rank, _old_file = move.OldSquare()
                _new_rank, _new_file = move.NewSquare()
                
                boardStatus[_old_rank][_old_file] = PieceType.EMPTY
                boardStatus[_new_rank][_new_file] = move.PieceToMove().PieceType()
            
            # Castling
            case MoveType.CASTLING_K | MoveType.CASTLING_Q:
                _aux_square = move.AuxSquare()
                if _aux_square == None:
                    print(f'ChessBoard.__apply_move_to_board_status()')
                    print(f'Error : Castling move has NoneType auxiliary square')
                    exit()
                
                _king_old_rank, _king_old_file = move.OldSquare()
                _king_new_rank, _king_new_file = move.NewSquare()
                _rook_old_rank, _rook_old_file = _aux_square[0]
                _rook_new_rank, _rook_new_file = _aux_square[1]

                boardStatus[_king_old_rank][_king_old_file] = PieceType.EMPTY
                boardStatus[_king_new_rank][_king_new_file] = move.PieceToMove().PieceType()
                boardStatus[_rook_old_rank][_rook_old_file] = PieceType.EMPTY
                boardStatus[_rook_new_rank][_rook_new_file] = move.PieceAux().PieceType()
            
            # En passant
            case MoveType.EN_PASSANT:
                _aux_square = move.AuxSquare()
                if _aux_square == None:
                    print(f'ChessBoard.__apply_move_to_board_status()')
                    print(f'Error : En passant move has NoneType auxiliary square')
                    exit()
                
                _old_rank, _old_file = move.OldSquare()
                _new_rank, _new_file = move.NewSquare()
                _aux_rank, _aux_file = _aux_square[0]

                boardStatus[_old_rank][_old_file] = PieceType.EMPTY
                boardStatus[_new_rank][_new_file] = move.PieceToMove().PieceType()
                boardStatus[_aux_rank][_aux_file] = PieceType.EMPTY
        
        # ChessBoard.__print_board_status(boardStatus)

    def __check_game_over(self) -> None:
        _is_check = self.__is_check_state()
        _is_no_avail_move = self.__is_no_avail_move()

        # Checkmate -> Last turn wins
        if _is_check and _is_no_avail_move:
            # Winner's turn
            _winner : PieceType = self.__turn ^ PieceType.COLOR_MASK

            if self.debug_mode == True:
                _str_winner = 'White' if _winner == PieceType.WHITE else 'Black'
                print(f'Checkmate by {_str_winner}')
            
            self.gameOverWin.emit(_winner)
        # Stalemate -> Tie
        elif (not _is_check) and _is_no_avail_move:
            self.gameOverTie.emit()
        else:
            return

    @staticmethod
    def __check_king_safety(turn : PieceType, boardStatus : list[list[PieceType]]) -> bool:
        # Find the square of king
        _king_rank, _king_file = -1, -1
        for _rank in range(8):
            for _file in range(8):
                _piece_on_square = boardStatus[_rank][_file]
                if ChessPiece.getPieceColor(_piece_on_square) == turn and \
                   ChessPiece.getPieceKind(_piece_on_square) == PieceType.KING:
                    _king_rank, _king_file = _rank, _file
                    break
        
        # Sanity check : King's existence
        if (_king_rank, _king_file) == (-1, -1):
            print(f'ChessBoard.__check_king_safety()')
            print(f'Error : Inexistence of King')
            exit()
        
        # Check if there is an opponent piece that attacks our king
        _is_king_on_attack = False

        # 1. UP
        _rank, _file = _king_rank + 1, _king_file
        _dist = 1
        while _rank < 8:
            # Get square information
            _piece_on_path = boardStatus[_rank][_file]
            
            # Empty square : Keep going
            if ChessPiece.isEmpty(_piece_on_path):
                _rank += 1; _dist += 1
                continue

            # Blocked by ally piece : Break
            elif ChessPiece.isMyPiece(_piece_on_path, turn):
                break
            
            # First meet by opponent piece : Check if the piece can attack the king
            else:
                _attackable_piece = [PieceType.ROOK, PieceType.QUEEN]
                if _dist == 1: # King can attack
                    _attackable_piece.append(PieceType.KING)
                
                if ChessPiece.getPieceKind(_piece_on_path) in _attackable_piece:
                    _is_king_on_attack = True
                
                break
        
        # 2. DOWN
        _rank, _file = _king_rank - 1, _king_file
        _dist = 1
        while _rank >= 0:
            # Get square information
            _piece_on_path = boardStatus[_rank][_file]
            
            # Empty square : Keep going
            if ChessPiece.isEmpty(_piece_on_path):
                _rank -= 1; _dist += 1
                continue
            
            # Blocked by ally piece : Break
            elif ChessPiece.isMyPiece(_piece_on_path, turn):
                break
            
            # First meet by opponent piece : Check if the piece can attack the king
            else:
                _attackable_piece = [PieceType.ROOK, PieceType.QUEEN]
                if _dist == 1: # King can attack
                    _attackable_piece.append(PieceType.KING)
                
                if ChessPiece.getPieceKind(_piece_on_path) in _attackable_piece:
                    _is_king_on_attack = True
                
                break
        
        # 3. LEFT
        _rank, _file = _king_rank, _king_file - 1
        _dist = 1
        while _file >= 0:
            # Get square information
            _piece_on_path = boardStatus[_rank][_file]
            
            # Empty square : Keep going
            if ChessPiece.isEmpty(_piece_on_path):
                _file -= 1; _dist += 1
                continue
            
            # Blocked by ally piece : Break
            elif ChessPiece.isMyPiece(_piece_on_path, turn):
                break
            
            # First meet by opponent piece : Check if the piece can attack the king, then break
            else:
                _attackable_piece = [PieceType.ROOK, PieceType.QUEEN]
                if _dist == 1: # King can attack
                    _attackable_piece.append(PieceType.KING)
                
                if ChessPiece.getPieceKind(_piece_on_path) in _attackable_piece:
                    _is_king_on_attack = True
                
                break
        
        # 4. RIGHT
        _rank, _file = _king_rank, _king_file + 1
        _dist = 1
        while _file < 8:
            # Get square information
            _piece_on_path = boardStatus[_rank][_file]

            # Empty square : Keep going
            if ChessPiece.isEmpty(_piece_on_path):
                _file += 1; _dist += 1
                continue
            
            # Blocked by ally piece : Break
            elif ChessPiece.isMyPiece(_piece_on_path, turn):
                break
            
            # First meet by opponent piece : Check if the piece can attack the king
            else:
                _attackable_piece = [PieceType.ROOK, PieceType.QUEEN]
                if _dist == 1: # King can attack
                    _attackable_piece.append(PieceType.KING)
                
                if ChessPiece.getPieceKind(_piece_on_path) in _attackable_piece:
                    _is_king_on_attack = True
                
                break
        
        # 5. LEFT-UP
        _rank, _file = _king_rank + 1, _king_file - 1
        _dist = 1
        while _rank < 8 and _file >= 0:
            # Get square information
            _piece_on_path = boardStatus[_rank][_file]

            # Empty square : Keep going
            if ChessPiece.isEmpty(_piece_on_path):
                _rank += 1; _file -= 1; _dist += 1
                continue
            
            # Blocked by ally piece : Break
            elif ChessPiece.isMyPiece(_piece_on_path, turn):
                break
            
            # First piece meet is opponent piece : Check if the piece can attack the king
            else:
                _attackable_piece = [PieceType.BISHOP, PieceType.QUEEN]
                if _dist == 1: # King can attack
                    _attackable_piece.append(PieceType.KING)
                    if turn == PieceType.WHITE:
                        _attackable_piece.append(PieceType.PAWN)
                
                if ChessPiece.getPieceKind(_piece_on_path) in _attackable_piece:
                    _is_king_on_attack = True
                
                break
        
        # 6. RIGHT-UP
        _rank, _file = _king_rank + 1, _king_file + 1
        _dist = 1
        while _rank < 8 and _file < 8:
            # Get square information
            _piece_on_path = boardStatus[_rank][_file]

            # Empty square : Keep going
            if ChessPiece.isEmpty(_piece_on_path):
                _rank += 1; _file += 1; _dist += 1
                continue
            
            # Blocked by ally piece : Break
            elif ChessPiece.isMyPiece(_piece_on_path, turn):
                break
            
            # First piece meet is opponent piece : Check if the piece can attack the king
            else:
                _attackable_piece = [PieceType.BISHOP, PieceType.QUEEN]
                if _dist == 1: # King can attack
                    _attackable_piece.append(PieceType.KING)
                    if turn == PieceType.WHITE: # Pawn can attack
                        _attackable_piece.append(PieceType.PAWN)
                
                if ChessPiece.getPieceKind(_piece_on_path) in _attackable_piece:
                    _is_king_on_attack = True
                
                break
        
        # 7. LEFT-DOWN
        _rank, _file = _king_rank - 1, _king_file - 1
        _dist = 1
        while _rank >= 0 and _file >= 0:
            # Get square information
            _piece_on_path = boardStatus[_rank][_file]

            # Empty square : Keep going
            if ChessPiece.isEmpty(_piece_on_path):
                _rank -= 1; _file -= 1; _dist += 1
                continue
            
            # Blocked by ally piece : Break
            elif ChessPiece.isMyPiece(_piece_on_path, turn):
                break
            
            # First piece meet is opponent piece : Check if the piece can attack the king
            else:
                _attackable_piece = [PieceType.BISHOP, PieceType.QUEEN]
                if _dist == 1: # King can attack
                    _attackable_piece.append(PieceType.KING)
                    if turn == PieceType.BLACK: # Pawn can attack
                        _attackable_piece.append(PieceType.PAWN)
                
                if ChessPiece.getPieceKind(_piece_on_path) in _attackable_piece:
                    _is_king_on_attack = True
                
                break
        
        # 8. RIGHT-DOWN
        _rank, _file = _king_rank - 1, _king_file + 1
        _dist = 1
        while _rank >= 0 and _file < 8:
            # Get square information
            _piece_on_path = boardStatus[_rank][_file]

            # Empty square : Keep going
            if ChessPiece.isEmpty(_piece_on_path):
                _rank -= 1; _file += 1; _dist += 1
                continue
            
            # Blocked by ally piece : Break
            elif ChessPiece.isMyPiece(_piece_on_path, turn):
                break
            
            # First piece meet is opponent piece : Check if the piece can attack the king
            else:
                _attackable_piece = [PieceType.BISHOP, PieceType.QUEEN]
                if _dist == 1: # King can attack
                    _attackable_piece.append(PieceType.KING)
                    if turn == PieceType.BLACK: # Pawn can attack
                        _attackable_piece.append(PieceType.PAWN)
                
                if ChessPiece.getPieceKind(_piece_on_path) in _attackable_piece:
                    _is_king_on_attack = True
                
                break
        
        # 9. KNIGHT
        for leap in [(-2, 1), (-1, 2), (1, 2), (2, 1),
                     (2, -1), (1, -2), (-1, -2), (-2, -1)]:
            _rank = _king_rank + leap[0]
            _file = _king_file + leap[1]
                    
            # Check if square is valid
            if 0 <= _rank and _rank < 8 and 0 <= _file and _file < 8:
                # Get square information
                _piece_on_square = boardStatus[_rank][_file]
                
                # Check if the square is of opponent knight
                if ChessPiece.isOpponentPiece(_piece_on_square, turn) and \
                   ChessPiece.getPieceKind(_piece_on_square) == PieceType.KNIGHT:
                    _is_king_on_attack = True
        
        return (not _is_king_on_attack)

    def __free_focus(self) -> None:
        self.__is_in_focus = False
        self.__piece_in_focus = None
        self.__remove_highlight()

    def __find_available_move(self, rank : int, file : int) -> PieceMove | None:
        if self.__is_in_focus == False:
            return None
        
        # Fast detection of boundary input
        if (rank, file) == (-1, -1):
            return None
        
        # Check if there exists available move with given destination square
        for _move in self.avail_moves:
            if (rank, file) == _move.NewSquare():
                return _move
        
        return None

    def __get_available_moves(self, piece : ChessPiece) -> bool:
        _color = piece.PieceColor()
        _kind  = piece.PieceKind()
        _rank, _file = piece.Square()
        _is_already_moved = piece.isAlreadyMoved()

        _cand_sqr = []
        _avail_moves : list[PieceMove] = []

        # Basic moves (including promotion)
        match _kind:
            case PieceType.PAWN:
                # Pawn's movement
                _cand_sqr.extend(self.__get_squares_pawn(_color, _is_already_moved, _rank, _file))
            
            case PieceType.KNIGHT:
                # Knight's movement
                _cand_sqr.extend(self.__get_squares_on_path(MoveDir.KNIGHT,    _color, _rank, _file, 2))
            
            case PieceType.BISHOP:
                # Bishop's movement : Move any distance diagonally
                _cand_sqr.extend(self.__get_squares_on_path(MoveDir.LEFTUP,    _color, _rank, _file, 8))
                _cand_sqr.extend(self.__get_squares_on_path(MoveDir.RIGHTUP,   _color, _rank, _file, 8))
                _cand_sqr.extend(self.__get_squares_on_path(MoveDir.LEFTDOWN,  _color, _rank, _file, 8))
                _cand_sqr.extend(self.__get_squares_on_path(MoveDir.RIGHTDOWN, _color, _rank, _file, 8))
            
            case PieceType.ROOK:
                # Rook's movement : Move any distance linearly
                _cand_sqr.extend(self.__get_squares_on_path(MoveDir.UP,        _color, _rank, _file, 8))
                _cand_sqr.extend(self.__get_squares_on_path(MoveDir.DOWN,      _color, _rank, _file, 8))
                _cand_sqr.extend(self.__get_squares_on_path(MoveDir.LEFT,      _color, _rank, _file, 8))
                _cand_sqr.extend(self.__get_squares_on_path(MoveDir.RIGHT,     _color, _rank, _file, 8))
            
            case PieceType.QUEEN:
                # Queen's movement : Move any distance with any direction
                _cand_sqr.extend(self.__get_squares_on_path(MoveDir.UP,        _color, _rank, _file, 8))
                _cand_sqr.extend(self.__get_squares_on_path(MoveDir.DOWN,      _color, _rank, _file, 8))
                _cand_sqr.extend(self.__get_squares_on_path(MoveDir.LEFT,      _color, _rank, _file, 8))
                _cand_sqr.extend(self.__get_squares_on_path(MoveDir.RIGHT,     _color, _rank, _file, 8))
                _cand_sqr.extend(self.__get_squares_on_path(MoveDir.LEFTUP,    _color, _rank, _file, 8))
                _cand_sqr.extend(self.__get_squares_on_path(MoveDir.RIGHTUP,   _color, _rank, _file, 8))
                _cand_sqr.extend(self.__get_squares_on_path(MoveDir.LEFTDOWN,  _color, _rank, _file, 8))
                _cand_sqr.extend(self.__get_squares_on_path(MoveDir.RIGHTDOWN, _color, _rank, _file, 8))
            
            case PieceType.KING:
                # King's basic movement : Move one square with any direction
                _cand_sqr.extend(self.__get_squares_on_path(MoveDir.UP,        _color, _rank, _file, 1))
                _cand_sqr.extend(self.__get_squares_on_path(MoveDir.DOWN,      _color, _rank, _file, 1))
                _cand_sqr.extend(self.__get_squares_on_path(MoveDir.LEFT,      _color, _rank, _file, 1))
                _cand_sqr.extend(self.__get_squares_on_path(MoveDir.RIGHT,     _color, _rank, _file, 1))
                _cand_sqr.extend(self.__get_squares_on_path(MoveDir.LEFTUP,    _color, _rank, _file, 1))
                _cand_sqr.extend(self.__get_squares_on_path(MoveDir.RIGHTUP,   _color, _rank, _file, 1))
                _cand_sqr.extend(self.__get_squares_on_path(MoveDir.LEFTDOWN,  _color, _rank, _file, 1))
                _cand_sqr.extend(self.__get_squares_on_path(MoveDir.RIGHTDOWN, _color, _rank, _file, 1))

        # Distinguish legal moves
        for _cand_rank, _cand_file in _cand_sqr:
            # Check if the move is promotion move
            if _kind == PieceType.PAWN:
                if _color == PieceType.WHITE:
                    if _cand_rank == 7:
                        _is_promotion = True
                    else:
                        _is_promotion = False
                else:
                    if _cand_rank == 0:
                        _is_promotion = True
                    else:
                        _is_promotion = False
            else:
                _is_promotion = False
            
            # Generate Candidate Move
            _cand_move = PieceMove(
                piece, self.__get_item_from_square(_cand_rank, _cand_file), None, 
                MoveType.BASIC if _is_promotion == False else MoveType.PROMOTION,
                (_rank, _file), (_cand_rank, _cand_file), None
            )

            # Check if the candidate move is legal (in terms of king's safety)
            # If so, add the move into available move list
            if self.__is_legal_move(_cand_move):
                _avail_moves.append(_cand_move)
            else:
                del _cand_move
        
        # Handle special moves
        # Castling
        if _kind == PieceType.KING:
            # King-side
            if self.__is_castling_available(_color, MoveType.CASTLING_K):
                if self.debug_mode == True:
                    print("Kingside Castling Available")

                _rook = self.item_white_rook_h if _color == PieceType.WHITE else \
                        self.item_black_rook_h
                _rook_rank, _rook_file = _rook.Square()

                _kingside_castling_move = PieceMove(
                    piece, None, _rook,
                    MoveType.CASTLING_K,
                    (_rank, _file), (_rank, _file+2), [(_rook_rank, _rook_file), (_rank, _file+1)]
                )
                _avail_moves.append(_kingside_castling_move)
            
            # Queen-side
            if self.__is_castling_available(_color, MoveType.CASTLING_Q):
                if self.debug_mode == True:
                    print("Queenside Castling Available")
                
                _rook = self.item_white_rook_a if _color == PieceType.WHITE else \
                        self.item_black_rook_a
                _rook_rank, _rook_file = _rook.Square()

                _queenside_castling_move = PieceMove(
                    piece, None, _rook,
                    MoveType.CASTLING_Q,
                    (_rank, _file), (_rank, _file-2), [(_rook_rank, _rook_file), (_rook_rank, _file-1)]
                )
                _avail_moves.append(_queenside_castling_move)
        
        # En passant
        if _kind == PieceType.PAWN:
            if self.__is_en_passant_available(_color, _rank, _file):
                if self.debug_mode == True:
                    print("En-passant available")
                
                _pawn_in_capture = self.__move_history[-1].PieceToMove()
                _pawn_rank, _pawn_file = _pawn_in_capture.Square()
                _en_passant_move = PieceMove(
                    piece, _pawn_in_capture, None,
                    MoveType.EN_PASSANT,
                    (_rank, _file), 
                    (_rank+1, _pawn_file) if _color == PieceType.WHITE else (_rank-1, _pawn_file),
                    [(_pawn_rank, _pawn_file)]
                )

                if self.__is_legal_move(_en_passant_move):
                    _avail_moves.append(_en_passant_move)

        self.avail_moves = _avail_moves

        return (len(self.avail_moves) > 0)

    def __get_item_from_square(self, rank : int, file : int) -> ChessPiece | None:
        if self.__reversed == False:
            _pos = QPoint( (file * 100 + 50), ((7 - rank) * 100 + 45))
        else:
            _pos = QPoint( ((7 - file) * 100 + 50), (rank * 100 + 45))
        
        _item = self.board_view.itemAt(_pos)

        # Check if there exists a piece on the square
        if isinstance(_item, ChessPiece):
            return _item
        else:
            return None
    
    @staticmethod
    def __get_square_from_pos(pos : QPoint, reversed : bool) -> tuple[int, int]:
        # Get coordinate of mouse-event 
        _x = pos.x(); _y = pos.y()

        # Ignore the input for boundary
        if _x % 100 == 0 or _y % 100 == 0:
            return (-1, -1)

        # Compute rank / file
        if reversed == False:
            _rank = 7 - (_y // 100)
            _file = _x // 100
        else:
            _rank = _y // 100
            _file = 7 - (_x // 100)
        
        return (_rank, _file)
    
    def __get_squares_on_path(self, movedir : MoveDir, color : PieceType,
                                    rank : int, file : int, maxdist : int) -> list[tuple[int, int]]:
        _squares_on_path = []
        _dist = 1

        match movedir:
            case MoveDir.UP:
                _curr_rank = rank + 1
                while _curr_rank < 8 and _dist <= maxdist:
                    # Target square
                    _piece_on_square = self.board_status[_curr_rank][file]
                    
                    # Empty on-path : Keep going
                    if _piece_on_square == PieceType.EMPTY:
                        _squares_on_path.append((_curr_rank, file))
                        _curr_rank += 1
                        _dist += 1
                    # Meet Opponent Piece First : Can reach and then finish
                    elif _piece_on_square & PieceType.COLOR_MASK != color:
                        _squares_on_path.append((_curr_rank, file))
                        break
                    # Meet Ally Piece First : Finish
                    else:
                        break
            
            case MoveDir.DOWN:
                _curr_rank = rank - 1
                while _curr_rank >= 0 and _dist <= maxdist:
                    # Target square
                    _piece_on_square = self.board_status[_curr_rank][file]
                    
                    # Empty on-path : Keep going
                    if _piece_on_square == PieceType.EMPTY:
                        _squares_on_path.append((_curr_rank, file))
                        _curr_rank -= 1
                        _dist += 1
                    # Meet Opponent Piece First : Can reach and then finish
                    elif _piece_on_square & PieceType.COLOR_MASK != color:
                        _squares_on_path.append((_curr_rank, file))
                        break
                    # Meet Ally Piece First : Finish
                    else:
                        break
            
            case MoveDir.LEFT:
                _curr_file = file - 1
                while _curr_file >= 0 and _dist <= maxdist:
                    # Target square
                    _piece_on_square = self.board_status[rank][_curr_file]

                    # Empty on-path : Keep going
                    if _piece_on_square == PieceType.EMPTY:
                        _squares_on_path.append((rank, _curr_file))
                        _curr_file -= 1
                        _dist += 1
                    # Meet Opponent Piece First : Can reach and then finish
                    elif _piece_on_square & PieceType.COLOR_MASK != color:
                        _squares_on_path.append((rank, _curr_file))
                        break
                    # Meet Ally Piece First : Don't add the square and Finish
                    else:
                        break
            
            case MoveDir.RIGHT:
                _curr_file = file + 1
                while _curr_file < 8 and _dist <= maxdist:
                    # Target square
                    _piece_on_square = self.board_status[rank][_curr_file]

                    # Empty on-path : Keep going
                    if _piece_on_square == PieceType.EMPTY:
                        _squares_on_path.append((rank, _curr_file))
                        _curr_file += 1
                        _dist += 1
                    # Meet Opponent Piece First : Can reach and then finish
                    elif _piece_on_square & PieceType.COLOR_MASK != color:
                        _squares_on_path.append((rank, _curr_file))
                        break
                    # Meet Ally Piece First : Finish
                    else:
                        break
            
            case MoveDir.LEFTUP:
                _curr_rank = rank + 1
                _curr_file = file - 1
                while _curr_rank < 8 and _curr_file >= 0 and _dist <= maxdist:
                    # Target square
                    _piece_on_square = self.board_status[_curr_rank][_curr_file]

                    # Empty on-path : Keep going
                    if _piece_on_square == PieceType.EMPTY:
                        _squares_on_path.append((_curr_rank, _curr_file))
                        _curr_rank += 1
                        _curr_file -= 1
                        _dist += 1
                    # Meet Opponent Piece First : Can reach and then finish
                    elif _piece_on_square & PieceType.COLOR_MASK != color:
                        _squares_on_path.append((_curr_rank, _curr_file))
                        break
                    # Meet Ally Piece First : Finish
                    else:
                        break
            
            case MoveDir.RIGHTUP:
                _curr_rank = rank + 1
                _curr_file = file + 1
                while _curr_rank < 8 and _curr_file < 8 and _dist <= maxdist:
                    # Target square
                    _piece_on_square = self.board_status[_curr_rank][_curr_file]

                    # Empty on-path : Keep going
                    if _piece_on_square == PieceType.EMPTY:
                        _squares_on_path.append((_curr_rank, _curr_file))
                        _curr_rank += 1
                        _curr_file += 1
                        _dist += 1
                    # Meet Opponent Piece First : Can reach and then finish
                    elif _piece_on_square & PieceType.COLOR_MASK != color:
                        _squares_on_path.append((_curr_rank, _curr_file))
                        break
                    # Meet Ally Piece First : Finish
                    else:
                        break
            
            case MoveDir.LEFTDOWN:
                _curr_rank = rank - 1
                _curr_file = file - 1
                while _curr_rank >= 0 and _curr_file >= 0 and _dist <= maxdist:
                    # Target square
                    _piece_on_square = self.board_status[_curr_rank][_curr_file]

                    # Empty on-path : Keep going
                    if _piece_on_square == PieceType.EMPTY:
                        _squares_on_path.append((_curr_rank, _curr_file))
                        _curr_rank -= 1
                        _curr_file -= 1
                        _dist += 1
                    # Meet Opponent Piece First : Can reach and then finish
                    elif _piece_on_square & PieceType.COLOR_MASK != color:
                        _squares_on_path.append((_curr_rank, _curr_file))
                        break
                    # Meet Ally Piece First : Finish
                    else:
                        break

            case MoveDir.RIGHTDOWN:
                _curr_rank = rank - 1
                _curr_file = file + 1
                while _curr_rank >= 0 and _curr_file < 8 and _dist <= maxdist:
                    # Target square
                    _piece_on_square = self.board_status[_curr_rank][_curr_file]

                    # Empty on-path : Keep going
                    if _piece_on_square == PieceType.EMPTY:
                        _squares_on_path.append((_curr_rank, _curr_file))
                        _curr_rank -= 1
                        _curr_file += 1
                        _dist += 1
                    # Meet Opponent Piece First : Can reach and then finish
                    elif _piece_on_square & PieceType.COLOR_MASK != color:
                        _squares_on_path.append((_curr_rank, _curr_file))
                        break
                    # Meet Ally Piece First : Finish
                    else:
                        break
            
            case MoveDir.KNIGHT:
                for leap in [(-2, 1), (-1, 2), (1, 2), (2, 1),
                             (2, -1), (1, -2), (-1, -2), (-2, -1)]:
                    _curr_rank = rank + leap[0]
                    _curr_file = file + leap[1]
                    
                    # Check if square is valid
                    if 0 <= _curr_rank and _curr_rank < 8 and 0 <= _curr_file and _curr_file < 8:
                        # Target square
                        _piece_on_square = self.board_status[_curr_rank][_curr_file]

                        # Check if the target square is either empty or of opponent piece
                        if _piece_on_square == PieceType.EMPTY or \
                           _piece_on_square & PieceType.COLOR_MASK != color:
                            _squares_on_path.append((_curr_rank, _curr_file))
        
        return _squares_on_path

    def __get_squares_pawn(self, color : PieceType, is_already_moved : bool, 
                                 rank : int, file : int) -> list[tuple[int, int]]:
        _candidate_square = []

        match color:
            case PieceType.WHITE:
                # Pawn's basic movement : Leap forward a square
                if self.board_status[rank+1][file] == PieceType.EMPTY:
                    _candidate_square.append((rank+1, file))

                    # Pawn's first movement : Can leap forward 2 squares (if not blocked by any piece)
                    if is_already_moved == False:
                        if self.board_status[rank+2][file] == PieceType.EMPTY:
                            _candidate_square.append((rank+2, file))
                
                # Pawn's capturing movement : Leap forward a square 'diagonally'
                if file > 0:
                    if self.board_status[rank+1][file-1] != PieceType.EMPTY and \
                       self.board_status[rank+1][file-1] & PieceType.COLOR_MASK == PieceType.BLACK:
                        _candidate_square.append((rank+1, file-1))
                if file < 7:
                    if self.board_status[rank+1][file+1] != PieceType.EMPTY and \
                       self.board_status[rank+1][file+1] & PieceType.COLOR_MASK == PieceType.BLACK:
                        _candidate_square.append((rank+1, file+1))
                
                # En passant : Pawn's special movement
                # TODO : implement this
            
            case PieceType.BLACK:
                # Pawn's basic movement : Leap forward a square
                if self.board_status[rank-1][file] == PieceType.EMPTY:
                    _candidate_square.append((rank-1, file))

                    # Pawn's first movement : Can leap forward 2 squares (if not blocked by any piece)
                    if is_already_moved == False:
                        if self.board_status[rank-2][file] == PieceType.EMPTY:
                            _candidate_square.append((rank-2, file))
                
                # Pawn's capturing movement : Leap forward a square 'diagonally'
                if file > 0:
                    if self.board_status[rank-1][file-1] != PieceType.EMPTY and \
                       self.board_status[rank-1][file-1] & PieceType.COLOR_MASK == PieceType.WHITE:
                        _candidate_square.append((rank-1, file-1))
                if file < 7:
                    if self.board_status[rank-1][file+1] != PieceType.EMPTY and \
                       self.board_status[rank-1][file+1] & PieceType.COLOR_MASK == PieceType.WHITE:
                        _candidate_square.append((rank-1, file+1))
                
                # En passant : Pawn's special movement
                # TODO : implement this
        
        return _candidate_square

    @staticmethod
    def __get_pos_from_square(rank : int, file : int, reversed : bool = False) -> QPoint:
        if reversed == False:
            return QPoint(file * 100, (7 - rank) * 100)
        else:
            return QPoint((7 - file) * 100, rank * 100)

    def __hand_player_turn(self) -> None:
        self.__turn = PieceType.BLACK if self.__turn == PieceType.WHITE else PieceType.WHITE
        self.turnChanged.emit()
    
    def __highlight_available_moves(self) -> None:
        for _move in self.avail_moves:
            _piece_in_capture = _move.PieceInCapture()
            _rank, _file = _move.NewSquare()

            _highlight = QGraphicsPixmapItem()
            self.__item_highlight.append(_highlight)
            if _piece_in_capture == None:
                _highlight.setPixmap(self.resource.highlight_dot)
            else:
                _highlight.setPixmap(self.resource.highlight_circle)
            
            self.board_scene.addItem(_highlight)
            _highlight.setPos(ChessBoard.__get_pos_from_square(_rank, _file, self.__reversed))

    def __is_castling_available(self, turn : PieceType, side : MoveType):
        match (turn, side):
            # White, King-side Castling
            case (PieceType.WHITE, MoveType.CASTLING_K):
                _item_king = self.item_white_king
                _item_rook = self.item_white_rook_h
                _square_between = [(0, 5), (0, 6)] # Squares between king and rook
                _square_on_path = [(0, 5), (0, 6)] # Squares king goes through

            # White, Queen-side Castling
            case (PieceType.WHITE, MoveType.CASTLING_Q):
                _item_king = self.item_white_king
                _item_rook = self.item_white_rook_a
                _square_between = [(0, 1), (0, 2), (0, 3)] # Squares between king and rook
                _square_on_path = [(0, 2), (0, 3)]         # Squares king goes through
            
            # Black, King-side Castling
            case (PieceType.BLACK, MoveType.CASTLING_K):
                _item_king = self.item_black_king
                _item_rook = self.item_black_rook_h
                _square_between = [(7, 5), (7, 6)] # Squares between king and rook
                _square_on_path = [(7, 5), (7, 6)] # Squares king goes through
            
            # Black, Queen-side Castling
            case (PieceType.BLACK, MoveType.CASTLING_Q):
                _item_king = self.item_black_king
                _item_rook = self.item_black_rook_a
                _square_between = [(7, 1), (7, 2), (7, 3)] # Squares between king and rook
                _square_on_path = [(7, 2), (7, 3)]         # Squares king goes through
        
        # Check if both king and rook haven't moved in the game
        if _item_king.isAlreadyMoved() or _item_rook.isAlreadyMoved():
            return False
        
        # Check if all squares between king and rook are empty.
        for _rank, _file in _square_between:
            if self.board_status[_rank][_file] != PieceType.EMPTY:
                return False

        # Check if king is currently on attack.
        if not ChessBoard.__check_king_safety(turn, self.board_status):
            return False
        
        # Check if the castling path is under attack.
        _tmp_board_status = deepcopy(self.board_status)
        _old_rank, _old_file = _item_king.Square()
        for _rank, _file in _square_on_path:
            # Temporarily change king's square
            _tmp_board_status[_old_rank][_old_file] = PieceType.EMPTY
            _tmp_board_status[_rank][_file] = _item_king.PieceType()

            # Check king's safety
            if not ChessBoard.__check_king_safety(turn, _tmp_board_status):
                return False
        
            # Roll back _tmp_board_status
            _tmp_board_status[_old_rank][_old_file] = _item_king.PieceType()
            _tmp_board_status[_rank][_file] = PieceType.EMPTY
        
        # If current board status passed all of them, then Castling is available.
        return True

    def __is_check_state(self):
        return (not ChessBoard.__check_king_safety(self.__turn, self.board_status))    

    def __is_en_passant_available(self, turn : PieceType,
                                        rank : int, file : int):
        # Get En passant rank
        _en_passant_rank = 4 if turn == PieceType.WHITE else 3

        # When there is no move done in the game
        if len(self.__move_history) == 0:
            return False
        
        # Get last moved piece
        _piece_last_moved = self.__move_history[-1].PieceToMove()

        # Check if last moved piece is opponent's double-leaped pawn right next to current pawn
        if _piece_last_moved.PieceKind() == PieceType.PAWN:
            _pawn_rank, _pawn_file = _piece_last_moved.Square()
            if rank == _en_passant_rank and _pawn_rank == _en_passant_rank and \
                abs(file - _pawn_file) == 1:
                return True
        
        return False

    def __is_legal_move(self, move : PieceMove) -> bool:
        # Temporarily update board status to determine king's safety
        _tmp_board_status = deepcopy(self.board_status)
        ChessBoard.__apply_move_to_board_status(move, _tmp_board_status)

        # Check king's safety after given move
        return ChessBoard.__check_king_safety(move.PieceToMove().PieceColor(), _tmp_board_status)

    def __is_no_avail_move(self) -> bool:
        _avail_move_exist = False

        # White
        if self.__turn == PieceType.WHITE:
            for _piece in self.active_white_piece:
                _avail_move_exist |= self.__get_available_moves(_piece)
        # Black
        elif self.__turn == PieceType.BLACK:
            for _piece in self.active_black_piece:
                _avail_move_exist |= self.__get_available_moves(_piece)
        # Invalid case
        else:
            print(f'ChessBoard.__is_no_avail_move() : ')
            print(f'Invalid \'turn\' Detected : {self.__turn}')
            exit()
        
        return (not _avail_move_exist)
    
    def __print_active_piece(self) -> None:
        print('White\'s active pieces : \n| ', end='')
        for _piece in self.active_white_piece:
            print(_piece.ObjectName(), end=' | ')
        print()

        print('Black\'s active pieces : \n| ', end='')
        for _piece in self.active_black_piece:
            print(_piece.ObjectName(), end=' | ')
        print()

    @staticmethod
    def __print_board_status(boardStatus : list[list[PieceType]]):
        print("="*110)
        for _rank in range(7, -1, -1):
            for _file in range(8):
                print(str(boardStatus[_rank][_file]), end = ' ')
            print()
        print("="*110)

    def __process_after_move(self) -> None:
        _last_move = self.__move_history[-1]
        _piece_to_move = _last_move.PieceToMove()

        # Update piece & board status
        self.__update_piece_status(_last_move)
        self.__update_board_status(_last_move)

        if self.debug_mode == True:
            ChessBoard.__print_board_status(self.board_status)
            self.__print_active_piece()

        # Clear Animation(s)
        self.animation.clear()
        if _last_move.MoveType() in [MoveType.CASTLING_K, MoveType.CASTLING_Q]:
            self.aux_animation.clear()
        
        # Promotion
        if _last_move.MoveType() == MoveType.PROMOTION:
            self.__promotion_mode == True

            _rank, _file = _piece_to_move.Square()
            if True: # If promotion item is vertical
                if _piece_to_move.PieceColor() == PieceType.WHITE:
                    # If board is not reversed
                    self.item_promotion_white.setPos(_file * 100, 0)
                    self.item_promotion_white.setVisible(True)
                elif _piece_to_move.PieceColor() == PieceType.BLACK:
                    # If board is not reversed
                    self.item_promotion_black.setPos(_file * 100, 400)
                    self.item_promotion_black.setVisible(True)
                else:
                    exit()

            # For the promotion case, [hand turn & check game-over] must be done after promotion.
            # Hand the remain process to 'promotionItemClickHandler()'.
            return
        
        # Hand the turn and check if game is over
        self.__hand_player_turn()
        self.__check_game_over()
    
    def __process_move(self, move : PieceMove) -> None:
        _piece_to_move         = move.PieceToMove()
        _old_rank, _old_file   = move.OldSquare()
        _new_rank, _new_file   = move.NewSquare()
        _old_pos_x, _old_pos_y = ChessPiece.getPosFromSquare(_old_rank, _old_file, self.__reversed)
        _new_pos_x, _new_pos_y = ChessPiece.getPosFromSquare(_new_rank, _new_file, self.__reversed)

        self.animation.setItem(_piece_to_move)
        for i in range(101):
            step = i / 100
            self.animation.setPosAt(step, QPointF(
                _old_pos_x * (1 - step) + _new_pos_x * step,
                _old_pos_y * (1 - step) + _new_pos_y * step
            ))
        
        # Castling : Move Rook simultaneously
        if move.MoveType() in [MoveType.CASTLING_K, MoveType.CASTLING_Q]:
            _piece_aux = move.PieceAux()
            _aux_old_rank, _aux_old_file = move.AuxSquare()[0]
            _aux_new_rank, _aux_new_file = move.AuxSquare()[1]
            _aux_old_pos_x, _aux_old_pos_y = ChessPiece.getPosFromSquare(_aux_old_rank, _aux_old_file, self.__reversed)
            _aux_new_pos_x, _aux_new_pos_y = ChessPiece.getPosFromSquare(_aux_new_rank, _aux_new_file, self.__reversed)

            self.aux_animation = QGraphicsItemAnimation(self)
            self.aux_animation.setItem(_piece_aux)
            self.aux_animation.setTimeLine(self.timeline) # Share same timeline

            for i in range(101):
                step = i / 100
                self.aux_animation.setPosAt(step, QPointF(
                    _aux_old_pos_x * (1 - step) + _aux_new_pos_x * step,
                    _aux_old_pos_y * (1 - step) + _aux_new_pos_y * step
                ))
        
        # Save the move into move history
        self.__move_history.append(move)

        # Start timeline : Run animation
        self.timeline.start()

    def __remove_highlight(self) -> None:
        for _item in self.__item_highlight:
            self.board_scene.removeItem(_item)
            del _item
        self.__item_highlight.clear()
    
    def __remove_move_history(self) -> None:
        for _move in self.__move_history:
            del _move
        self.__move_history.clear()

    def __reset_chess_board(self) -> None:
        # Reset all pieces
        self.item_white_king    .reset(0, 4);     self.item_black_king    .reset(7, 4)
        self.item_white_queen   .reset(0, 3);     self.item_black_queen   .reset(7, 3)
        self.item_white_rook_a  .reset(0, 0);     self.item_black_rook_a  .reset(7, 0)
        self.item_white_rook_h  .reset(0, 7);     self.item_black_rook_h  .reset(7, 7)
        self.item_white_bishop_c.reset(0, 2);     self.item_black_bishop_c.reset(7, 2)
        self.item_white_bishop_f.reset(0, 5);     self.item_black_bishop_f.reset(7, 5)
        self.item_white_knight_b.reset(0, 1);     self.item_black_knight_b.reset(7, 1)
        self.item_white_knight_g.reset(0, 6);     self.item_black_knight_g.reset(7, 6)

        self.item_white_pawn_a.reset(1, 0);       self.item_black_pawn_a.reset(6, 0)
        self.item_white_pawn_b.reset(1, 1);       self.item_black_pawn_b.reset(6, 1)
        self.item_white_pawn_c.reset(1, 2);       self.item_black_pawn_c.reset(6, 2)
        self.item_white_pawn_d.reset(1, 3);       self.item_black_pawn_d.reset(6, 3)
        self.item_white_pawn_e.reset(1, 4);       self.item_black_pawn_e.reset(6, 4)
        self.item_white_pawn_f.reset(1, 5);       self.item_black_pawn_f.reset(6, 5)
        self.item_white_pawn_g.reset(1, 6);       self.item_black_pawn_g.reset(6, 6)
        self.item_white_pawn_h.reset(1, 7);       self.item_black_pawn_h.reset(6, 7)

        # Activate every piece
        self.active_white_piece.clear(); self.active_black_piece.clear()
        self.active_white_piece = [
            self.item_white_king,     self.item_white_queen,    self.item_white_rook_a,   self.item_white_rook_h,
            self.item_white_bishop_c, self.item_white_bishop_f, self.item_white_knight_b, self.item_white_knight_g,
            self.item_white_pawn_a,   self.item_white_pawn_b,   self.item_white_pawn_c,   self.item_white_pawn_d,
            self.item_white_pawn_e,   self.item_white_pawn_f,   self.item_white_pawn_g,   self.item_white_pawn_h
        ]
        self.active_black_piece = [
            self.item_black_king,     self.item_black_queen,    self.item_black_rook_a,   self.item_black_rook_h,
            self.item_black_bishop_c, self.item_black_bishop_f, self.item_black_knight_b, self.item_black_knight_g,
            self.item_black_pawn_a,   self.item_black_pawn_b,   self.item_black_pawn_c,   self.item_black_pawn_d,
            self.item_black_pawn_e,   self.item_black_pawn_f,   self.item_black_pawn_g,   self.item_black_pawn_h
        ]
        
        # Reset game status
        self.__turn = PieceType.WHITE
        self.__reversed = False
        self.__free_focus()
        self.__remove_move_history()
        self.__promotion_mode = False
        self.board_status.clear()
        self.board_status = [
            [PieceType.WHITE_ROOK, PieceType.WHITE_KNIGHT, PieceType.WHITE_BISHOP, PieceType.WHITE_QUEEN, 
             PieceType.WHITE_KING, PieceType.WHITE_BISHOP, PieceType.WHITE_KNIGHT, PieceType.WHITE_ROOK],
            [PieceType.WHITE_PAWN, PieceType.WHITE_PAWN,   PieceType.WHITE_PAWN,   PieceType.WHITE_PAWN,
             PieceType.WHITE_PAWN, PieceType.WHITE_PAWN,   PieceType.WHITE_PAWN,   PieceType.WHITE_PAWN],
            [PieceType.EMPTY,      PieceType.EMPTY,        PieceType.EMPTY,        PieceType.EMPTY, 
             PieceType.EMPTY,      PieceType.EMPTY,        PieceType.EMPTY,        PieceType.EMPTY],
            [PieceType.EMPTY,      PieceType.EMPTY,        PieceType.EMPTY,        PieceType.EMPTY, 
             PieceType.EMPTY,      PieceType.EMPTY,        PieceType.EMPTY,        PieceType.EMPTY],
            [PieceType.EMPTY,      PieceType.EMPTY,        PieceType.EMPTY,        PieceType.EMPTY, 
             PieceType.EMPTY,      PieceType.EMPTY,        PieceType.EMPTY,        PieceType.EMPTY],
            [PieceType.EMPTY,      PieceType.EMPTY,        PieceType.EMPTY,        PieceType.EMPTY, 
             PieceType.EMPTY,      PieceType.EMPTY,        PieceType.EMPTY,        PieceType.EMPTY],
            [PieceType.BLACK_PAWN, PieceType.BLACK_PAWN,   PieceType.BLACK_PAWN,   PieceType.BLACK_PAWN,
             PieceType.BLACK_PAWN, PieceType.BLACK_PAWN,   PieceType.BLACK_PAWN,   PieceType.BLACK_PAWN],
            [PieceType.BLACK_ROOK, PieceType.BLACK_KNIGHT, PieceType.BLACK_BISHOP, PieceType.BLACK_QUEEN, 
             PieceType.BLACK_KING, PieceType.BLACK_BISHOP, PieceType.BLACK_KNIGHT, PieceType.BLACK_ROOK]
        ]

    def __reverse_chess_board(self) -> None:
        self.__reversed = not self.__reversed

        self.__free_focus()

        for _white_piece in self.active_white_piece:
            _white_piece.reverse()
        
        for _black_piece in self.active_black_piece:
            _black_piece.reverse()
    
    def __set_focus_on_piece(self, piece : ChessPiece) -> None:
        # Remove previous highlight moves
        self.__remove_highlight()

        # Set focus on the piece
        self.__is_in_focus = True
        self.__piece_in_focus = piece

        # Get available moves
        self.__get_available_moves(piece)

        # Show available squares on the command
        if self.debug_mode == True:
            if len(self.avail_moves) > 0:
                print('Available squares : ', end='')
                print('| ', end='')
                for _move in self.avail_moves:
                    _rank, _file = _move.NewSquare()
                    _str = ChessPiece.fileDict[_file] + ChessPiece.rankDict[_rank]
                    print(_str, end = ' | ')
                print()
            else:
                print('No available move')

        # Highlight available squares
        self.__highlight_available_moves()
    
    def __update_board_status(self, move : PieceMove) -> None:
        ChessBoard.__apply_move_to_board_status(move, self.board_status)

    def __update_piece_status(self, move : PieceMove) -> None:
        _piece_to_move = move.PieceToMove()
        _new_rank, _new_file = move.NewSquare()
        _piece_to_move.setMoved()
        _piece_to_move.setSquare(_new_rank, _new_file)

        _piece_in_capture = move.PieceInCapture()
        if _piece_in_capture != None:
            # Set invisible
            _piece_in_capture.setVisible(False)

            # Remove from active piece list
            if _piece_in_capture.PieceColor() == PieceType.WHITE:
                self.active_white_piece.remove(_piece_in_capture)
            elif _piece_in_capture.PieceColor() == PieceType.BLACK:
                self.active_black_piece.remove(_piece_in_capture)
            else:
                exit()
        
        if move.MoveType() in [MoveType.CASTLING_K, MoveType.CASTLING_Q]:
            _piece_aux = move.PieceAux()
            _aux_new_rank, _aux_new_file = move.AuxSquare()[1]
            _piece_aux.setMoved()
            _piece_aux.setSquare(_aux_new_rank, _aux_new_file)

