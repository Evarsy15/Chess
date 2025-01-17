from PySide6.QtCore import (Qt, QObject, QRect, QRectF,
                            QTimer, Signal, Slot)
from PySide6.QtWidgets import QWidget, QLCDNumber

class ChessClock(QObject):
    def __init__(self, objname : str = '', parent : QObject = None) :
        super().__init__()
        self.setObjectName(objname)
        self.clock_lcd = QLCDNumber(parent)
        self.clock_timer = QTimer(parent)
        self.clock_time : int = 0

    # Initialize Clock Display
        self.clock_lcd.setObjectName(objname + '_clock_lcd')
        self.clock_lcd.setSegmentStyle(QLCDNumber.Filled)

    # Initialize Inner-Timer
        self.clock_timer.setObjectName(objname + '_clock_timer')
        self.clock_timer.setTimerType(Qt.PreciseTimer)
        self.clock_timer.stop()
        self.clock_timer.setInterval(1000) # 1 second


    # Connect inside signal-slot
        self.clock_timer.timeout.connect(self.__updateClock)

    def setGeometry(self, pos : QRect | QRectF):
        self.clock_lcd.setGeometry(pos)

    def setTimer(self, time : int = 0):
        if time < 0:
            print("ChessClock.setTimer() received negative time factor.")
            raise ValueError
        
        self.clock_time = time
        self.__display()
        
    
    # Signal
    signalTimeOver = Signal()

    def startClock(self):
        self.clock_timer.start()
    
    def pauseClock(self):
        self.clock_timer.stop()
        self.__remaining_time = self.clock_timer.remainingTime
    
    def resumeClock(self):
        self.clock_timer.start(self.__remaining_time)

    @Slot()
    def __updateClock(self):
        self.clock_time -= 1
        self.__display()
        if self.clock_time == 0:
            self.signalTimeOver.emit()

    def __display(self):
        __min = self.clock_time // 60
        __sec = self.clock_time % 60
        __display_str = f'{__min}:{__sec}' if __sec >= 10 else \
                        f'{__min}:0{__sec}'
        self.clock_lcd.display(__display_str)

    