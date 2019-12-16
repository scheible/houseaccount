from datetime import date
from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt, QDate, QObject, pyqtSignal, QThread
from PyQt5.QtSql import QSqlDatabase, QSqlQuery, QSql
from PyQt5.QtWidgets import QErrorMessage
import xlrd


class Importer(QObject):
    finished = pyqtSignal()
    tick = pyqtSignal(int)

    def __init__(self, fileName, db, parent=None):
        super(Importer, self).__init__(parent)
        self.stop = False
        self.tickCounter = 0

        self.__fileName = fileName
        self.__itemSheetIndex = 0
        self.__categorySheetIndex = 1
        self.__itemColumnIndex = {
            'date': 0,
            'cost': 1,
            'cat_id': 2,
            'cat_text': 3,
            'comment': 4}
        self.__catColumnIndex = {
            'cat_id': 0,
            'cat_text': 1}
        self.__isOpen = False

        self.__db = db

        self.__book = None
        self.__sheetItems = None
        self.__sheetCategories = None

    def open(self):
        if (not self.__isOpen):
            self.__book = xlrd.open_workbook(self.__fileName, encoding_override="utf-8")
            self.__sheetItems = self.__book.sheet_by_index(self.__itemSheetIndex)
            self.__sheetCategories = self.__book.sheet_by_index(self.__categorySheetIndex)
            self.__isOpen = True

    def getNumberOfItems(self):
        if (self.__isOpen):
            return self.__sheetItems.nrows + self.__sheetCategories.nrows
        else:
            return 0

    def __dateFromExcelValue(self, excelValue, datemode):
        if (excelValue == ""):
            return date(1990,1,1)
        year, month, day, hour, minute, second = xlrd.xldate_as_tuple(excelValue, datemode)
        return QDate(year, month, day)

    def loadCategories(self):
        for i in range(0, self.__sheetCategories.nrows):
            id = int(self.__sheetCategories.cell(i, self.__catColumnIndex['cat_id']).value)
            text = self.__sheetCategories.cell(i, self.__catColumnIndex['cat_text']).value

            if (text != ""):
                cat = Category(id, text)
                self.__db.addCategory(cat)

            self.ticker()
            if (self.stop):
                break

    def loadItems(self):
        for i in range(1, self.__sheetItems.nrows):
            dVal = self.__sheetItems.cell(i, self.__itemColumnIndex['date']).value
            cost = self.__sheetItems.cell(i, self.__itemColumnIndex['cost']).value
            catId = self.__sheetItems.cell(i, self.__itemColumnIndex['cat_id']).value
            comment = self.__sheetItems.cell(i, self.__itemColumnIndex['comment']).value

            if (cost != "" and dVal != ""):
                print("->:", dVal, cost, catId, comment, end="")
                d = self.__dateFromExcelValue(dVal, self.__book.datemode)
                catId = int(catId)
                cat = Category(catId, 'dummy')
                if (cat != None):
                    print(" adding...", end="")
                    item = SpendingItem(None, cost, d, cat, comment)
                    item.setCategoryId(catId)
                    self.__db.addSpendingItem(item, False)
                print()

            self.ticker()
            if (self.stop):
                break

        self.__db.databaseChanged.emit()

    def ticker(self):
        self.tickCounter += 1
        self.tick.emit(self.tickCounter)

    def cancel(self):
        self.stop = True

    def run(self):
        self.loadCategories()
        self.loadItems()
        self.finished.emit()


class Category:

    def __init__(self, id: int, name: str):
        self.__id = id
        self.__name = name

    def getName(self):
        return self.__name

    def getId(self):
        return self.__id

    def hasId(self):
        if (self.__id == None):
            return False
        else:
            return True

    def setName(self, name: str):
        self.__name = name


