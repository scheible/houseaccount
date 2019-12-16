import math

from PyQt5.QtSql import QSqlDatabase
from PyQt5.QtWidgets import QWidget, \
    QTableView, \
    QVBoxLayout, \
    QHBoxLayout, \
    QLabel, \
    QDateEdit, \
    QComboBox, \
    QGroupBox, \
    QAction, QMainWindow, QMenu, QLineEdit, QPushButton, QAbstractItemView, QDialog, QFormLayout, QFileDialog, \
    QTabWidget, QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsRectItem, QCheckBox, \
    QSpacerItem, QSizePolicy, QProgressBar
from PyQt5.QtCore import Qt, pyqtSignal, QModelIndex, QDate, QSettings, QThread
from PyQt5.QtGui import QKeySequence, QValidator, QKeyEvent, QColor, QPainter, QLinearGradient, QPen, QPalette
from dataObjects import ItemList, SpendingItem, Category, Importer, CategoryList, Database
from filterWidget import *
from dashboardWidgets import *
import sys
import os.path


class ImportWidget(QDialog):
    def __init__(self, database, parent=None):
        super(ImportWidget, self).__init__(parent)
        self.setGeometry(100, 100, 500, 200)
        self.setWindowTitle("Import Data")
        self.setModal(True)

        self.__database = database

        _lv = QVBoxLayout()
        self.setLayout(_lv)

        _lh = QHBoxLayout()

        self.__lblFileName = QLabel("File name:")
        self.__txtFileName = QLineEdit()
        self.__btnLoad = QPushButton("load")

        _lh.addWidget(self.__lblFileName)
        _lh.addWidget(self.__txtFileName)
        _lh.addWidget(self.__btnLoad)

        _lv.addLayout(_lh)

        self.__chkIgnoreDups = QCheckBox("Ignore exact duplicates")
        _lv.addWidget(self.__chkIgnoreDups)

        _lh2 = QHBoxLayout()
        _lh2.addStretch(10)
        self.__btnCancel = QPushButton("cancel")
        self.__btnCancel.setEnabled(False)
        self.__btnImport = QPushButton("import")
        self.__btnImport.setEnabled(False)
        self.__btnImport.setFixedWidth(80)
        _lh2.addWidget(self.__btnCancel)
        _lh2.addWidget(self.__btnImport)
        _lv.addLayout(_lh2)

        self.__progressBar = QProgressBar()
        _lv.addWidget(self.__progressBar)

        _lh3 = QHBoxLayout()
        _lh3.addStretch(10)
        self.__btnClose = QPushButton("close")

        _lh3.addWidget(self.__btnClose)
        _lv.addLayout(_lh3)

        self.__progressBar.setMinimum(0)
        self.__progressBar.setMaximum(100)
        self.__progressBar.setValue(0)

        self.__btnImport.clicked.connect(self.import_clicked)
        self.__btnClose.clicked.connect(self.close_clicked)
        self.__btnLoad.clicked.connect(self.load_clicked)
        self.__txtFileName.editingFinished.connect(self.txtFilename_changed)
        self.__txtFileName.textChanged.connect(self.txtFilename_changed)
        self.__btnCancel.clicked.connect(self.cancel_clicked)

        self.__controlGroup1 = [self.__txtFileName, self.__btnImport, self.__btnLoad, self.__btnClose, self.__chkIgnoreDups]

    def txtFilename_changed(self):
        palette = QPalette()
        palette.setColor(QPalette.Base, Qt.white)
        palette.setColor(QPalette.Text, Qt.black)

        paletteRed = QPalette()
        paletteRed.setColor(QPalette.Base, Qt.white)
        paletteRed.setColor(QPalette.Text, Qt.red)

        fileName = self.__txtFileName.text()
        if os.path.isfile(fileName):
            self.__btnImport.setEnabled(True)
            self.__txtFileName.setPalette(palette)
        else:
            self.__btnImport.setEnabled(False)
            self.__txtFileName.setPalette(paletteRed)

    def load_clicked(self):
        d = QFileDialog(self)
        fileName, type = d.getOpenFileName()

        if (fileName != ""):
            self.__txtFileName.setText(fileName)

    def close_clicked(self):
        self.close()

    def tick(self, step):
        self.__progressBar.setValue(step)

    def import_clicked(self):
        for c in self.__controlGroup1:
            c.setEnabled(False)
        self.__btnCancel.setEnabled(True)

        self.thread = QThread()
        self.importWorker = Importer(self.__txtFileName.text(), self.__database)
        self.importWorker.open()
        self.__progressBar.setMaximum(self.importWorker.getNumberOfItems()-1)
        self.importWorker.moveToThread(self.thread)
        self.thread.started.connect(self.importWorker.run)
        self.importWorker.finished.connect(self.thread.quit)
        self.importWorker.tick.connect(self.tick)
        self.importWorker.finished.connect(self.import_done)
        self.thread.start()

    def import_done(self):
        for c in self.__controlGroup1:
            c.setEnabled(True)
        self.__btnCancel.setEnabled(False)
        self.__database.databaseChanged.emit()

    def cancel_clicked(self):
        self.importWorker.cancel()


