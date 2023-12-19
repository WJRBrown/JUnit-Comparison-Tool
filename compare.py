import xml.etree.ElementTree as ET
import os
import sys
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

class ParseJUnit():
    def __init__(self, path):
        self.path = path
        self.tree = ET.parse(self.path)
        self.root = self.tree.getroot()
    
    def getResults(self):
        """
        The resulting data takes the form of: 
        {testsuite: [[testcase, pass/fail, symbol, highlight], [testcase2, pass/fail, symbol, highlight]]}
        """
        results = {}
        for suite in self.root:
            children = []
            for testcase in suite:
                if testcase.find('failure') in testcase:
                    children.append([testcase.attrib['name'], True, None, False])
                else:
                    children.append([testcase.attrib['name'], False, None, False])
                children.sort()
            results[suite.attrib['name']] = children
        return results
    
    @staticmethod
    def diff_data(data, data2):
        """
        Method to compare the JUnit files + add blank spaces / symbols / highlights. 
        We iterate through both sets of data and add empty data / symbols / highlight 
        flags to the data lists where appropriate. Returns edited dictionary.
        """
        blank_spaces = []
        for idx, key in enumerate(data.keys()):
            if key not in data2.keys():
                new_tree = list(data2.items())
                new_tree.insert(idx, (key, [[' ', None, "-", True]])) 
                new_tree.sort() 
                data2 = dict(new_tree)
                for i, case in enumerate(data[key]):
                    if i == 0:
                        case[2] = "+"
                        case[3] = True
                    else:
                        case[2] = "+"
                        case[3] = True
                        blank_spaces.append((key, (idx, [" ", None, "-", True])))
            else:
                other_tests = [test[0] for test in data2[key]]
                for i, case in enumerate(data[key]):
                    if case[0] not in other_tests:
                        if case[0] != " ":
                            print(case[0])
                            print(other_tests)
                            case[2] = "+"
                            case[3] = True
                            data2[key].insert(i, [' ', None, "-", True])
                    else:
                        if case[1] != data2[key][i][1]:
                            case[3] = True

        for blank in blank_spaces:
            data2[blank[0]].insert(*blank[1])

        return data2
    
    @staticmethod
    def pure_diff(data, data2):
        pure_data = {}
        for key in data.keys():
            for i, case in enumerate(data[key]):
                if case[1] != data2[key][i][1]:
                    pure_data.update(key)

        return pure_data 

class LoadView(QWidget):
    def __init__(self):
        super(LoadView, self).__init__()
        self.index = 0
        self.tree = QTreeWidget()
        self.tree.setColumnCount(3)
        self.tree.setHeaderLabels(['Test', 'Result', 'Error'])
        self.tree.setColumnWidth(0, 175)
        self.tree.setColumnWidth(1, 50)
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.tree)
        self.setLayout(self.layout)

    def clear(self):
        self.tree.clear()

    def getTreeWidgets(self):
        return [self.tree]

class CompareTree(QWidget):
    def __init__(self):
        super(CompareTree, self).__init__()
        self.state = {}
        self.index = 1
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tree = QTreeWidget()
        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels(['Test', ' ', 'Result'])
        self.tree.setColumnWidth(0, 175)
        self.tree.setColumnWidth(1, 20)
        self.tree.setColumnWidth(2, 50)
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.tree)
        self.setLayout(self.layout)

class SetupView(QWidget):
    def __init__(self, parent):
        super(SetupView, self).__init__(parent)
        self.parent = parent
        self.setWindowTitle("Compare JUnit XML's")
        #self.setMinimumSize(400, 200)
        #self.setBaseSize(50, 50)
        self.left_button = QPushButton("Left")
        self.right_button = QPushButton("Right")
        self.left_filepath = QLineEdit()
        self.right_filepath = QLineEdit()
        self.compare = QPushButton("Compare")
        
        self.layout = QVBoxLayout()
        self.buttons = QGridLayout()
        self.buttons.addWidget(self.left_button, 0, 0)
        self.buttons.addWidget(self.left_filepath, 0, 1)
        self.buttons.addWidget(self.right_button, 1, 0)
        self.buttons.addWidget(self.right_filepath, 1, 1)
        self.layout.addLayout(self.buttons)
        self.layout.addWidget(self.compare)
        self.setLayout(self.layout)

        self.left_button.clicked.connect(lambda: self.load_xml(self.left_filepath))
        self.right_button.clicked.connect(lambda: self.load_xml(self.right_filepath))
        self.compare.clicked.connect(self.compare_files)

    def load_xml(self, widget):
        response = QFileDialog.getOpenFileName(
            parent=self,
            caption='Select an JUnit XML file',
            dir=os.getcwd(),
            filter = "xml(*.xml)"
        )
        widget.setText(response[0])

    def compare_files(self):
        file1 = self.left_filepath.text()
        file2 = self.right_filepath.text()

        if file1 and file2:
            self.parent.switch_layout()
            self.parent.tree.load_data(file1, file2)


