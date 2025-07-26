from PyQt5.QtCore import QThread, pyqtSignal
# データ取得用QThread
class DataFetchThread(QThread):
    result_ready = pyqtSignal(list, int, int)  # (page_results, result_count, page_count)

    def __init__(self, db_path, format_text, format_lc, current_page, results_limit):
        super().__init__()
        self.db_path = db_path
        self.format_text = format_text
        self.format_lc = format_lc
        self.current_page = current_page
        self.results_limit = results_limit

    def run(self):
        import sqlite3
        filtered_results = []
        result_count = 0
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            if self.format_text == 'すべて':
                c.execute('SELECT raw_json FROM packages')
            else:
                c.execute('''SELECT DISTINCT p.raw_json FROM packages p
                    JOIN resources r ON p.id = r.package_id
                    WHERE LOWER(r.format) LIKE ?''', (f'%{self.format_lc}%',))
            rows = c.fetchall()
            import json
            for row in rows:
                entry = json.loads(row[0])
                if self.format_text == 'すべて':
                    filtered_results.append(entry)
                else:
                    if any(self.format_lc in (res.get('format','').strip().lower()) for res in entry.get('resources', [])):
                        filtered_results.append(entry)
            conn.close()
        except Exception as e:
            # エラー時は空リスト返す
            filtered_results = []
        result_count = len(filtered_results)
        page_count = max(1, (result_count + self.results_limit - 1) // self.results_limit)
        start_idx = (self.current_page - 1) * self.results_limit
        end_idx = start_idx + self.results_limit
        page_results = filtered_results[start_idx:end_idx]
        self.result_ready.emit(page_results, result_count, page_count)
# -*- coding: utf-8 -*-
"""
/***************************************************************************
 CKAN-Browser
                                 A QGIS plugin
 Download and display CKAN enabled Open Data Portals
                              -------------------
        begin                : 2014-10-24
        git sha              : $Format:%H$
        copyright            : (C) 2014 by BergWerk GIS
        email                : wb@BergWerk-GIS.at
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import math
import os
import sys
from PyQt5.QtCore import Qt, QTimer
from PyQt5 import QtGui, uic
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QListWidgetItem, QDialog, QMessageBox
from .ckan_browser_dialog_disclaimer import CKANBrowserDialogDisclaimer
from .ckan_browser_dialog_dataproviders import CKANBrowserDialogDataProviders
from .pyperclip import copy
from .ckanconnector import CkanConnector
from .util import Util


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ckan_browser_dialog_base.ui'))


class CKANBrowserDialog(QDialog, FORM_CLASS):
    def update_format_list(self, results):
        """
        すべてのリソースからformat値を収集し、重複を除去してリスト化し、formats.jsonに保存
        """
        import json
        format_set = set()
        for entry in results:
            for res in entry.get('resources', []):
                if 'format' in res and res['format']:
                    fmt = res['format'].strip()
                    if fmt:
                        format_set.add(fmt)
        format_list = sorted(format_set, key=lambda x: x.lower())
        # formats.jsonに保存
        # キャッシュディレクトリ未設定時はユーザーのダウンロード/CKAN-Browser配下に作成
        cache_dir = self.settings.cache_dir
        if not cache_dir or not os.path.isdir(cache_dir):
            if sys.platform == 'win32':
                from pathlib import Path
                downloads = str(Path.home() / 'Downloads')
            elif sys.platform == 'darwin':
                downloads = os.path.expanduser('~/Downloads')
            else:
                downloads = os.path.expanduser('~/Downloads')
            cache_dir = os.path.join(downloads, 'CKAN-Browser')
            if not os.path.isdir(cache_dir):
                os.makedirs(cache_dir, exist_ok=True)
        formats_path = os.path.join(cache_dir, 'formats.json')
        try:
            with open(formats_path, 'w', encoding='utf-8') as f:
                json.dump(format_list, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.util.msg_log_error(f"formats.json保存エラー: {e}")
        self.set_format_combobox(format_list)

    def set_format_combobox(self, format_list):
        if hasattr(self, 'IDC_comboFormat'):
            self.IDC_comboFormat.blockSignals(True)
            self.IDC_comboFormat.clear()
            self.IDC_comboFormat.addItem('すべて')
            for fmt in format_list:
                self.IDC_comboFormat.addItem(fmt)
            self.IDC_comboFormat.blockSignals(False)

    def __init__(self, settings, iface, parent=None):
        """Constructor."""
        super(CKANBrowserDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.iface = iface
        self.main_win = parent
        self.search_txt = ''
        self.cur_package = None
        self.result_count = 0
        self.current_page = 1
        self.page_count = 0
        self.current_group = None
        # TODO:
        # * create settings dialog
        # * read SETTINGS

        self.settings = settings
        self.util = Util(self.settings, self.main_win)

        self.IDC_lblVersion.setText(self.IDC_lblVersion.text().format(self.settings.version))
        #self.IDC_lblSuchergebnisse.setText(self.util.tr('py_dlg_base_search_result'))
        self.IDC_lblPage.setText(self.util.tr('py_dlg_base_page_1_1'))

        # データ形式コンボボックスを手入力可能に
        if hasattr(self, 'IDC_comboFormat'):
            self.IDC_comboFormat.setEditable(True)

        icon_path = self.util.resolve(u'icon-copy.png')
        self.IDC_bCopy.setIcon(QtGui.QIcon(icon_path))

        self.cc = CkanConnector(self.settings, self.util)

        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.window_loaded)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        # don't initialized dialogs here, WaitCursor would be set several times
        # self.dlg_disclaimer = CKANBrowserDialogDisclaimer(self.settings)
        # self.dlg_dataproviders = CKANBrowserDialogDataProviders(self.settings, self.util)

        # --- 追加: SQLite再取得ボタンのシグナル接続 ---
        if hasattr(self, 'IDC_bRefreshSqlite'):
            self.IDC_bRefreshSqlite.clicked.connect(self.refresh_sqlite_clicked)
    def refresh_sqlite_clicked(self):
        """
        全データセットを再取得しSQLiteキャッシュを再作成する
        """
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            ok, result = self.cc.get_groups()
            if ok is False:
                QApplication.restoreOverrideCursor()
                self.util.dlg_warning(result)
                return
            if not result:
                self.list_all_clicked()
                return
            all_results = []
            page = 1
            while True:
                ok, page_result = self.cc.package_search('', None, page)
                if not ok or 'results' not in page_result:
                    break
                results = page_result['results']
                if not results:
                    break
                all_results.extend(results)
                if page == 1:
                    total_count = page_result.get('count', 0)
                    results_limit = getattr(self.settings, 'results_limit', 50)
                    max_page = (total_count + results_limit - 1) // results_limit
                if page >= max_page:
                    break
                page += 1
            if all_results:
                from qgis.core import QgsMessageLog, Qgis
                try:
                    from save_ckan_to_sqlite import save_ckan_packages_to_sqlite
                    cache_dir = self.settings.cache_dir
                    if not cache_dir or not os.path.isdir(cache_dir):
                        if sys.platform == 'win32':
                            from pathlib import Path
                            downloads = str(Path.home() / 'Downloads')
                        elif sys.platform == 'darwin':
                            downloads = os.path.expanduser('~/Downloads')
                        else:
                            downloads = os.path.expanduser('~/Downloads')
                        cache_dir = os.path.join(downloads, 'CKAN-Browser')
                        if not os.path.isdir(cache_dir):
                            os.makedirs(cache_dir, exist_ok=True)
                    db_path = os.path.join(cache_dir, 'ckan_cache.db')
                    QgsMessageLog.logMessage(self.util.tr(u"Caching data to SQLite has started."), 'CKAN-Browser', Qgis.Info)
                    save_ckan_packages_to_sqlite(db_path, all_results)
                    QgsMessageLog.logMessage(self.util.tr(u"Caching data to SQLite has finished."), 'CKAN-Browser', Qgis.Info)
                    self.util.msg_log_debug(self.util.tr(u"Saved {} records to SQLite DB: {}.").format(len(all_results), db_path))
                except Exception as e:
                    QgsMessageLog.logMessage(self.util.tr(u"SQLite save error: {}".format(e)), 'CKAN-Browser', Qgis.Critical)
                    self.util.msg_log_error(self.util.tr(u"SQLite save error: {}".format(e)))
                self.update_format_list(all_results)
        finally:
            QApplication.restoreOverrideCursor()


    def showEvent(self, event):
        self.util.msg_log_debug('showevent')
        QDialog.showEvent(self, event)
        if self.timer is not None:
            self.timer.start(500)
        self.util.msg_log_debug('showevent finished')

    def window_loaded(self):
        import json
        try:
            self.settings.load()
            self.IDC_lblApiUrl.setText(self.util.tr('py_dlg_base_current_server').format(self.settings.ckan_url))
            self.IDC_lblCacheDir.setText(self.util.tr('py_dlg_base_cache_path').format(self.settings.cache_dir))
            if self.timer is not None:
                self.timer.stop()
                self.timer = None

            self.IDC_listResults.clear()
            self.IDC_listGroup.clear()
            self.IDC_textDetails.setText('')
            self.IDC_listRessources.clear()
            self.IDC_plainTextLink.setPlainText('')

            self.util.msg_log_debug('before get_groups')

            # formats.jsonがあればそれを使う
            # キャッシュディレクトリ未設定時はユーザーのダウンロード/CKAN-Browser配下に作成
            cache_dir = self.settings.cache_dir
            if not cache_dir or not os.path.isdir(cache_dir):
                if sys.platform == 'win32':
                    from pathlib import Path
                    downloads = str(Path.home() / 'Downloads')
                elif sys.platform == 'darwin':
                    downloads = os.path.expanduser('~/Downloads')
                else:
                    downloads = os.path.expanduser('~/Downloads')
                cache_dir = os.path.join(downloads, 'CKAN-Browser')
                if not os.path.isdir(cache_dir):
                    os.makedirs(cache_dir, exist_ok=True)
            formats_path = os.path.join(cache_dir, 'formats.json')
            if os.path.isfile(formats_path):
                try:
                    with open(formats_path, 'r', encoding='utf-8') as f:
                        format_list = json.load(f)
                    self.set_format_combobox(format_list)
                except Exception as e:
                    self.util.msg_log_error(f"formats.json読込エラー: {e}")
            else:
                # formats.jsonがなければ従来通り全件取得して生成
                ok, result = self.cc.get_groups()
                if ok is False:
                    QApplication.restoreOverrideCursor()
                    self.util.dlg_warning(result)
                    return

                if not result:
                    self.list_all_clicked()
                else:
                    for entry in result:
                        item = QListWidgetItem(entry['display_name'])
                        item.setData(Qt.UserRole, entry)
                        item.setCheckState(Qt.Unchecked)
                        self.IDC_listGroup.addItem(item)
                    # サーバーからグループ一覧取得後、全データセットも取得してデータ形式リストを初期化（全ページ対応）
                    all_results = []
                    page = 1
                    while True:
                        ok, page_result = self.cc.package_search('', None, page)
                        if not ok or 'results' not in page_result:
                            break
                        results = page_result['results']
                        if not results:
                            break
                        all_results.extend(results)
                        # ページ数の計算
                        if page == 1:
                            total_count = page_result.get('count', 0)
                            results_limit = getattr(self.settings, 'results_limit', 50)
                            max_page = (total_count + results_limit - 1) // results_limit
                        if page >= max_page:
                            break
                        page += 1
                    if all_results:
                        # SQLiteに保存（設定画面のキャッシュディレクトリに保存）
                        from qgis.core import QgsMessageLog, Qgis
                        try:
                            from save_ckan_to_sqlite import save_ckan_packages_to_sqlite
                            # キャッシュディレクトリ未設定時はユーザーのダウンロード/CKAN-Browser配下に作成
                            cache_dir = self.settings.cache_dir
                            if not cache_dir or not os.path.isdir(cache_dir):
                                if sys.platform == 'win32':
                                    from pathlib import Path
                                    downloads = str(Path.home() / 'Downloads')
                                elif sys.platform == 'darwin':
                                    downloads = os.path.expanduser('~/Downloads')
                                else:
                                    downloads = os.path.expanduser('~/Downloads')
                                cache_dir = os.path.join(downloads, 'CKAN-Browser')
                                if not os.path.isdir(cache_dir):
                                    os.makedirs(cache_dir, exist_ok=True)
                            db_path = os.path.join(cache_dir, 'ckan_cache.db')
                            QgsMessageLog.logMessage(self.util.tr(u"Caching data to SQLite has started."), 'CKAN-Browser', Qgis.Info)
                            save_ckan_packages_to_sqlite(db_path, all_results)
                            QgsMessageLog.logMessage(self.util.tr(u"Caching data to SQLite has finished."), 'CKAN-Browser', Qgis.Info)
                            self.util.msg_log_debug(self.util.tr(u"Saved {} records to SQLite DB: {}.").format(len(all_results), db_path))
                        except Exception as e:
                            QgsMessageLog.logMessage(self.util.tr(u"SQLite save error: {}".format(e)), 'CKAN-Browser', Qgis.Critical)
                            self.util.msg_log_error(self.util.tr(u"SQLite save error: {}".format(e)))
                        self.update_format_list(all_results)
        finally:
            QApplication.restoreOverrideCursor()

    def close_dlg(self):
        QDialog.reject(self)

    def show_disclaimer(self):
        self.dlg_disclaimer = CKANBrowserDialogDisclaimer(self.settings)
        self.dlg_disclaimer.show()

    def searchtextchanged(self, search_txt):
        self.search_txt = search_txt

    def suchen(self):
        self.current_page = 1
        self.current_group = None
        self.__search_package()

    def list_all_clicked(self):
        self.current_page = 1
        self.current_group = None
        # don't hint on wildcards, empty text works as well, as CKAN uses *:* as
        # default when ?q= has not text
        # self.IDC_lineSearch.setText('*:*')
        self.IDC_lineSearch.setText('')
        self.__search_package()

    def category_item_clicked(self, item):
        self.util.msg_log_debug(item.data(Qt.UserRole)['name'])
        self.current_group = item.data(Qt.UserRole)['name']
        self.current_page = 1
        self.__search_package()

    def select_data_provider_clicked(self):
        self.util.msg_log_debug('select data provider clicked')
        self.dlg_dataproviders = CKANBrowserDialogDataProviders(self.settings)
        self.dlg_dataproviders.show()
        if self.dlg_dataproviders.exec_():
            QApplication.setOverrideCursor(Qt.WaitCursor)
            self.window_loaded()

    def __search_package(self, page=None):
        self.IDC_listResults.clear()
        # ページング制御
        if page is not None:
            self.util.msg_log_debug(u'page is not None, cp:{0} pg:{1}'.format(self.current_page, page))
            self.current_page = self.current_page + page
            if self.current_page < 1:
                self.current_page = 1
            if self.current_page > self.page_count:
                self.current_page = self.page_count
            self.util.msg_log_debug(u'page is not None, cp:{0} pg:{1}'.format(self.current_page, page))
        QApplication.setOverrideCursor(Qt.WaitCursor)
        db_path = os.path.join(self.settings.cache_dir or os.getcwd(), 'ckan_cache.db')
        format_text = self.IDC_comboFormat.currentText() if hasattr(self, 'IDC_comboFormat') else 'すべて'
        format_lc = format_text.lower()
        results_limit = getattr(self.settings, 'results_limit', 50)
        # QThreadでデータ取得
        self.data_thread = DataFetchThread(db_path, format_text, format_lc, self.current_page, results_limit)
        self.data_thread.result_ready.connect(self._on_data_ready)
        self.data_thread.start()

    def _on_data_ready(self, page_results, result_count, page_count):
        QApplication.restoreOverrideCursor()
        self.result_count = result_count
        self.page_count = page_count
        erg_text = self.util.tr(u'py_dlg_base_result_count').format(self.result_count)
        self.util.msg_log_debug(erg_text)
        page_text = self.util.tr(u'py_dlg_base_page_count').format(self.current_page, self.page_count)
        self.IDC_lblSuchergebnisse.setText(erg_text)
        self.IDC_lblPage.setText(page_text)
        self.IDC_listResults.clear()
        for entry in page_results:
            title_txt = u'no title available'
            if 'title' not in entry:
                continue
            e = entry['title']
            if e is None:
                title_txt = 'no title'
            elif isinstance(e, dict):
                title_txt = next(iter(list(e.values())))
            elif isinstance(e, list):
                title_txt = e[0]
            else:
                title_txt = e
            item = QListWidgetItem(title_txt)
            item.setData(Qt.UserRole, entry)
            self.IDC_listResults.addItem(item)

    def list_group_item_changed(self, item):
        self.searchtextchanged(self.IDC_lineSearch.text())

    def resultitemchanged(self, new_item):
        self.IDC_textDetails.setText('')
        self.IDC_listRessources.clear()
        self.IDC_plainTextLink.clear()
        if new_item is None:
            return
        package = new_item.data(Qt.UserRole)
        self.cur_package = package
        if package is None:
            return
        self.IDC_textDetails.setText(
            u'{0}\n\n{1}\n{2}\n\n{3}'.format(
                package.get('notes', 'no notes'),
                package.get('author', 'no author'),
                package.get('author_email', 'no author_email'),
                package.get('license_id', 'no license_id')
            )
        )
        # データ形式フィルタ
        format_text = self.IDC_comboFormat.currentText() if hasattr(self, 'IDC_comboFormat') else 'すべて'
        format_lc = format_text.lower()
        def is_format_match(res):
            if format_text == 'すべて':
                return True
            # formatフィールドのみ判定（部分一致・空白除去・相互包含）
            if 'format' in res and res['format']:
                fmt = res['format'].strip().lower()
                if format_lc in fmt or fmt in format_lc:
                    return True
            return False
        resources = package.get('resources', [])
        filtered_resources = [res for res in resources if is_format_match(res)]
        for res in filtered_resources:
            disp = u'{}: {}'.format(res.get('format', 'no format'), res.get('url', '(no url)'))
            item = QListWidgetItem(disp)
            item.setData(Qt.UserRole, res)
            item.setCheckState(Qt.Unchecked)
            self.IDC_listRessources.addItem(item)

    def resource_item_changed(self, new_item):
        if new_item is None:
            return
        url = new_item.data(Qt.UserRole)['url']
        self.util.msg_log_debug(url)
        self.__fill_link_box(url)

    def load_resource_clicked(self):
        res = self.__get_selected_resources()
        if res is None:
            self.util.dlg_warning(self.util.tr(u'py_dlg_base_warn_no_resource'))
            return
        # self.util.dlg_warning(u'pkg:{0} res:{1} {2}'.format(self.cur_package['id'], res[0]['id'], res[0]['url']))
        for resource in res:
            if resource['name'] is None:
                # self.util.dlg_warning(self.util.tr(u'py_dlg_base_warn_no_resource_name').format(resource['id']))
                # continue
                resource['name'] = "Unnamed resource"
            self.util.msg_log_debug(u'Bearbeite: {0}'.format(resource['name']))
            dest_dir = os.path.join(
                self.settings.cache_dir,
                self.cur_package['id'],
                resource['id']
            )
            if self.util.create_dir(dest_dir) is False:
                self.util.dlg_warning(self.util.tr(u'py_dlg_base_warn_cache_dir_not_created').format(dest_dir))
                return

            dest_file = os.path.join(dest_dir, os.path.split(resource['url'])[1])

            # wmts
            format_lower = resource['format'].lower()
            if format_lower == 'wms':
                format_lower = 'wmts'
            if format_lower == 'wmts':
                resource_url = resource['url']
                resource_url_lower = resource_url.lower()
                if not resource_url_lower.endswith('.qlr'):
                    dest_file += '.wmts'
                #pyperclip.copy(resource_url)
                """
                self.util.dlg_information(u'{0}\n{1}\n\n{2}\n{3}\n{4}'.format(
                    u'WMTS kann nicht automatisch geladen werden.',
                    u'Der Link wurde in die Zwischenablage kopiert.',
                    u'Layer -> Layer hinzufügen -> ',
                    u'WMS/WMTS-Layer hinzufügen ->',
                    u'Neu -> im Textfeld "URL" Strg+V drücken'
                ))
                continue
                """
            if format_lower == 'wfs':
                dest_file += '.wfs'
            if format_lower == 'georss':
                dest_file += '.georss'

            do_download = True
            do_delete = False
            if os.path.isfile(dest_file):
                if QMessageBox.Yes == self.util.dlg_yes_no(self.util.tr(u'py_dlg_base_data_already_loaded')):
                    do_delete = True
                    do_download = True
                else:
                    do_download = False
            if do_download is True:
                # set wait cursor if request take it time, low latency, server not reachable, ...
                QApplication.setOverrideCursor(Qt.WaitCursor)
                QtWidgets.qApp.processEvents()
                file_size_ok, file_size, hdr_exception = self.cc.get_file_size(resource['url'])
                QApplication.restoreOverrideCursor()
                # Silently ignore the error
                if not file_size_ok:
                    file_size = 0
                if file_size > 50 and QMessageBox.No == self.util.dlg_yes_no(self.util.tr(u'py_dlg_base_big_file').format(file_size)):
                    continue  # stop process if user does not want to download the file
                if hdr_exception:
                    # self.util.dlg_warning(u'{}'.format(hdr_exception))
                    # continue
                    # just log exception and continue, some servers dont support HEAD request
                    self.util.msg_log_error(u'error getting size of response, HEAD request failed: {}'.format(hdr_exception))

                self.util.msg_log_debug('setting wait cursor')
                QApplication.setOverrideCursor(Qt.WaitCursor)
                # pump GUI messages, otherwise wait cursor might not get displayed
                # as we are running the downloads on the main thread and if the request
                # gets stuck immediately (eg low latency or connection refused only after some time)
                # wait cursor might not appear
                QtWidgets.qApp.processEvents()
                self.util.msg_log_debug('wait cursor set')

                ok, err_msg, new_file_name = self.cc.download_resource(
                    resource['url']
                    , resource['format']
                    , dest_file
                    , do_delete
                )
                QApplication.restoreOverrideCursor()
                if ok is False:
                    #self.util.dlg_warning(self.util.tr(u'py_dlg_base_download_error').format(err_msg))
                    self.util.dlg_warning(err_msg)
                    continue
                # set new file name obtained from service 'content-disposition'
                if new_file_name:
                    dest_file = new_file_name
                if os.path.basename(dest_file).lower().endswith('.zip'):
                    ok, err_msg = self.util.extract_zip(dest_file, dest_dir)
                    QApplication.restoreOverrideCursor()
                    if ok is False:
                        self.util.dlg_warning(self.util.tr(u'py_dlg_base_warn_not_extracted').format(err_msg))
                        continue

            #QApplication.setOverrideCursor(Qt.WaitCursor)
            ok, err_msg = self.util.add_lyrs_from_dir(dest_dir, resource['name'], resource['url'])
            #QApplication.restoreOverrideCursor()
            if ok is False:
#                 self.util.dlg_warning(self.util.tr(u'py_dlg_base_lyr_not_loaded').format(resource['name'], err_msg))
                if isinstance(err_msg, dict):
                    if QMessageBox.Yes == self.util.dlg_yes_no(self.util.tr(u'py_dlg_base_open_manager').format(resource['url'])):
                        self.util.open_in_manager(err_msg["dir_path"])
                else:
                    self.util.dlg_warning(self.util.tr(u'py_dlg_base_lyr_not_loaded').format(resource['name'], err_msg))
                continue

    def next_page_clicked(self):
        self.__search_package(page=+1)

    def previous_page_clicked(self):
        self.__search_package(page=-1)

    def copy_clipboard(self):
        copy(self.IDC_plainTextLink.toPlainText())

    def __fill_link_box(self, url):
        self.IDC_plainTextLink.setPlainText(url)

    def __get_selected_groups(self):
        groups = []
        for i in range(0, self.IDC_listGroup.count()):
            item = self.IDC_listGroup.item(i)
            if item.checkState() == Qt.Checked:
                groups.append(item.data(Qt.UserRole)['name'])

        # None: means search all groups
        if len(groups) < 1 or len(groups) == self.IDC_listGroup.count():
            return None
        return groups

    def __get_selected_resources(self):
        res = []
        for i in range(0, self.IDC_listRessources.count()):
            item = self.IDC_listRessources.item(i)
            if item.checkState() == Qt.Checked:
                res.append(item.data(Qt.UserRole))

        if len(res) < 1:
            return None
        return res

    def _shorten_path(self, s):
        """ private class to shorten string to 33 chars and place a html-linebreak inside"""
        result = u""
        if len(s) > 33:
            result = s[:33] + u'<br />' + self._shorten_path(s[33:])
        else:
            return s
        return result

    def help_ttip_search(self):
        self.util.dlg_information(self.util.tr(u'dlg_base_ttip_search'))

    def help_ttip_filter(self):
        self.util.dlg_information(self.util.tr(u'dlg_base_ttip_filter'))

    def help_ttip_data_list(self):
        self.util.dlg_information(self.util.tr(u'dlg_base_ttip_data_list'))

    def help_ttip_resource(self):
        self.util.dlg_information(self.util.tr(u'dlg_base_ttip_resource'))