class SpendingItem:

    def __init__(self, id, cost: float, d: QDate, category: str, comment: str):
        self.__cost = 0
        self.setCost(cost)
        self.__category = category
        self.__comment = comment
        self.__date = d
        self.__id = id
        self.__catId = None

    def __str__(self):
        return self.__date.toString(Qt.ISODate) + ";" + str(self.__cost) + ";" + self.__category + ";" + self.__comment

    def hasId(self):
        if (self.__id == None):
            return False
        else:
            return True

    def getCategoryId(self):
        return self.__catId

    def setCategoryId(self, id):
        self.__catId = id

    def getId(self):
        return self.__id

    def getDate(self):
        return self.__date

    def getCost(self):
        return self.__cost

    def getCategory(self):
        return self.__category

    def getComment(self):
        return self.__comment

    def setDate(self, d: QDate):
        self.__date = d

    def setCost(self, cost: float):
        if (cost >= 0):
            self.__cost = round(cost, 2)

    def setCategory(self, cat):
        self.__category = cat

    def setComment(self, c):
        self.__comment = c


class SqlSpendingItem(SpendingItem):

    def __init__(self, query: QSqlQuery):
        self.__id = query.value("id")
        self.__cost = query.value("cost")
        self.__date = QDate.fromString(query.value("date"), Qt.ISODate)
        self.__category = query.value("catName")
        self.__comment = query.value("comment")
        super(SqlSpendingItem, self).__init__(self.__id, self.__cost, self.__date, self.__category, self.__comment)


class CategoryList(QAbstractTableModel):

    def __init__(self, parent=None):
        super(CategoryList, self).__init__(parent)

        self.__categoryList = []

    def rowCount(self, parent: QModelIndex):
        return len(self.__categoryList)

    def columnCount(self, parent: QModelIndex):
        return 2

    def data(self, index: QModelIndex, role):
        if (role == Qt.DisplayRole):
            col = index.column()
            row = index.row()
            item: Category = self.__getItem(row)
            if (item != None):
                if (col == 0):
                    return str(item.getId())
                elif (col == 1):
                    return item.getName()
                else:
                    return ""
        else:
            return None

    def addItem(self, c: Category):
        self.__categoryList.append(c)
        self.layoutChanged.emit()

    def __getItem(self, index: int):
        if (index >= 0 and index < len(self.__categoryList)):
            return self.__categoryList[index]
        else:
            return None

    def findRowIndexOfCategoryId(self, catId: int):
        for index, e in enumerate(self.__categoryList):
            if (e.getId() == catId):
                return index
        return -1

    def findCategory(self, id: int):
        for e in self.__categoryList:
            if (e.getId() == id):
                return e
        return None

    def getItem(self, index: int):
        return self.__getItem(index)

    def clear(self):
        self.__categoryList.clear()
        self.layoutChanged.emit()


class ItemList(QAbstractTableModel):

    def __init__(self, parent=None):
        super(ItemList, self).__init__(parent)

        self.__dataList = []

    def rowCount(self, parent: QModelIndex):
        return len(self.__dataList)

    def columnCount(self, parent: QModelIndex):
        return 4

    def data(self, index: QModelIndex, role):
        if (role == Qt.DisplayRole):
            col = index.column()
            row = index.row()
            item: SpendingItem = self.getItem(row)
            if (item != None):
                if (col == 0):
                    return item.getDate().toString(Qt.ISODate)
                elif (col == 1):
                    return str(item.getCost()) + " €"
                elif (col == 2):
                    return item.getCategory()
                elif (col == 3):
                    return item.getComment()
                else:
                    return ""
        else:
            return None

    def headerData(self, section, orientation, role):
        headers = ['Date', 'Cost', 'Category', 'Comment']

        if (role == Qt.DisplayRole):
            if(orientation == 1):
                if (section < len(headers)):
                    return headers[section]
                else:
                    return "-"
            elif (orientation == 2):
                return str(section+1)

    def getItem(self, index: int):
        if (index >= 0 and index < len(self.__dataList)):
            return self.__dataList[index]
        else:
            return None

    def addItem(self, item: SpendingItem):
        self.__dataList.append(item)
        self.layoutChanged.emit()

    def findItem(self, index: QModelIndex):
        return self.getItem(index.row())

    def clear(self):
        self.__dataList.clear()
        self.layoutChanged.emit()


