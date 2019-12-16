from PyQt5.QtWidgets import QWidget, \
    QVBoxLayout, \
    QHBoxLayout, \
    QLabel, \
    QDateEdit, \
    QComboBox, \
    QGroupBox, \
    QLineEdit, \
    QPushButton
from PyQt5.QtCore import pyqtSignal


class Search(QWidget):
    searchChanged = pyqtSignal()

    def __init__(self, parent=None):
        super(Search, self).__init__(parent)

        _layout = QHBoxLayout(self)
        self.setLayout(_layout)
        self.__text = QLineEdit()
        _layout.addWidget(self.__text)

        self.__btnSearch = QPushButton("Search", self)
        _layout.addWidget(self.__btnSearch)

        self.__text.editingFinished.connect(self.searchChanged.emit)
        self.__btnSearch.clicked.connect(self.searchChanged.emit)

    def getSearch(self):
        if self.__text.text() != "":
            return self.__text.text()
        else:
            return None

    def setFocus(self, Qt_FocusReason=None):
        self.__text.setFocus()
        self.__text.selectAll()


class FilterWidget(QWidget):
    filterChanged = pyqtSignal()

    def __init__(self, catList, parent=None):
        super(FilterWidget, self).__init__(parent)

        self.__catList = catList
        self.__drw = DateRangeWidget(self)
        self.__costRangeEdit = CostRangeWidget(self)
        self.__categoryEdit = CategoryFilterWidget(catList, self)

        _layout = QHBoxLayout(self)
        self.setLayout(_layout)
        _layout.addWidget(self.__drw)
        _layout.addWidget(self.__costRangeEdit)
        _layout.addWidget(self.__categoryEdit)

        self.__drw.filterChanged.connect(self.filterChanged.emit)
        self.__costRangeEdit.filterChanged.connect(self.filterChanged.emit)
        self.__categoryEdit.filterChanged.connect(self.filterChanged.emit)

    def getCostRange(self):
        return self.__costRangeEdit

    def getDateRange(self):
        return self.__drw

    def getCategoryEdit(self):
        return self.__categoryEdit

    def setCategoryModel(self, model):
        self.__categoryEdit.setCategoryModel(model)


class DateRangeWidget(QGroupBox):
    filterChanged = pyqtSignal()

    def __init__(self, parent=None):
        super(DateRangeWidget, self).__init__(parent)

        _layout = QHBoxLayout(self)
        self.setLayout(_layout)

        self.setTitle("Date Range")
        self.setCheckable(True)

        _layout1 = QVBoxLayout(self)
        self.__labelStartDate = QLabel("Start")
        self.__startDateEdit = QDateEdit()

        _layout2 = QVBoxLayout(self)
        self.__labelEndDate = QLabel("End")
        self.__endDateEdit = QDateEdit()

        _layout1.addWidget(self.__labelStartDate)
        _layout1.addWidget(self.__startDateEdit)
        _layout2.addWidget(self.__labelEndDate)
        _layout2.addWidget(self.__endDateEdit)
        _layout.addLayout(_layout1)
        _layout.addLayout(_layout2)

        self.toggled.connect(self.filterChanged.emit)
        self.__startDateEdit.editingFinished.connect(self.filterChanged.emit)
        self.__endDateEdit.editingFinished.connect(self.filterChanged.emit)

    def getMinDate(self):
        if (self.isChecked()):
            return self.__startDateEdit.date()
        else:
            return None

    def getMaxDate(self):
        if (self.isChecked()):
            return self.__endDateEdit.date()
        else:
            return None


class CostRangeWidget(QGroupBox):
    filterChanged = pyqtSignal()

    def __init__(self, parent=None):
        super(CostRangeWidget, self).__init__(parent)

        _layout = QHBoxLayout(self)
        self.setLayout(_layout)

        self.setTitle("Cost Range")
        self.setCheckable(True)

        _layout1 = QVBoxLayout(self)
        self.__labelStartCost = QLabel("Min")
        self.__startCostEdit = QLineEdit()

        _layout2 = QVBoxLayout(self)
        self.__labelEndCost = QLabel("Max")
        self.__endCostEdit = QLineEdit()

        _layout1.addWidget(self.__labelStartCost)
        _layout1.addWidget(self.__startCostEdit)
        _layout2.addWidget(self.__labelEndCost)
        _layout2.addWidget(self.__endCostEdit)
        _layout.addLayout(_layout1)
        _layout.addLayout(_layout2)

        self.toggled.connect(self.filterChanged.emit)
        self.__startCostEdit.editingFinished.connect(self.filterChanged.emit)
        self.__endCostEdit.editingFinished.connect(self.filterChanged.emit)

    def getCostMin(self):
        if self.isChecked():
            f = 0.0
            try:
                f = float(self.__startCostEdit.text())
            except:
                return None
            return f
        else:
            return None

    def getCostMax(self):
        if (self.isChecked()):
            f = 0.0
            try:
                f = float(self.__endCostEdit.text())
            except:
                return None
            return f
        else:
            return None


class CategoryFilterWidget(QGroupBox):
    filterChanged = pyqtSignal()

    def __init__(self, catListModel, parent=None):
        super(CategoryFilterWidget, self).__init__(parent)

        self.setTitle("Category")
        self.setCheckable(True)

        _layout = QVBoxLayout()
        self.setLayout(_layout)

        self.__catListEdit = QComboBox(self)
        self.__catListEdit.setModel(catListModel)
        self.__catListEdit.setModelColumn(1)
        _layout.addWidget(self.__catListEdit)

        self.toggled.connect(self.filterChanged.emit)
        self.__catListEdit.currentIndexChanged.connect(self.filterChanged.emit)

    def setCategoryModel(self, model):
        self.__catListEdit.setModel(model)

    def getCategory(self):
        if (self.isChecked()):
            i = self.__catListEdit.currentIndex()
            if (i >= 0):
                return self.__catListEdit.model().getItem(i).getId()
        return None