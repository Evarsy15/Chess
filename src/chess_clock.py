from PySide6.QtCore import (Qt, QObject, QRect, QRectF,
                            QTimer, Signal, Slot)
from PySide6.QtWidgets import QWidget, QLCDNumber

class ChessClock(QObject):
    def __init__(self, time : int,
                       fischer : int = 0,
                       parent : QObject = None) :
        super().__init__()
        self.clock_lcd = QLCDNumber(parent)
        self.clock_timer = QTimer(parent)

    # Initialize Clock Display
        self.clock_lcd.setSegmentStyle(QLCDNumber.Filled)

    # Initialize Inner-Timer
        self.clock_timer.setTimerType(Qt.PreciseTimer)
        self.clock_timer.stop()
        self.clock_timer.setInterval(1000) # 1 second
    
    # Initialize variables for clock management
        self.launched = False
        self.unlimited = False
        self.base_time = time
        self.fischer_time = fischer
        self.clock_time = self.base_time
        self.__display_time()

    # Connect inside signal-slot
        self.clock_timer.timeout.connect(self.__update_clock)

    def setGeometry(self, pos : QRect | QRectF):
        self.clock_lcd.setGeometry(pos)

    def setObjectName(self, objname : str) -> None:
        super().setObjectName(objname)
        self.clock_lcd.setObjectName(objname + '_clock_lcd')
        self.clock_timer.setObjectName(objname + '_clock_timer')


    def setTimer(self, time : int = 0, fischer : int = 0):
        if time < 0:
            print("ChessClock.setTimer() received negative time factor.")
            exit()
        
        self.launched = False
        self.unlimited = False
        self.base_time = time
        self.fischer_time = fischer
        self.clock_time = time
        self.__display_time()
    
    def setUnlimited(self):
        self.launched = False
        self.unlimited = True
        self.clock_lcd.display("--:--")
    
    # Signal
    timeOut = Signal()

    def startClock(self):
        if self.unlimited == False:
            self.launched = True
            self.clock_timer.start(1000)
    
    def pauseClock(self):
        if self.unlimited == False:
            self.__remaining_time = self.clock_timer.remainingTime()
            self.clock_timer.stop()
    
    def resumeClock(self):
        if self.unlimited == False:
            if self.launched == True:
                self.clock_time += self.fischer_time
                self.clock_timer.start(self.__remaining_time)
            else:
                self.startClock()
    
    def resetClock(self):
        self.launched = False
        self.clock_timer.stop()
        self.clock_time = self.base_time
        self.__display_time()

    @Slot()
    def __update_clock(self):
        self.clock_time -= 1
        self.__display_time()

        if self.clock_time == 0:
            self.clock_timer.stop()
            self.timeOut.emit()
            return
        
        self.clock_timer.start(1000)

    def __display_time(self):
        __min = self.clock_time // 60
        __sec = self.clock_time % 60
        __display_str = f'{__min}:{__sec}' if __sec >= 10 else \
                        f'{__min}:0{__sec}'
        self.clock_lcd.display(__display_str)

    