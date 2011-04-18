'''
Created on 17 Apr 2011

@author: Mike Thomas

'''

from PyQt4.QtGui import QDialog, QListWidgetItem
from PyQt4.QtCore import Qt, QVariant, pyqtSignature

from Data.Beat import Beat
from Data.MeasureCount import MeasureCount
from ui_DBComplextCountDialog import Ui_complexCountDialog

class QComplexCountDialog(QDialog, Ui_complexCountDialog):
    '''
    classdocs
    '''


    def __init__(self, registry, measureCount, parent = None):
        '''
        Constructor
        '''
        super(QComplexCountDialog, self).__init__(parent)
        self.setupUi(self)
        self._default = measureCount
        self._registry = registry
        for name, unusedCount in self._registry:
            self.countBox.addItem(name)
        self.beatList.currentItemChanged.connect(self._newBeatChosen)
        self.countBox.currentIndexChanged.connect(self._beatChanged)
        self.numTicksSpinBox.valueChanged.connect(self.numTicksChanged)
        self._restoreDefault()
        restore = self.buttonBox.button(self.buttonBox.Reset)
        restore.clicked.connect(self._restoreDefault)

    def _restoreDefault(self):
        self.setCount(self._default)

    def setCount(self, count):
        self.beatList.clear()
        for beatNum, beat in enumerate(count):
            countIndex = self._registry.lookupIndex(beat)
            item = QListWidgetItem("".join(beat.count(beatNum + 1)))
            item.setData(Qt.UserRole, QVariant(countIndex))
            self.beatList.addItem(item)
        self.beatList.setCurrentRow(0)
        self.preview()

    def preview(self):
        self._checkDeleteEnabled()
        self.previewText.setText("".join(unicode(self.beatList.item(beatNum).text())
                                         for beatNum in
                                         range(0, self.beatList.count())))

    def _checkDeleteEnabled(self):
        self.deleteButton.setEnabled(self.beatList.count() > 1)

    def _newBeatChosen(self):
        item = self.beatList.currentItem()
        if item is None:
            return
        index = item.data(Qt.UserRole).toInt()[0]
        self.countBox.setCurrentIndex(index)
        beatCounter = self._registry.getCounterByIndex(index)
        self.numTicksSpinBox.setMinimum(1)
        self.numTicksSpinBox.setMaximum(len(beatCounter))
        self.numTicksSpinBox.setValue(len(item.text()))

    def _beatChanged(self):
        counter = self._registry.getCounterByIndex(self.countBox.currentIndex())
        self.numTicksSpinBox.setMaximum(len(counter))
        self.numTicksSpinBox.setValue(len(counter))
        item = self.beatList.currentItem()
        beat = Beat(counter)
        item.setText("".join(beat.count(self.beatList.currentRow() + 1)))
        item.setData(Qt.UserRole, self.countBox.currentIndex())
        self.preview()

    def _updateBeatText(self):
        for row in range(0, self.beatList.count()):
            item = self.beatList.item(row)
            index = item.data(Qt.UserRole).toInt()[0]
            counter = self._registry.getCounterByIndex(index)
            beat = Beat(counter, len(item.text()))
            item.setText("".join(beat.count(row + 1)))

    @pyqtSignature("")
    def on_addButton_clicked(self):
        counter = self._registry.getCounterByIndex(self.countBox.currentIndex())
        beat = Beat(counter)
        beatNum = self.beatList.count()
        item = QListWidgetItem("".join(beat.count(beatNum + 1)))
        item.setData(Qt.UserRole, QVariant(self.countBox.currentIndex()))
        self.beatList.addItem(item)
        self.beatList.setCurrentItem(item)
        self.preview()

    @pyqtSignature("")
    def on_deleteButton_clicked(self):
        self.beatList.takeItem(self.beatList.currentRow())
        self._updateBeatText()
        self.preview()

    def numTicksChanged(self):
        counter = self._registry.getCounterByIndex(self.countBox.currentIndex())
        beat = Beat(counter, self.numTicksSpinBox.value())
        beatText = "".join(beat.count(self.beatList.currentRow() + 1))
        self.beatList.currentItem().setText(beatText)
        self.preview()

    def getCount(self):
        mc = MeasureCount()
        for row in range(0, self.beatList.count()):
            item = self.beatList.item(row)
            index = item.data(Qt.UserRole).toInt()[0]
            counter = self._registry.getCounterByIndex(index)
            beat = Beat(counter, len(item.text()))
            mc.addBeats(beat, 1)
        return mc