class SpendingItemWidget(QDialog):

    def __init__(self, categoryList: CategoryList, parent=None):
        super(SpendingItemWidget, self).__init__(parent)

        self.__categoryList = categoryList

        self.setGeometry(100, 100, 500, 200)
        self.setWindowTitle("New Item")
        self.setModal(True)

        self.__outerLayout = QVBoxLayout()
        self.setLayout(self.__outerLayout)

        self.__layout = QFormLayout()
        self.__buttonLayout = QHBoxLayout()

        self.__outerLayout.addLayout(self.__layout)
        self.__outerLayout.addLayout(self.__buttonLayout)

        self.__lblDate = QLabel('Date')
        self.__dtDate = QDateEdit(QDate.currentDate())
        self.__dtDate.setFixedWidth(120)
        self.__layout.addRow(self.__lblDate, self.__dtDate)

        self.__lblCost = QLabel('Cost')
        self.__txtCost = QLineEdit()
        self.__txtCost.setFixedWidth(120)
        self.__layout.addRow(self.__lblCost, self.__txtCost)

        self.__lblCategory = QLabel('Category')
        self.__cbxCategory = QComboBox()
        self.__layout.addRow(self.__lblCategory, self.__cbxCategory)
        self.__cbxCategory.setModel(self.__categoryList)
        self.__cbxCategory.setModelColumn(1)

        self.__lblComment= QLabel('Comment')
        self.__txtComment = QLineEdit()
        self.__layout.addRow(self.__lblComment, self.__txtComment)

        self.__okButton = QPushButton("Ok")
        self.__cancelButton = QPushButton("Cancel")
        self.__buttonLayout.addWidget(self.__okButton)
        self.__buttonLayout.addWidget(self.__cancelButton)

        self.__okButton.clicked.connect(self.ok_click)
        self.__cancelButton.clicked.connect(self.cancel_click)

        self.__item: SpendingItem = None

        self.__txtCost.setFocus()

    def __getCost(self):
        costTxt = self.__txtCost.text()
        costTxt = costTxt.replace(",",".")
        cost = float(''.join(c for c in costTxt if (c.isdigit() or c == '.')))
        return cost

    def __getCategory(self):
        index = self.__cbxCategory.currentIndex()
        cID = self.__categoryList.getItem(index).getId()
        return cID

    def editSpendingItem(self, item: SpendingItem):
        self.__dtDate.setDate(item.getDate())
        self.__txtCost.setText(str(item.getCost()) + " €")
        self.__cbxCategory.setCurrentText(item.getCategory())
        self.__txtComment.setText(item.getComment())
        result = self.exec()
        if (result == QDialog.Accepted):
            item = SpendingItem(item.getId(), self.__getCost(), self.__dtDate.date(), "dummyCat", self.__txtComment.text())
            item.setCategoryId(self.__getCategory())
            return item
        else:
            return None

    def getNewSpendingItem(self):
        result = self.exec()
        if (result == QDialog.Accepted):
            item = SpendingItem(None, self.__getCost(), self.__dtDate.date(), "dummyCat", self.__txtComment.text())
            item.setCategoryId(self.__getCategory())
            return item
        else:
            return None

    def ok_click(self):
        self.accept()

    def cancel_click(self):
        print("cancel")
        self.close()


