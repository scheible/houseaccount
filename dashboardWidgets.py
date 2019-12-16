import math

from PyQt5.QtCore import Qt, QDate
from PyQt5.QtWidgets import QGraphicsView, \
    QGraphicsScene, \
    QGraphicsEllipseItem, \
    QGraphicsLineItem, \
    QGraphicsRectItem, \
    QWidget, QVBoxLayout, QHBoxLayout
from PyQt5.QtGui import QColor, \
    QPainter, \
    QLinearGradient, \
    QPen, QKeyEvent
from dataObjects import Database


class BarDashboardWidget(QGraphicsView):
    def __init__(self, parent=None):
        super(BarDashboardWidget, self).__init__(parent)

        self.__scene = QGraphicsScene()
        self.setScene(self.__scene)

        self.__min=0
        self.__max=10
        self.__barWidth = 30
        self.__barHeight = 200
        self.__barDistance = 60

        self.__values = []

    def keyPressEvent(self, event: QKeyEvent):
        if (event.key() == Qt.Key_Plus):
            print("pressed [+] key")
        elif (event.key() == Qt.Key_Minus):
            print("pressed [-] key")
        else:
            super(BarDashboardWidget, self).keyPressEvent(event)

    def clear(self):
        self.__values.clear()
        self.__max = 10

    def addItem(self, data, label):
        self.__values.append([label, data])
        if (data > self.__max):
            self.__max = int(data)

    def redraw(self):
        self.__scene.clear()
        self.__addGrid()

        xStart = 0

        for e in self.__values:
            label = e[0]
            value = e[1]

            height = self.__barHeight * value/self.__max

            bar = QGraphicsRectItem(xStart, 0, self.__barWidth, -height)
            bar.setBrush(QColor(0, 0, 200))
            self.__scene.addItem(bar)

            textItem = self.__scene.addText(label, self.font())
            textItem.setPos(xStart, 10)

            xStart += self.__barDistance

        height = self.__barHeight * 800/self.__max
        width = len(self.__values) * self.__barDistance
        redLine = QGraphicsLineItem(-30, -height, width+30, -height)
        redLine.setPen(QPen(QColor(240, 0, 0)))
        self.__scene.addItem(redLine)


        self.__scene.setSceneRect(-30, -30, width + 30, -self.__barHeight)
        #self.setSceneRect(-30, -30, width + 30, -self.__barHeight)

    def __addGrid(self):
        w = len(self.__values) * self.__barDistance
        p = QPen(QColor(200, 200, 200))

        for h in range(0, self.__max, 200):
            pxH = self.__barHeight * h / self.__max
            l = QGraphicsLineItem(0, -pxH, w, -pxH)
            l.setPen(p)
            self.__scene.addItem(l)


            textItem = self.__scene.addText(str(h) + " €", self.font())
            textItem.setDefaultTextColor(QColor(150, 150, 150))
            textItem.setPos(-50, -(pxH + 20))


class PieDashboardWidget(QGraphicsView):
    def __init__(self, parent=None):
        super(PieDashboardWidget, self).__init__(parent)

        self.__scene = QGraphicsScene()
        self.setScene(self.__scene)

        self.__colors = [QColor(255, 0, 0),
                         QColor(0, 255, 0),
                         QColor(0, 0, 255),
                         QColor(255, 255, 0),
                         QColor(0, 255, 255),
                         QColor(255, 0, 255),
                         QColor(120, 0, 0),
                         QColor(0, 120, 0),
                         QColor(0, 0, 120),
                         QColor(120, 0, 0)]

        self.__elements = []

    def addItemBatch(self, items):
        self.__elements = items

    def __getElementSum(self):
        sum=0
        for e in self.__elements:
            sum += e[0]
        return sum

    def __getColor(self, index: int):
        l = len(self.__colors)
        i = index % l
        return self.__colors[i]

    def __getPenisPos(self, startAngle, angle, dist):
        middleAngleDeg = (startAngle + angle / 2.0) / 16
        middleAngleRad = (2 * math.pi * middleAngleDeg) / (360)
        xOffset = math.cos(middleAngleRad) * dist
        yOffset = math.sin(middleAngleRad) * dist
        return xOffset, yOffset

    def redraw(self):
        self.__scene.clear()

        total = self.__getElementSum()
        startAngle = 0
        for i, element in enumerate(self.__elements):
            elementValue = element[0]
            elementText = element[1]

            angle = round(elementValue/total * 16 * 360)
            ellipse = QGraphicsEllipseItem(0, 0, 300, 300)

            ellipse.setStartAngle(startAngle)
            ellipse.setSpanAngle(angle)
            ellipse.setBrush(self.__getColor(i))
            self.__scene.addItem(ellipse)

            if (angle > 10*16):
                f = self.font()
                textItem = self.__scene.addText(elementText, f)
                x, y = self.__getPenisPos(startAngle, angle, 155)

                xText = 150+x
                yText = 150-y
                if (startAngle+angle/2 > 90*16 and startAngle+angle/2 < 270*16):
                    xText = xText - textItem.boundingRect().width()

                if (startAngle+angle/2 > 0 and startAngle+angle/2 < 180*16):
                    yText = yText - textItem.boundingRect().height()

                textItem.setPos(xText, yText)

            startAngle += angle


class DashboardWidget(QWidget):

    def __init__(self, database, parent=None):
        super(DashboardWidget, self).__init__(parent)

        self.__database = database

        self.__barDashboard = BarDashboardWidget()
        self.__pieDashboardCurrent = PieDashboardWidget()
        self.__pieDashboardLastMon = PieDashboardWidget()

        _lv = QVBoxLayout()
        _lh = QHBoxLayout()

        _lv.addWidget(self.__barDashboard)
        _lv.addLayout(_lh)
        _lh.addWidget(self.__pieDashboardCurrent)
        _lh.addWidget(self.__pieDashboardLastMon)

        self.setLayout(_lv)

        self.__database.databaseChanged.connect(self.refresh)

    def refresh(self):
        monthlyTotal = self.__database.getMonthlyTotal()
        self.__barDashboard.clear()

        for e in reversed(monthlyTotal):
            d = e[0]
            t = e[1]
            self.__barDashboard.addItem(t, d.toString("MMM"))
        self.__barDashboard.redraw()

        today = QDate.currentDate()
        currentMonth = self.__database.getMonthPerCategory(today.year(), today.month())
        self.__pieDashboardCurrent.addItemBatch(currentMonth)
        self.__pieDashboardCurrent.redraw()

        lastMonth = self.__database.getMonthPerCategory(today.addMonths(-1).year() , today.addMonths(-1).month())
        self.__pieDashboardLastMon.addItemBatch(lastMonth)
        self.__pieDashboardLastMon.redraw()
