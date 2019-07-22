# sel_opt.py

from collections import namedtuple
from typing import Union

from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtWidgets import QDialog

from helper import EXT_ID_INCREMENT
from ui_sel_opt import Ui_SelOpt


class SelOpt(QDialog):
    # todo instead of controller use the dict/map of list choosen items in all widgets
    def __init__(self, controller, parent=None):
        super(SelOpt, self).__init__(parent)
        self.ui = Ui_SelOpt()
        self.ui.setupUi(self)

        self.ctrl = controller

        self.not_older = 5
        self._restore_state()

        self.ui.chAuthor.stateChanged.connect(self.author_toggle)
        self.ui.chDate.stateChanged.connect(self.date_toggle)
        self.ui.chDirs.stateChanged.connect(self.dir_toggle)
        self.ui.chExt.stateChanged.connect(self.ext_toggle)
        self.ui.chTags.stateChanged.connect(self.tag_toggle)
        self.ui.eDate.textEdited.connect(self._text_edited)

    def _text_edited(self, ed_str):
        # print('|--> _text_edited', ed_str)
        self.not_older = int(ed_str)

    def _restore_state(self):
        settings = QSettings()
        rest = settings.value('SelectionOptions', (False, False, False, True,
                                                   False, (True, 5, True)))
        self.ui.chDirs.setChecked(rest[0])
        self.ui.chExt.setChecked(rest[1])
        self.ui.chTags.setChecked(rest[2])
        self.ui.tagAll.setChecked(rest[3])
        self.ui.chAuthor.setChecked(rest[4])
        self.ui.chDate.setChecked(rest[5][0])
        if rest[5][1]:
            self.not_older = int(rest[5][1])
        else:
            self.not_older = 5
        self.ui.eDate.setText(str(self.not_older))
        self.ui.eDate.setEnabled(rest[5][0])
        self.ui.dateFile.setChecked(rest[5][2])

    def author_toggle(self, author_list):
        if self.ui.chAuthor.isChecked():
            self.ui.eAuthors.setText(author_list)  # todo the same in the similar ethods
            # author_list = self.ctrl.get_selected_items(self.ctrl.ui.authorsList))
        else:
            self.ui.eAuthors.setText('')

    def date_toggle(self):
        state = self.ui.chDate.isChecked()
        self.ui.eDate.setEnabled(state)
        self.ui.dateBook.setEnabled(state)
        self.ui.dateFile.setEnabled(state)

        if state:
            if not self.ui.eDate.text():
                self.ui.eDate.setText(str(self.not_older))
        else:
            self.ui.eDate.setText('')

    def dir_toggle(self):
        if self.ui.chDirs.isChecked():
            self.ui.lDir.setText(self.ctrl.get_selected_items(self.ctrl.ui.dirTree))
            if self.ui.lDir.text():
                self.ui.sbLevel.setEnabled(True)
        else:
            self.ui.lDir.setText('')
            self.ui.sbLevel.setEnabled(False)

    def ext_toggle(self):
        if self.ui.chExt.isChecked():
            self.ui.eExt.setText(self.ctrl.get_selected_items(self.ctrl.ui.extList))
        else:
            self.ui.eExt.setText('')

    def tag_toggle(self):
        # print('--> tag_toggle')
        state = self.ui.chTags.isChecked()
        if state:
            self.ui.eTags.setText(self.ctrl.get_selected_items(self.ctrl.ui.tagsList))
        else:
            self.ui.eTags.setText('')

        self.ui.tagAll.setEnabled(state)
        self.ui.tagAny.setEnabled(state)

    def get_result(self):
        result = namedtuple('result', 'dir extension tags authors date')
        dir_ = namedtuple('dir', 'use id_list')
        extension = namedtuple('extension', 'use id_list')
        tags = namedtuple('tags', 'use match_all id_list')
        authors = namedtuple('authors', 'use id_list')
        doc_date = namedtuple('not_older', 'use date file_date')

        dir_ids = self._get_dir_ids()
        ext_ids = self._get_ext_ids()
        tag_ids = self._get_tags_id()
        author_ids = self._get_authors_id()

        res = result(dir=dir_(use=self.ui.chDirs.isChecked(), id_list=dir_ids),
                     extension=extension(use=self.ui.chExt.isChecked(),
                                         id_list=ext_ids),
                     tags=tags(use=self.ui.chTags.isChecked(),
                               id_list=tag_ids,
                               match_all=self.ui.tagAll.isChecked()),
                     authors=authors(use=self.ui.chAuthor.isChecked(),
                                     id_list=author_ids),
                     date=doc_date(use=self.ui.chDate.isChecked(),
                                   date=self.ui.eDate.text(),
                                   file_date=self.ui.dateFile.isChecked()))
        settings = QSettings()
        settings.setValue('SelectionOptions', (res.dir.use, res.extension.use,
                                               res.tags.use, res.tags.match_all,
                                               res.authors.use,
                                               (res.date.use, res.date.date,
                                                res.date.file_date)))
        return res

    def _get_dir_ids(self) -> str:
        ''' returns list of selected IDs as string separated by coma '''
        if self.ui.chDirs.isChecked():
            lvl = 0
            idx = self.ctrl.ui.dirTree.currentIndex()
            root_id = int(self.ctrl.ui.dirTree.model().data(idx, Qt.UserRole)[0])

            ids = ','.join([str(id_[0]) for id_ in
                            self.ctrl.get_db_utils().dir_ids_select(root_id, lvl)])
            return ids
        return ''

    def _get_ext_ids( self ) -> str:
        ''' returns list of selected IDs as string separated by coma '''
        if self.ui.chExt.isChecked():
            sel_idx = self.ctrl.ui.extList.selectedIndexes()
            model = self.ctrl.ui.extList.model()
            aux = []
            for id_ in sel_idx:
                aux.append(model.data(id_, Qt.UserRole))

            idx = []
            for id_ in aux:
                if id_[0] > EXT_ID_INCREMENT:
                    idx.append(id_[0] - EXT_ID_INCREMENT)
                else:
                    idx += self._ext_in_group(id_[0])

            idx.sort()
            return ','.join([str(id_) for id_ in idx])
        return ''

    def _ext_in_group(self, gr_id) -> list:
        curr = self.ctrl.get_db_utils().select_other('EXT_ID_IN_GROUP', (gr_id,))
        idx = []
        for id_ in curr:
            idx.append(id_[0])

        return idx

    def _get_tags_id(self) -> str:
        if self.ui.chTags.isChecked():
            tags = self._get_items_id(self.ctrl.ui.tagsList)
            if tags:
                if self.ui.tagAll.isChecked():
                    num = len(tags.split(','))
                    res = self.ctrl.get_db_utils().select_other2('FILE_IDS_ALL_TAG',
                                                                 (tags, num)).fetchall()
                else:
                    res = self.ctrl.get_db_utils().select_other2('FILE_IDS_ANY_TAG',
                                                                 (tags,)).fetchall()
                return ','.join(str(ix[0]) for ix in res)

            return ''

        return ''

    def _get_authors_id(self) -> str:
        if self.ui.chAuthor.isChecked():
            auth_ids = self._get_items_id(self.ctrl.ui.authorsList)
            file_ids = self.ctrl.get_db_utils().select_other2('FILE_IDS_AUTHORS',
                                                              (auth_ids,)).fetchall()
            return ','.join(str(ix[0]) for ix in file_ids)

        return ''

    @staticmethod
    def _get_items_id(view):
        sel_idx = view.selectedIndexes()
        model = view.model()
        aux = []
        for id_ in sel_idx:
            aux.append(model.data(id_, Qt.UserRole))
        aux.sort()
        return ','.join([str(id_) for id_ in aux])

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    from gov_files import FilesCrt

    app = QApplication(sys.argv)

    _controller = FilesCrt()

    set_opt = SelOpt(_controller)

    if set_opt.exec_():
        print(set_opt.get_result())
    sys.exit(app.exec_())

    # sys.exit(app.exec_())