class MyTableView(QTableView):
    enterPressed = pyqtSignal()

    def keyPressEvent(self, event: QKeyEvent):
        if (event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter):
            self.enterPressed.emit()
        else:
            super(MyTableView, self).keyPressEvent(event)


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.__settings = QSettings("houseaccount", "settings")

        self.database = Database()

        _w = QWidget()
        self.setCentralWidget(_w)

        self.__itemList = ItemList()
        self.__catList = CategoryList()
        self.__tabView = QTabWidget()

        self.view = MyTableView()
        self.view.setModel(self.__itemList)
        self.view.verticalHeader().setVisible(False)

        self.__dashboard = DashboardWidget(self.database)

        self.__tabView.addTab(self.view, "Expenses")
        self.__tabView.addTab(self.__dashboard, "Dashboard")

        #TODO: use the proper constant instead of 1 here
        self.view.setSelectionBehavior(1)

        _layout = QVBoxLayout()
        _w.setLayout(_layout)

        self.__search = Search(self)
        self.__search.searchChanged.connect(self.searchChanged)
        self.__filter = FilterWidget(self.__catList, self)
        self.__filter.getCostRange().filterChanged.connect(self.filterCostChanged)
        self.__filter.getDateRange().filterChanged.connect(self.filterDateChange)
        self.__filter.getCategoryEdit().filterChanged.connect(self.filterCategoryChanged)
        self.__filter.getCategoryEdit().setChecked(False)
        self.__filter.getCostRange().setChecked(False)
        self.__filter.getDateRange().setChecked(False)
        self.__filter.setVisible(False)
        self.__search.setVisible(False)

        _layout.addWidget(self.__search)
        _layout.addWidget(self.__filter)
        _layout.addWidget(self.__tabView)

        self.setWindowTitle("House Account")
        self.setGeometry(50, 50, 1000, 500)

        self.view.selectionModel().selectionChanged.connect(self.selectionChanged)

        self.initActions()
        self.initMenu()
        self.initToolbar()

        self.view.enterPressed.connect(self.__actionEditSpendingItem.trigger)
        self.database.databaseChanged.connect(self.databaseChanged)
        self.database.databaseChanged.connect(self.refresh)
        self.database.filtersChanged.connect(self.refresh)

        self.loadSettings()

    def refresh(self):
        self.__itemList.clear()
        self.database.getSpendingItems(self.__itemList)
        self.__catList.clear()
        self.database.getCategories(self.__catList)

    def searchChanged(self):
        s = self.__search.getSearch()
        self.database.setCommentFilter(s)

    def filterDateChange(self):
        min = self.__filter.getDateRange().getMinDate()
        max = self.__filter.getDateRange().getMaxDate()

        self.database.setDateFilter(min, max)

    def filterCategoryChanged(self):
        catId = self.__filter.getCategoryEdit().getCategory()
        self.database.setCategoryFilter(catId)

    def filterCostChanged(self):
        min = self.__filter.getCostRange().getCostMin()
        max = self.__filter.getCostRange().getCostMax()

        self.database.setCostFilter(min, max)

    def selectionChanged(self, selected, deselected):
        rows = self.__selectedRows(self.view.selectedIndexes())

        if (len(rows) <= 0):
            self.__actionDeleteSpendingItem.setEnabled(False)
            self.__actionEditSpendingItem.setEnabled(False)
        if (len(rows) == 1):
            self.__actionEditSpendingItem.setEnabled(True)
            self.__actionDeleteSpendingItem.setEnabled(True)
        if (len(rows) > 1):
            self.__actionEditSpendingItem.setEnabled(False)
            self.__actionDeleteSpendingItem.setEnabled(True)

    def __selectedRows(self, selection):
        rows = []
        for s in selection:
            r = s.row()
            if (not r in rows):
                rows.append(r)
        return rows

    def initActions(self):
        self.__actionOpenDatabase = QAction("&Open Database...")
        self.__actionOpenDatabase.triggered.connect(self.openDatabase)

        self.__actionAddSpendingItem = QAction("New")
        self.__actionAddSpendingItem.setShortcut("Ctrl+N")
        self.__actionAddSpendingItem.triggered.connect(self.new)

        self.__actionEditSpendingItem = QAction("&Edit")
        self.__actionEditSpendingItem.setShortcut("Enter")
        self.__actionEditSpendingItem.triggered.connect(self.edit)

        self.__actionDeleteSpendingItem = QAction("&Delete")
        self.__actionDeleteSpendingItem.setShortcut(QKeySequence(Qt.Key_Delete))
        self.__actionDeleteSpendingItem.triggered.connect(self.delete)

        self.__actionQuit = QAction("Exit")
        self.__actionQuit.setShortcut("Ctrl+W")
        self.__actionQuit.triggered.connect(self.exit)

        self.__actionImport = QAction("&Import")
        self.__actionImport.triggered.connect(self.importData)

        self.__actionExport = QAction("&Export")

        self.__actionSearch = QAction("Search")
        self.__actionSearch.triggered.connect(self.search)
        self.__actionSearch.setShortcut("Ctrl+F")
        self.__actionSearch.setCheckable(True)

        self.__actionFilter = QAction("Filter")
        self.__actionFilter.triggered.connect(self.filter)
        self.__actionFilter.setShortcut("Ctrl+G")
        self.__actionFilter.setCheckable(True)

        self.__actionVerticalHeader = QAction("Line Numbers")
        self.__actionVerticalHeader.triggered.connect(self.lineNumbers)
        self.__actionVerticalHeader.setShortcut("Ctrl+L")
        self.__actionVerticalHeader.setCheckable(True)

    def initMenu(self):
        self.__fileMenu: QMenu = self.menuBar().addMenu("&File")
        self.__fileMenu.addAction(self.__actionOpenDatabase)
        self.__fileMenu.addAction(self.__actionImport)
        self.__fileMenu.addAction(self.__actionExport)
        self.__fileMenu.addAction(self.__actionQuit)

        self.__editMenu: QMenu = self.menuBar().addMenu("&Edit")
        self.__editMenu.addAction(self.__actionAddSpendingItem)
        self.__editMenu.addAction(self.__actionEditSpendingItem)
        self.__editMenu.addAction(self.__actionDeleteSpendingItem)

        self.__viewMenu: QMenu = self.menuBar().addMenu("&View")
        self.__viewMenu.addAction(self.__actionSearch)
        self.__viewMenu.addAction(self.__actionFilter)
        self.__viewMenu.addAction(self.__actionVerticalHeader)

    def initToolbar(self):
        self.toolbar = self.addToolBar('Functions')
        self.toolbar.addAction(self.__actionAddSpendingItem)
        self.toolbar.addAction(self.__actionEditSpendingItem)
        self.toolbar.addAction(self.__actionDeleteSpendingItem)

    def openDatabase(self):
        d = QFileDialog()

        fileName, type = d.getOpenFileName()
        print(fileName)
        if (fileName != ""):
            self.__itemList.clear()
            self.__catList.clear()
            self.database.openDatabase(fileName)
            self.database.getSpendingItems(self.__itemList)
            self.database.getCategories(self.__catList)

    def importData(self):
        dialog = ImportWidget(self.database, self)
        dialog.show()

    def edit(self):
        if not self.__actionEditSpendingItem.isEnabled():
            return

        selectedIndex = self.view.currentIndex()
        item = self.__itemList.findItem(selectedIndex)

        self.dialog = SpendingItemWidget(self.__catList)
        editedItem = self.dialog.editSpendingItem(item)
        if (editedItem != None):
            self.database.updateSpendingItem(editedItem)

    def lineNumbers(self):
        v = self.view.verticalHeader().isVisible()
        self.view.verticalHeader().setVisible(not v)
        self.__actionVerticalHeader.setChecked(not v)

    def filter(self):
        v = self.__filter.isVisible()
        self.__filter.setVisible(not v)
        self.__actionFilter.setChecked(not v)
        self.__filter.setFocus()

    def search(self):
        v = self.__search.isVisible()
        self.__search.setVisible(not v)
        self.__actionSearch.setChecked(not v)

        if (not v):
            self.__search.setFocus()

    def exit(self):
        self.database.close()
        self.saveSettings()
        sys.exit(0)

    def new(self):
        d = SpendingItemWidget(self.__catList, self)
        item = d.getNewSpendingItem()
        if (item != None):
            self.database.addSpendingItem(item)

    def delete(self):
        rows = self.__selectedRows(self.view.selectedIndexes())
        itemIdsToDelete = []

        for index in rows:
            item = self.__itemList.getItem(index)
            if (item != None):
                itemIdsToDelete.append(item.getId())

        self.database.deleteListOfSpendingItems(itemIdsToDelete)
        self.refresh()
        self.view.selectionModel().clear()

    def databaseChanged(self):
        if self.database.isOpen():
            self.__actionAddSpendingItem.setEnabled(True)
            self.__filter.setEnabled(True)
            self.__search.setEnabled(True)
            self.view.setEnabled(True)
            self.__actionImport.setEnabled(True)
            self.__actionExport.setEnabled(True)
        else:
            self.__actionAddSpendingItem.setEnabled(False)
            self.__filter.setEnabled(False)
            self.__search.setEnabled(False)
            self.__actionEditSpendingItem.setEnabled(False)
            self.__actionDeleteSpendingItem.setEnabled(False)
            self.view.setEnabled(False)
            self.__actionImport.setEnabled(False)
            self.__actionExport.setEnabled(False)

    def loadSettings(self):
        fileName = self.__settings.value("databaseFile")
        if (fileName != ""):
            self.database.openDatabase(fileName)

    def saveSettings(self):
        self.__settings.setValue("databaseFile", self.database.getFileName())
        self.__settings.sync()