class TreeView(QWidget):
    def __init__(self, parent):
        super(TreeView, self).__init__(parent)
        self.left_tree = CompareTree()
        self.right_tree = CompareTree()
        self.return_button = QPushButton("Back")
        scroll1 = self.left_tree.tree.verticalScrollBar()
        scroll2 = self.right_tree.tree.verticalScrollBar()
        scroll1.valueChanged.connect(lambda: scroll2.setValue(scroll1.value()))
        scroll2.valueChanged.connect(lambda: scroll1.setValue(scroll2.value()))

        self.main_layout = QVBoxLayout()
        self.layout = QHBoxLayout()
        self.layout.addWidget(self.left_tree)
        self.layout.addWidget(self.right_tree)
        self.main_layout.addLayout(self.layout)
        self.main_layout.addWidget(self.return_button)
        self.setLayout(self.main_layout)

        self.return_button.clicked.connect(self.clear_trees)
        self.return_button.clicked.connect(parent.switch_layout)

    def clear_trees(self):
        self.left_tree.tree.clear()
        self.right_tree.tree.clear()

    def load_data(self, file1, file2):
        self.left_tree.label.setText(os.path.basename(file1))
        self.right_tree.label.setText(os.path.basename(file2))

        self.left_tree.state = self.read_junit(file1)
        self.right_tree.state = self.read_junit(file2)

        self.update_tree(self.left_tree)
        self.update_tree(self.right_tree)

        self.right_tree.state = ParseJUnit.diff_data(self.left_tree.state, self.right_tree.state)
        self.left_tree.state = ParseJUnit.diff_data(self.right_tree.state, self.left_tree.state)

        self.update_tree(self.right_tree)
        self.update_tree(self.left_tree)

    def read_junit(self, path):
        junit = ParseJUnit(path)
        results = junit.getResults()
        return results

    def update_tree(self, tree):
        """
        Nested loop through each testsuite + testcase and updates tree element.
        """
        tree.tree.clear()
        for key in tree.state.keys():
            for idx, case in enumerate(tree.state[key]):
                test = case[0]
                result = case[1]
                symbol = case[2]
                highlight = case[3]
                self.update_tree_element(tree.tree, key, test, idx, result, symbol, highlight) 

    def update_tree_element(self, tree, suite, case, idx, result, symbol=None, highlight=False):
        """
        Check to add to or create new parent test suite entry
        """
        if len(tree.findItems(suite, Qt.MatchFlag.MatchContains)) < 1:
            parent = QTreeWidgetItem(tree)
            parent.setText(0, suite)
        else:
            parent = tree.findItems(suite, Qt.MatchFlag.MatchContains)[0] 

        """
        Adding child test cases to correct position
        """     
        child = QTreeWidgetItem()
        child.setText(0, case)
        parent.insertChild(idx, child)
        if result == True:
            child.setBackground(2, QColor('#B90E0A'))
        elif result == False:
            child.setBackground(2, QColor('#5DBB63'))  
        if symbol:
            child.setText(1, symbol)  
        if highlight:
            child.setBackground(0, QColor("#c0cbdb"))
        tree.expandToDepth(0)

class MainWindow(QWidget):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("Compare JUnit XML's")
        self.resize(400, 150)
        #self.setMinimumWidth(400)
        self.setup = SetupView(self)
        self.tree = TreeView(self)
        self.stacked = QStackedLayout()
        self.stacked.addWidget(self.setup)
        self.stacked.addWidget(self.tree)
        self.setLayout(self.stacked)

    def switch_layout(self):
        if self.stacked.currentIndex() == 0:
            self.change_size(700, 500)
            self.stacked.setCurrentIndex(1)
        else:
            self.change_size(400, 150)
            self.stacked.setCurrentIndex(0)
    
    def change_size(self, x, y):
        center = self.geometry().center()
        left = (center.x() - (x/2))
        top = (self.geometry().top())

        rect = QRect(left, top, x, y)
        self.setGeometry(rect)


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    sys.exit(app.exec())