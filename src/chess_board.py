import os
from enum import IntEnum
from copy import deepcopy
from PySide6.QtCore import (Qt, QObject, QPoint, QPointF, QRect, QRectF, QTimeLine, Signal)
from PySide6.QtGui import QPixmap, QPainter, QTransform
from PySide6.QtWidgets import (QWidget,
    QGraphicsScene, QGraphicsView, QGraphicsItemAnimation
)

from image import ChessImage
from .chess_piece import ChessPiece, PieceType

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
    PAWN      = 9

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

    def mousePressEvent(self, event):
        __pos  = event.pos()
        __item = self.itemAt(__pos)

        # Determine which item is clicked: piece or board.
        if isinstance(__item, ChessPiece):
            self.pieceClicked.emit(__item)
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

        self.__init_chess_piece()
        self.__init_chess_board()
        self.__connect_signal_and_slot()
    
    def setGeometry(self, rect : QRect | QRectF):
        self.board_view.setGeometry(rect)
    
    def show(self):
        self.board_view.show()
    
    def updateResource(self):
        pass
    
    # Chess-board event handler
    def boardClickHandler(self, pos : QPoint) -> None:
        if self.debug_mode == True:
            print(f'ChessBoard.boardClickHandler() : ')
            print(f' - pos : ({pos.x()}, {pos.y()})')
        
        # When there is a piece in focus
        if self.__is_in_focus == True:
            # Get rank/file coordinate for clicked square
            _new_rank, _new_file = ChessBoard.__get_square_from_pos(pos)
            if self.debug_mode == True:
                if (_new_rank, _new_file) != (-1, -1):
                    print(f'{ChessPiece.fileDict[_new_file]}{ChessPiece.rankDict[_new_rank]} square')
                else:
                    print(f'Boundary')
            
            # Check if a player clicked available squares
            # When a square is clicked for legal move : Process as the rule
            if (_new_rank, _new_file) in self.avail_squares:
                # Get square information
                _piece_on_square = self.board_status[_new_rank][_new_file]

                # When the target square is empty
                if ChessPiece.isEmpty(_piece_on_square):
                    # Promotion
                    if False:   # if self.__is_promotion_move(_rank, _file):
                        pass
                    # Castling
                    elif False:
                        pass
                    # En passant
                    elif False:
                        pass
                    # Basic move
                    else:
                        self.__move_piece(self.__piece_in_focus, None, (_new_rank, _new_file))

                    # Hand player's turn
                    self.__hand_player_turn()
                
                # Otherwise : Ignore the input.
                # ※ If you want to capture opponent piece, you have to click the corresponding piece image.
                else:
                    pass
            
            # Mouse event for freeing focus : Do nothing
            else:
                pass

        # Free focus
        self.__free_focus()

    def pieceClickHandler(self, piece : ChessPiece) -> None:
        if self.debug_mode == True:
            _rank, _file = piece.Square()
            print(f'ChessBoard.pieceClickHandler() : ')
            print(f' - Clicked Piece : {piece.ObjectName()} at {ChessPiece.fileDict[_file]}{ChessPiece.rankDict[_rank]} square')

        # Check if any piece is in focus.
        # If so, check whether current piece is clicked for capturing or not.
        if self.__is_in_focus == True:
            if self.debug_mode == True:
                print(f" - Current focused piece : {self.__piece_in_focus.ObjectName()}")
            
            # Opponent piece : Check if piece is clicked for capturing
            if ChessPiece.isOpponentPiece(piece.PieceType(), self.__turn):
                _new_square = piece.Square()
                if _new_square in self.avail_squares:
                    # Move focused piece and capture clicked piece
                    self.__move_piece(self.__piece_in_focus, piece, _new_square)

                    # Save current move
                    
                    # Hand player's turn
                    self.__hand_player_turn()
                    
                # Free focus
                self.__free_focus()
            
            # Ally piece : Change focus of piece
            else:
                # Set focus on current piece
                self.__set_focus_on_piece(piece)

                # Get available squares to move
                self.avail_squares = self.__get_available_squares(piece)
                if self.debug_mode == True:
                    print('Available Squares : ', end='')
                    print(self.avail_squares)

                # Highlight available squares
                # TODO : implement this
        
        # Otherwise, set a focus on clicked piece if it is of current turn.
        else:
            # Check whether the piece is of current turn.
            if piece.PieceColor() == self.__turn:
                # Get square information
                _rank, _file = piece.Square()
            
                # Sanity check
                if piece.PieceType() != self.board_status[_rank][_file]:
                    print(f"Error : Board Status Inconsistency")
                    print(f"\tPiece detected at {ChessPiece.fileDict[_file]}{ChessPiece.rankDict[_rank]} square, ", end='')
                    print(f"ChessPiece.piece_type = {piece.PieceType()}, ", end='')
                    print(f"ChessBoard.board_status[{_rank}][{_file}] = {self.board_status[_rank][_file]}")
                    exit()

                # Set Focus on the piece
                self.__set_focus_on_piece(piece)

    def __init_chess_piece(self):
        self.item_white_king     = ChessPiece(0, 4, PieceType.WHITE_KING,   self.resource.white_king,   'white-king')
        self.item_white_queen    = ChessPiece(0, 3, PieceType.WHITE_QUEEN,  self.resource.white_queen,  'white-queen')
        self.item_white_rook_a   = ChessPiece(0, 0, PieceType.WHITE_ROOK,   self.resource.white_rook,   'white-rook-a')
        self.item_white_rook_h   = ChessPiece(0, 7, PieceType.WHITE_ROOK,   self.resource.white_rook,   'white-rook-h')
        self.item_white_bishop_c = ChessPiece(0, 2, PieceType.WHITE_BISHOP, self.resource.white_bishop, 'white-bishop-c')
        self.item_white_bishop_f = ChessPiece(0, 5, PieceType.WHITE_BISHOP, self.resource.white_bishop, 'white-bishop-f')
        self.item_white_knight_b = ChessPiece(0, 1, PieceType.WHITE_KNIGHT, self.resource.white_knight, 'white-knight-b')
        self.item_white_knight_g = ChessPiece(0, 6, PieceType.WHITE_KNIGHT, self.resource.white_knight, 'white-knight-g')
        self.item_white_pawn_a   = ChessPiece(1, 0, PieceType.WHITE_PAWN,   self.resource.white_pawn,   'white-pawn-a')
        self.item_white_pawn_b   = ChessPiece(1, 1, PieceType.WHITE_PAWN,   self.resource.white_pawn,   'white-pawn-b')
        self.item_white_pawn_c   = ChessPiece(1, 2, PieceType.WHITE_PAWN,   self.resource.white_pawn,   'white-pawn-c')
        self.item_white_pawn_d   = ChessPiece(1, 3, PieceType.WHITE_PAWN,   self.resource.white_pawn,   'white-pawn-d')
        self.item_white_pawn_e   = ChessPiece(1, 4, PieceType.WHITE_PAWN,   self.resource.white_pawn,   'white-pawn-e')
        self.item_white_pawn_f   = ChessPiece(1, 5, PieceType.WHITE_PAWN,   self.resource.white_pawn,   'white-pawn-f')
        self.item_white_pawn_g   = ChessPiece(1, 6, PieceType.WHITE_PAWN,   self.resource.white_pawn,   'white-pawn-g')
        self.item_white_pawn_h   = ChessPiece(1, 7, PieceType.WHITE_PAWN,   self.resource.white_pawn,   'white-pawn-h')

        self.item_black_king     = ChessPiece(7, 4, PieceType.BLACK_KING,   self.resource.black_king,   'black-king')
        self.item_black_queen    = ChessPiece(7, 3, PieceType.BLACK_QUEEN,  self.resource.black_queen,  'black-queen')
        self.item_black_rook_a   = ChessPiece(7, 0, PieceType.BLACK_ROOK,   self.resource.black_rook,   'black-rook-a')
        self.item_black_rook_h   = ChessPiece(7, 7, PieceType.BLACK_ROOK,   self.resource.black_rook,   'black-rook-h')
        self.item_black_bishop_c = ChessPiece(7, 2, PieceType.BLACK_BISHOP, self.resource.black_bishop, 'black-bishop-c')
        self.item_black_bishop_f = ChessPiece(7, 5, PieceType.BLACK_BISHOP, self.resource.black_bishop, 'black-bishop-f')
        self.item_black_knight_b = ChessPiece(7, 1, PieceType.BLACK_KNIGHT, self.resource.black_knight, 'black-knight-b')
        self.item_black_knight_g = ChessPiece(7, 6, PieceType.BLACK_KNIGHT, self.resource.black_knight, 'black-knight-g')
        self.item_black_pawn_a   = ChessPiece(6, 0, PieceType.BLACK_PAWN,   self.resource.black_pawn,   'black-pawn-a')
        self.item_black_pawn_b   = ChessPiece(6, 1, PieceType.BLACK_PAWN,   self.resource.black_pawn,   'black-pawn-b')
        self.item_black_pawn_c   = ChessPiece(6, 2, PieceType.BLACK_PAWN,   self.resource.black_pawn,   'black-pawn-c')
        self.item_black_pawn_d   = ChessPiece(6, 3, PieceType.BLACK_PAWN,   self.resource.black_pawn,   'black-pawn-d')
        self.item_black_pawn_e   = ChessPiece(6, 4, PieceType.BLACK_PAWN,   self.resource.black_pawn,   'black-pawn-e')
        self.item_black_pawn_f   = ChessPiece(6, 5, PieceType.BLACK_PAWN,   self.resource.black_pawn,   'black-pawn-f')
        self.item_black_pawn_g   = ChessPiece(6, 6, PieceType.BLACK_PAWN,   self.resource.black_pawn,   'black-pawn-g')
        self.item_black_pawn_h   = ChessPiece(6, 7, PieceType.BLACK_PAWN,   self.resource.black_pawn,   'black-pawn-h')

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
    
    def __init_chess_board(self):
        self.__turn = PieceType.WHITE         # Turn
        self.__is_in_focus = False            # Focus
        self.__piece_in_focus = None          # Piece in Focus
        self.__last_move = [None, None, None] # Last move (Piece, Old_Square, New_Square)
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
        
    def __connect_signal_and_slot(self):
        self.board_view.boardClicked.connect(self.boardClickHandler)
        self.board_view.pieceClicked.connect(self.pieceClickHandler)
    
    def __free_focus(self) -> None:
        self.__is_in_focus = False
        self.__piece_in_focus = None

    def __get_available_squares(self, piece : ChessPiece) -> list[tuple[int, int]]:
        # Get piece information
        _piece_type       = piece.PieceType()
        _is_already_moved = piece.isAlreadyMoved()
        _rank, _file      = piece.Square()

        # Sanity check
        if _piece_type != self.board_status[_rank][_file]:
            print(f"Error : Board Status Inconsistency")
            print(f"\tPiece detected at {ChessPiece.fileDict[_file]}{ChessPiece.rankDict[_rank]} square, ", end='')
            print(f"ChessPiece.piece_type = {_piece_type}, ", end='')
            print(f"ChessBoard.board_status[{_rank}][{_file}] = {self.board_status[_rank][_file]}")
            exit()

        # Get logically available squares with respect to the piece's movement
        _candidate_squares = self.__get_candidate_squares(_piece_type, _is_already_moved, _rank, _file)

        # Detect invalid movement with respect to king's safety
        # _avail_squares = self.__choose_legal_moves(_candidate_squares)

        return _candidate_squares # _avail_squares

    def __get_candidate_squares(self, piecetype : PieceType, 
                                      is_already_moved : bool,
                                      rank : int, file : int) -> list[tuple[int, int]]:
        _color = ChessPiece.getPieceColor(piecetype)
        _kind  = ChessPiece.getPieceKind (piecetype)
        _candidate_square = []

        match _kind:
            case PieceType.PAWN:
                # Pawn's movement
                _candidate_square.extend(self.__get_squares_pawn(_color, is_already_moved, rank, file))
            
            case PieceType.KNIGHT:
                # Knight's movement
                _candidate_square.extend(self.__get_squares_on_path(MoveDir.KNIGHT,    _color, rank, file, 2))
            
            case PieceType.BISHOP:
                # Bishop's movement : Move any distance diagonally
                _candidate_square.extend(self.__get_squares_on_path(MoveDir.LEFTUP,    _color, rank, file, 8))
                _candidate_square.extend(self.__get_squares_on_path(MoveDir.RIGHTUP,   _color, rank, file, 8))
                _candidate_square.extend(self.__get_squares_on_path(MoveDir.LEFTDOWN,  _color, rank, file, 8))
                _candidate_square.extend(self.__get_squares_on_path(MoveDir.RIGHTDOWN, _color, rank, file, 8))
            
            case PieceType.ROOK:
                # Rook's movement : Move any distance linearly
                _candidate_square.extend(self.__get_squares_on_path(MoveDir.UP,        _color, rank, file, 8))
                _candidate_square.extend(self.__get_squares_on_path(MoveDir.DOWN,      _color, rank, file, 8))
                _candidate_square.extend(self.__get_squares_on_path(MoveDir.LEFT,      _color, rank, file, 8))
                _candidate_square.extend(self.__get_squares_on_path(MoveDir.RIGHT,     _color, rank, file, 8))
            
            case PieceType.QUEEN:
                # Queen's movement : Move any distance with any direction
                _candidate_square.extend(self.__get_squares_on_path(MoveDir.UP,        _color, rank, file, 8))
                _candidate_square.extend(self.__get_squares_on_path(MoveDir.DOWN,      _color, rank, file, 8))
                _candidate_square.extend(self.__get_squares_on_path(MoveDir.LEFT,      _color, rank, file, 8))
                _candidate_square.extend(self.__get_squares_on_path(MoveDir.RIGHT,     _color, rank, file, 8))
                _candidate_square.extend(self.__get_squares_on_path(MoveDir.LEFTUP,    _color, rank, file, 8))
                _candidate_square.extend(self.__get_squares_on_path(MoveDir.RIGHTUP,   _color, rank, file, 8))
                _candidate_square.extend(self.__get_squares_on_path(MoveDir.LEFTDOWN,  _color, rank, file, 8))
                _candidate_square.extend(self.__get_squares_on_path(MoveDir.RIGHTDOWN, _color, rank, file, 8))
            
            case PieceType.KING:
                # King's basic movement : Move one square with any direction
                _candidate_square.extend(self.__get_squares_on_path(MoveDir.UP,        _color, rank, file, 1))
                _candidate_square.extend(self.__get_squares_on_path(MoveDir.DOWN,      _color, rank, file, 1))
                _candidate_square.extend(self.__get_squares_on_path(MoveDir.LEFT,      _color, rank, file, 1))
                _candidate_square.extend(self.__get_squares_on_path(MoveDir.RIGHT,     _color, rank, file, 1))
                _candidate_square.extend(self.__get_squares_on_path(MoveDir.LEFTUP,    _color, rank, file, 1))
                _candidate_square.extend(self.__get_squares_on_path(MoveDir.RIGHTUP,   _color, rank, file, 1))
                _candidate_square.extend(self.__get_squares_on_path(MoveDir.LEFTDOWN,  _color, rank, file, 1))
                _candidate_square.extend(self.__get_squares_on_path(MoveDir.RIGHTDOWN, _color, rank, file, 1))

                # Castling : King's special movement
                # TODO : implement this part
                
        return _candidate_square

    @staticmethod
    def __get_square_from_pos(pos : QPoint) -> tuple[int, int]:
        # Get coordinate of mouse-event 
        _x = pos.x(); _y = pos.y()

        # Ignore the input for boundary
        if _x % 100 == 0 or _y % 100 == 0:
            return (-1, -1)

        # Compute rank / file
        _rank = 7 - (_y // 100)
        _file = _x // 100
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

    def __hand_player_turn(self) -> None:
        self.__turn = PieceType.BLACK if self.__turn == PieceType.WHITE else PieceType.WHITE

    def __move_piece(self, pieceToMove : ChessPiece, 
                           pieceToBeCaptured : ChessPiece | None,
                           newsquare : tuple[int, int]) -> None:
        # Animated movement
        _old_rank, _old_file = pieceToMove.Square()
        _new_rank, _new_file = newsquare
        _old_pos_x, _old_pos_y = ChessPiece.getPosFromSquare(_old_rank, _old_file)
        _new_pos_x, _new_pos_y = ChessPiece.getPosFromSquare(_new_rank, _new_file)
        
        if self.debug_mode == True:
            print(f'oldpos = ({_old_pos_x}, {_old_pos_y}), newpos = ({_new_pos_x}, {_new_pos_y})')

        timeline = QTimeLine(200) # 200 ms
        timeline.setUpdateInterval(1)   # 1 ms

        animation = QGraphicsItemAnimation(self)
        animation.setItem(pieceToMove)
        animation.setTimeLine(timeline)
        for i in range(26):
            step = i / 25
            animation.setPosAt(step, QPointF(
                _old_pos_x * (1 - step) + _new_pos_x * step,
                _old_pos_y * (1 - step) + _new_pos_y * step
            ))

        timeline.start()

        # Disable captured piece
        if pieceToBeCaptured != None:
            pieceToBeCaptured.setVisible(False)

        # Update piece & board status
        pieceToMove.setMoved()
        pieceToMove.setSquare(_new_rank, _new_file)
        self.board_status[_old_rank][_old_file] = PieceType.EMPTY
        self.board_status[_new_rank][_new_file] = pieceToMove.PieceType()


    def __reset_chess_board(self) -> None:
        # Unimplemented
        pass
    
    def __set_focus_on_piece(self, piece : ChessPiece) -> None:
        # Set focus on the piece
        self.__is_in_focus = True
        self.__piece_in_focus = piece

        # Get available squares to move
        self.avail_squares = self.__get_available_squares(piece)
        if self.debug_mode == True:
            print('Available Squares : ', end='')
            print(self.avail_squares)

        # Highlight available squares
        # TODO : implement this

if __name__ == '__main__':
    exit(0)