class Database(QObject):
    databaseChanged = pyqtSignal()
    filtersChanged = pyqtSignal()

    def __init__(self, parent=None):
        super(Database, self).__init__(parent)

        self.__isOpen = False
        self.__fileName = ""
        self.__driver = "QSQLITE"
        self.__db = QSqlDatabase.addDatabase(self.__driver)

        self.__filterDateMin = None
        self.__filterDateMax = None
        self.__filterCostMin = None
        self.__filterCostMax = None
        self.__filterCat  = None
        self.__filterComment = None

    def getConnection(self):
        return self.__db

    def getFileName(self):
        return self.__db.databaseName()

    def isOpen(self):
        return self.__db.isOpen()

    def setCostFilter(self, min, max):
        self.__filterCostMin = min
        self.__filterCostMax = max
        self.filtersChanged.emit()

    def setDateFilter(self, min, max):
        self.__filterDateMin = min
        self.__filterDateMax = max
        self.filtersChanged.emit()

    def setCategoryFilter(self, id):
        self.__filterCat = id
        self.filtersChanged.emit()

    def setCommentFilter(self, c):
        self.__filterComment = c
        self.filtersChanged.emit()

    def createEmptyDatabase(self, fileName):
        self.__db.setDatabaseName(fileName)
        self.__db.open()

        query = QSqlQuery()
        query.exec("CREATE TABLE category (id integer primary key, name varchar(40));")
        query.exec("CREATE TABLE spendingItem (id integer primary key, date date, cost float, categoryId int, comment varchar(70));")

    def openDatabase(self, fileName):
        if (self.__db.isOpen()):
            self.__db.close()

        self.__db.setDatabaseName(fileName)
        self.__db.open()

        if (not self.__db.isOpen()):
            e = QErrorMessage()
            e.showMessage("Could not open database")
        else:
            self.databaseChanged.emit()

    def addSpendingItem(self, s: SpendingItem, triggerEvent=True):
        if (not self.__db.isOpen()):
            return False

        query = QSqlQuery(self.__db)
        if (not s.hasId()):
            query.prepare("INSERT INTO spendingItem (date, cost, categoryId, comment) VALUES (:date, :cost, :catId, :comment);")
        else:
            query.prepare(("INSERT INTO spendingItem (id, date, cost, categoryId, comment) VALUES (:id, :date, :cost, :catId, :comment);"))
            query.bindValue(":id", s.getId())
        query.bindValue(":date", s.getDate().toString(Qt.ISODate))
        query.bindValue(":cost", s.getCost())
        query.bindValue(":catId", s.getCategoryId())
        query.bindValue(":comment", s.getComment())

        if (not query.exec()):
            return False

        if (triggerEvent):
            self.databaseChanged.emit()
        return True

    def updateSpendingItem(self, s: SpendingItem):
        if (not self.__db.isOpen()):
            return False

        if (not s.hasId()):
            return False

        query = QSqlQuery(self.__db)
        query.prepare("UPDATE spendingItem SET date = :date, cost = :cost, categoryId = :catId, comment = :comment WHERE id = :id;")
        query.bindValue(":id", s.getId())
        query.bindValue(":date", s.getDate())
        query.bindValue(":cost", s.getCost())
        query.bindValue(":catId", s.getCategoryId())
        query.bindValue(":comment", s.getComment())

        if (not query.exec()):
            return False

        self.databaseChanged.emit()
        return True

    def deleteListOfSpendingItems(self, listOfIDs):
        queryString = "DELETE FROM spendingItem WHERE id IN ("
        for id in listOfIDs[:-1]:
                queryString += str(id) + ","

        queryString += str(listOfIDs[len(listOfIDs)-1]) + ");"
        query = QSqlQuery(self.__db)
        query.prepare(queryString)
        if (not query.exec()):
            print(query.lastError().text())
            return False

        self.databaseChanged.emit()
        return True

    def deleteSpendingItem(self, s: SpendingItem):
        if (not self.__db.isOpen()):
            return False

        query = QSqlQuery(self.__db)
        query.prepare("DELETE FROM spendingItem WHERE id = :id;")
        query.bindValue(":id", s.getId())
        if (not query.exec()):
            return False

        self.databaseChanged.emit()
        return True

    def addCategory(self, c: Category):
        if (self.__db.isOpen()):
            query = QSqlQuery(self.__db)
            if (not c.hasId()):
                query.prepare("INSERT INTO category (name) VALUES (:name);")
            else:
                query.prepare("INSERT INTO category (id, name) VALUES (:id, :name);")
                query.bindValue(":id", c.getId())
            query.bindValue(":name", c.getName())

            if (not query.exec()):
                return False
            else:
                self.databaseChanged.emit()
                return True
        else:
            return False

    def __getQueryString(self):
        qBaseString = "SELECT s.id as id, s.date as date, s.cost as cost, c.name as catName, " \
                      "s.comment as comment FROM spendingItem as s, Category as c WHERE c.id = s.categoryId"

        if (self.__filterCostMin != None):
            qCostMinFilter = " AND cost >= "+str(self.__filterCostMin)
        else:
            qCostMinFilter = ""

        if (self.__filterCostMax != None ):
            qCostMaxFilter = " AND cost <= "+str(self.__filterCostMax)
        else:
            qCostMaxFilter = ""

        if (self.__filterDateMin != None):
            qDateMinFilter = " AND date >= '" + self.__filterDateMin.toString(Qt.ISODate) + "'"
        else:
            qDateMinFilter = ""

        if (self.__filterDateMax != None):
            qDateMaxFilter = " AND date <= '" + self.__filterDateMax.toString(Qt.ISODate) + "'"
        else:
            qDateMaxFilter = ""

        if (self.__filterCat != None):
            qCategoryFilter = " AND c.id = " + str(self.__filterCat)
        else:
            qCategoryFilter = ""

        if (self.__filterComment != None):
            qCommentFilter = " AND s.comment LIKE '%" + self.__filterComment + "%'"
        else:
            qCommentFilter = ""

        return qBaseString + qCostMinFilter + qCostMaxFilter + \
               qDateMinFilter + qDateMaxFilter + qCategoryFilter + qCommentFilter + " ORDER BY date DESC;"

    def getSpendingItems(self, itemList: ItemList):
        if (not self.__db.isOpen()):
            return None

        query = QSqlQuery(self.__db)
        query.prepare(self.__getQueryString())

        query.exec()
        while (query.next()):
            sItem = SqlSpendingItem(query)
            itemList.addItem(sItem)

    def getCategories(self, catList: CategoryList):
        query = QSqlQuery(self.__db)
        query.exec("SELECt id, name FROM category;")

        while(query.next()):
            c = Category(query.value("id"), query.value("name"))
            catList.addItem(c)

    def close(self):
        self.__db.close()

    def getMonthlyTotal(self, limit=15):
        sqlString = "SELECT SUM(cost) as total, strftime('%Y', date) as year, strftime('%m', date) as month " \
                    "FROM spendingItem " \
                    "GROUP BY year, month " \
                    "ORDER BY year DESC, month DESC " \
                    "LIMIT :limit;" \

        query = QSqlQuery(self.__db)
        query.prepare(sqlString)
        query.bindValue(":limit", limit)
        query.exec()

        items = []


        while (query.next()):
            total = query.value("total")
            year = query.value("year")
            month = query.value("month")
            date = QDate(int(year), int(month), 1)
            items.append([date, total])

        return items

    def getMonthPerCategory(self, year, month):
        sqlString = "SELECT SUM(cost) as total, " \
                    "category.name, strftime('%Y', date) as year, strftime('%m', date) as month " \
                    "FROM spendingItem, Category " \
                    "WHERE year = :year AND month = :month AND categoryId = category.id " \
                    "GROUP BY categoryId;"

        query = QSqlQuery()
        query.prepare(sqlString)
        query.bindValue(":year", str(year))
        query.bindValue(":month", str(month))

        query.exec()

        values = []
        while(query.next()):
            spending = query.value("total")
            name = query.value("name")
            values.append([spending, name])

        return values
