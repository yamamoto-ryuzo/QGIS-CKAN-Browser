# -*- coding: utf-8 -*-

import errno
import os
from fnmatch import filter
import shutil
import subprocess
import sys
import zipfile
import json

from PyQt5.QtCore import \
    QCoreApplication, \
    QDateTime, \
    QDir, \
    QFile, \
    QFileInfo, \
    QIODevice, \
    QObject, \
    QSettings, \
    QUrl, \
    QUrlQuery
    #SIGNAL, \
    #SLOT
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtXml import QDomNode, QDomElement, QDomDocument, QDomNodeList

from qgis.core import QgsMessageLog, QgsVectorLayer, QgsRasterLayer, QgsProviderRegistry
from qgis.core import QgsLayerTreeGroup, QgsProject
from qgis.core import QgsMapLayer
from qgis.core import Qgis
from qgis.utils import iface


class Util:

    def __init__(self, settings, main_win):
        self.main_win = main_win
        self.dlg_caption = settings.DLG_CAPTION
        self.settings = settings

    # Moved from ckan_browser.py
    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        #return QCoreApplication.translate('CKANBrowser', message, None)
        return QCoreApplication.translate('self.util', message, None)

    def create_dir(self, dir_path):
        if not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path)
            except OSError as ose:
                if ose.errno != errno.EEXIST:
                    return False
        return True

    def check_dir(self, dir_path):
        if (
            dir_path is None or
            dir_path.isspace() or
            dir_path == ''
        ):
            return False
        if os.path.isdir(dir_path):
            # TODO check write permissions
            return True
        return self.create_dir(dir_path)

    def safe_filename(self, name, fallback='item', max_len=100):
        """Return a filesystem-safe, human-friendly filename derived from name.

        - Normalize Unicode and remove combining marks.
        - Replace path separators and unsafe characters with underscore.
        - Collapse repeated underscores and trim.
        - Return fallback when resulting name is empty.
        """
        import re, unicodedata
        try:
            if name is None:
                name = ''
            name = str(name)
        except Exception:
            name = ''

        if not name:
            name = fallback

        # Normalize and remove combining marks
        name = unicodedata.normalize('NFKD', name)
        name = ''.join(ch for ch in name if not unicodedata.category(ch).startswith('M'))

        # Replace path separators and whitespace with underscore
        name = re.sub(r'[\\/\s]+', '_', name)

        # Replace characters that are not word, dash, dot or underscore
        name = re.sub(r'[^\w\-\._]', '_', name)

        # Collapse multiple underscores and trim
        name = re.sub(r'_+', '_', name).strip('._-')

        if not name:
            name = fallback

        if len(name) > max_len:
            name = name[:max_len].rstrip('._-')

        return name


    def check_api_url(self, api_url):
        if(
           not api_url or
           api_url is None or
           api_url.isspace() or
           api_url == ''
           ):
            return False
        else:
            return True

    def extract_zip(self, archive, dest_dir):
        try:
            # zf.extractall(dest_dir) fails for umlauts
            # https://github.com/joeferraro/MavensMate/pull/27/files
            with zipfile.ZipFile(archive, 'r') as f:
                self.msg_log_debug(u'dest_dir: {0}'.format(dest_dir))

                for file_info in f.infolist():
                    file_name = os.path.join(dest_dir, file_info.filename)
                    # different types of ZIPs
                    # some have a dedicated entry for folders
                    if file_name[-1] == u'/':
                        if not os.path.exists(file_name):
                            os.makedirs(file_name)
                        continue
                    # some don't hava dedicated entry for folder
                    # extract folder info from file name
                    extract_dir = os.path.dirname(file_name)
                    if not os.path.exists(extract_dir):
                        os.makedirs((extract_dir))
                    with f.open(file_info.filename) as src, open(file_name, 'wb') as out_file:
                        shutil.copyfileobj(src, out_file)
            return True, None
        except UnicodeDecodeError as ude:
            return False, u'UnicodeDecodeError: {0}'.format(ude)
        except AttributeError as ae:
            return False, u'AttributeError: {0}'.format(ae)
        except:
            self.msg_log_debug(u'Except: {0}'.format(sys.exc_info()[1]))
            return False, u'Except: {0}'.format(sys.exc_info()[1])

    def add_lyrs_from_dir(self, data_dir, layer_name, layer_url):
        try:
            file_types = (
                '*.[Ss][Hh][Pp]',
                '*.[Gg][Pp][Kk][Gg]',  # GPKG (GeoPackage) を追加
                '*.[Gg][Mm][Ll]',
                '*.[Gg][Ee][Oo][Rr][Ss][Ss]',
                '*.[Xx][Mm][Ll]',
                '*.[Cc][Ss][Vv]',
                '*.[Tt][Xx][Tt]',
                '*.[Pp][Dd][Ff]',
                '*.[Tt][Ii][Ff]',
                '*.[Tt][Ii][Ff][Ff]',
                '*.[Aa][Ss][Cc]',
                '*.[Qq][Ll][Rr]',
                '*.[Ii][Mm][Gg]',
                '*.[Jj][2][Kk]',
                '*.[Jj][Pp][2]',
                '*.[Rr][Ss][Tt]',
                '*.[Dd][Ee][Mm]',
                '*.[Ww][Mm][Tt][Ss]',
                '*.[Ww][Mm][Ss]',
                '*.[Ww][Ff][Ss]',
                '*.[Kk][Mm][Ll]',
                '*.[Xx][Ll][Ss]',
                '*.[Xx][Ll][Ss][Xx]',
                '*.[Dd][Oo][Cc]',
                '*.[Dd][Oo][Cc][Xx]',
                '*.[Jj][Pp][Gg]',
                '*.[Jj][Pp][Ee][Gg]',
                '*.[Pp][Nn][Gg]',
                '*.*[Jj][Ss][Oo][Nn]'
            )
            geo_files = []
            for file_type in file_types:
                ### python 3.5
                # glob_term = os.path.join(data_dir, '**', file_type)
                # geo_files.extend(glob.glob(glob_term))
                ### python > 2.2
                for root, dir_names, file_names in os.walk(data_dir):
                    for file_name in filter(file_names, file_type):
                        geo_files.append(os.path.join(root, file_name))

            self.msg_log_debug(u'add lyrs: {0}'.format(data_dir))
            self.msg_log_debug(u'add lyrs: {0}'.format('\n'.join(geo_files)))

            if len(geo_files) < 1:
                self.msg_log_debug('len(geo_files)<1')
#                 return False, u'Keine anzeigbaren Daten gefunden in\n{0}.\n\n\n     ===----!!!TODO!!!----===\n\nBenutzer anbieten Verzeichnis zu öffnen'.format(dir)
                return False, {"message": "unknown fileytpe", "dir_path": data_dir}
            for geo_file in geo_files:
                if os.path.basename(geo_file).lower().endswith('.shp.xml'):
                    self.msg_log_debug(u'skipping {0}'.format(geo_file))
                    continue
                self.msg_log_debug(geo_file)
                full_path = os.path.join(data_dir, geo_file)
                full_layer_name = layer_name + ' - ' + os.path.basename(geo_file)
                low_case = os.path.basename(geo_file).lower()
                lyr = None

                if low_case.endswith('json'):
                    self.msg_log_debug(u'Open JSON')
                    if False is self.__is_geojson(full_path):
                        if self.__open_with_system(full_path) > 0:
                            if QMessageBox.Yes == self.dlg_yes_no(self.tr(u'py_dlg_base_open_manager').format(layer_url)):
                                self.open_in_manager(data_dir)
                        continue

                if(
                        low_case.endswith('.txt') or
                        low_case.endswith('.pdf') or
                        low_case.endswith('.xls') or
                        low_case.endswith('.xlsx') or
                        low_case.endswith('.doc') or
                        low_case.endswith('.docx') or
                        low_case.endswith('.jpg') or
                        low_case.endswith('.jpeg') or
                        low_case.endswith('.png')
                    ):
                    if self.__open_with_system(full_path) > 0:
                        if QMessageBox.Yes == self.dlg_yes_no(self.tr(u'py_dlg_base_open_manager').format(layer_url)):
                            self.open_in_manager(data_dir)
                    continue
                elif low_case.endswith('.qlr'):
                    lyr = self.__add_layer_definition_file(
                        full_path,
                        QgsProject.instance().layerTreeRoot()
                    )
                elif low_case.endswith('.wmts') or low_case.endswith('.wms'): # for now, we assume it's a WMTS
                    self.msg_log_debug(u'Open WM(T)S')
                    self._open_wmts(layer_name, layer_url)
                    continue
                elif low_case.endswith('.wfs'): # for now, we assume it's a WMTS
                    self.msg_log_debug(u'Open WFS')
                    self._open_wfs(layer_name, layer_url)
                    continue
                elif low_case.endswith('.csv'):
#                     lyr = self.__add_csv_table(full_path, full_layer_name)
                    self.msg_log_debug(u'Open CSV')
                    self._open_csv(full_path)
                    continue
                elif(
                        low_case.endswith('.asc') or
                        low_case.endswith('.tif') or
                        low_case.endswith('.tiff') or
                        low_case.endswith('.img') or
                        low_case.endswith('.jp2') or
                        low_case.endswith('.j2k') or
                        low_case.endswith('.rst') or
                        low_case.endswith('.dem')
                    ):
                    lyr = self.__add_raster_layer(full_path, full_layer_name)
                else:
                    lyr = self.__add_vector_layer(full_path, full_layer_name)
                if lyr is not None:
                    if not lyr.isValid():
                        self.msg_log_debug(u'not valid: {0}'.format(full_path))
                        if QMessageBox.Yes == self.dlg_yes_no(self.tr(u'py_dlg_base_open_manager').format(layer_url)):
                            self.open_in_manager(data_dir)
                        continue
                    QgsProject.instance().addMapLayer(lyr)
                else:
                    self.msg_log_debug(u'could not add layer: {0}'.format(full_path))
            return True, None
        except AttributeError as ae:
            return False, u'AttributeError: {}'.format(ae)
        except TypeError as te:
            return False, u'TypeError: {}'.format(te)
        except:
            return False, sys.exc_info()[0]

    def __add_vector_layer(self, file_name, full_layer_name):
        self.msg_log_debug(u'vector layer'.format(file_name))
        lyr = QgsVectorLayer(
            file_name,
            full_layer_name,
            'ogr'
        )
        return lyr

    def __add_raster_layer(self, file_name, full_layer_name):
        self.msg_log_debug(u'raster layer'.format(file_name))
        lyr = QgsRasterLayer(
            file_name,
            full_layer_name
        )
        return lyr

    def __add_csv_table(self, file_name, full_layer_name):
        self.msg_log_debug(u'csv layer'.format(file_name))
        # file:///f:/scripts/map/points.csv?delimiter=%s&
        # file:///home/bergw/open-data-ktn-cache-dir/42b67af7-f795-48af-9de0-25c8d777bb50/d5ea898b-2ee7-4b52-9b7d-412826d73e45/schuler-und-klassen-kaernten-gesamt-sj-2014-15.csv?encoding=ISO-8859-1&type=csv&delimiter=;&geomType=none&subsetIndex=no&watchFile=no
        # file:///C:/Users/bergw/_TEMP/open-data-ktn-cache-2/wohnbevgemeinzeljahre-2014-WINDOWS.csv?encoding=windows-1252&type=csv&delimiter=%5Ct;&geomType=none&subsetIndex=no&watchFile=no
        slashes = '//'
        if os.name == 'nt':
            slashes += '/'
        lyr_src = u'file:{0}{1}?encoding=ISO-8859-1&type=csv&delimiter=;&geomType=none&subsetIndex=no&watchFile=no'.format(
            slashes,
            file_name
        )
        lyr = QgsVectorLayer(
            lyr_src,
            full_layer_name,
            'delimitedtext'
        )
        return lyr

    def __add_layer_definition_file(self, file_name, root_group):
        """
        shamelessly copied from
        https://github.com/qgis/QGIS/blob/master/src/core/qgslayerdefinition.cpp
        """
        qfile = QFile(file_name)
        if not qfile.open(QIODevice.ReadOnly):
            return None
        doc = QDomDocument()
        if not doc.setContent(qfile):
            return None
        file_info = QFileInfo(qfile)
        QDir.setCurrent(file_info.absoluteDir().path())
        root = QgsLayerTreeGroup()
        ids = doc.elementsByTagName('id')
        for i in range(0, ids.size()):
            id_node = ids.at(i)
            id_elem = id_node.toElement()
            old_id = id_elem.text()
            layer_name = old_id[:-17]
            date_time = QDateTime.currentDateTime()
            new_id = layer_name + date_time.toString('yyyyMMddhhmmsszzz')
            id_elem.firstChild().setNodeValue(new_id)
            tree_layer_nodes = doc.elementsByTagName('layer-tree-layer')
            for j in range(0, tree_layer_nodes.count()):
                layer_node = tree_layer_nodes.at(j)
                layer_elem = layer_node.toElement()
                if old_id == layer_elem.attribute('id'):
                    layer_node.toElement().setAttribute('id', new_id)
        layer_tree_elem = doc.documentElement().firstChildElement('layer-tree-group')
        load_in_legend = True
        if not layer_tree_elem.isNull():
            root.readChildrenFromXML(layer_tree_elem)
            load_in_legend = False
        layers = QgsMapLayer.fromLayerDefinition(doc)
        QgsProject.instance().addMapLayers(layers, load_in_legend)
        nodes = root.children()
        for node in nodes:
            root.takeChild(node)
        del root
        root_group.insertChildNodes(-1, nodes)
        return None

    def _open_wmts(self, name, capabilites_url):
        # Add new HTTPConnection like in source
        # https://github.com/qgis/QGIS/blob/master/src/gui/qgsnewhttpconnection.cpp

        self.msg_log_debug(u'add WM(T)S: Name = {0}, URL = {1}'.format(name, capabilites_url))

        s = QSettings()

        s.setValue(u'qgis/WMS/{0}/password'.format(name), '')
        s.setValue(u'qgis/WMS/{0}/username'.format(name), '')
        s.setValue(u'qgis/WMS/{0}/authcfg'.format(name), '')
        s.setValue(u'qgis/connections-wms/{0}/dpiMode'.format(name), 7)  # refer to https://github.com/qgis/QGIS/blob/master/src/gui/qgsnewhttpconnection.cpp#L229-L247
        s.setValue(u'qgis/connections-wms/{0}/ignoreAxisOrientation'.format(name), False)
        s.setValue(u'qgis/connections-wms/{0}/ignoreGetFeatureInfoURI'.format(name), False)
        s.setValue(u'qgis/connections-wms/{0}/ignoreGetMapURI'.format(name), False)
        s.setValue(u'qgis/connections-wms/{0}/invertAxisOrientation'.format(name), False)
        s.setValue(u'qgis/connections-wms/{0}/referer'.format(name), '')
        s.setValue(u'qgis/connections-wms/{0}/smoothPixmapTransform'.format(name), False)
        s.setValue(u'qgis/connections-wms/{0}/url'.format(name), capabilites_url)

        s.setValue(u'qgis/connections-wms/selected', name)

        if self.settings.auth_propagate and self.settings.authcfg:
            s.setValue(u'qgis/WMS/{0}/authcfg'.format(name), self.settings.authcfg)

        # create new dialog
        wms_dlg = QgsProviderRegistry.instance().createSelectionWidget("wms", self.main_win)
        wms_dlg.addRasterLayer.connect(iface.addRasterLayer)
        wms_dlg.show()


    def _open_wfs(self, name, capabilites_url):
        # Add new HTTPConnection like in source
        # https://github.com/qgis/QGIS/blob/master/src/gui/qgsnewhttpconnection.cpp
        # https://github.com/qgis/QGIS/blob/79616fd8d8285b4eb93adafdfcb97a3e429b832e/src/app/qgisapp.cpp#L3783

        self.msg_log_debug(u'add WFS: Name={0}, original URL={1}'.format(name, capabilites_url))

        # remove additional url parameters, otherwise adding wfs works the frist time only
        # https://github.com/qgis/QGIS/blob/9eee12111567a84f4d4de7e020392b3c01c28598/src/gui/qgsnewhttpconnection.cpp#L199-L214
        url = QUrl(capabilites_url)
        query_string = url.query()

        if query_string:
            query_string = QUrlQuery(query_string)
            query_string.removeQueryItem('SERVICE')
            query_string.removeQueryItem('REQUEST')
            query_string.removeQueryItem('FORMAT')
            query_string.removeQueryItem('service')
            query_string.removeQueryItem('request')
            query_string.removeQueryItem('format')
            #also remove VERSION: shouldn't be necessary, but QGIS sometimes seems to append version=1.0.0
            query_string.removeQueryItem('VERSION')
            query_string.removeQueryItem('version')
            url.setQuery(query_string)

        capabilites_url = url.toString()
        self.msg_log_debug(u'add WFS: Name={0}, base URL={1}'.format(name, capabilites_url))

        s = QSettings()

        self.msg_log_debug(u'existing WFS url: {0}'.format(s.value(u'qgis/connections-wfs/{0}/url'.format(name), '')))

        key_user = u'qgis/WFS/{0}/username'.format(name)
        key_pwd = u'qgis/WFS/{0}/password'.format(name)
        key_referer = u'qgis/connections-wfs/{0}/referer'.format(name)
        key_url = u'qgis/connections-wfs/{0}/url'.format(name)
        key_authcfg = u'qgis/WFS/{0}/authcfg'.format(name)

        s.remove(key_user)
        s.remove(key_pwd)
        s.remove(key_referer)
        s.remove(key_url)
        s.sync()

        s.setValue(key_user, '')
        s.setValue(key_pwd, '')
        s.setValue(key_referer, '')
        s.setValue(key_url, capabilites_url)

        if self.settings.auth_propagate and self.settings.authcfg:
            s.setValue(key_authcfg, self.settings.authcfg)

        s.setValue(u'qgis/connections-wfs/selected', name)

        # create new dialog
        wfs_dlg = QgsProviderRegistry.instance().selectWidget("WFS", self.main_win)

        wfs_dlg = QgsProviderRegistry.instance().createSelectionWidget("WFS", self.main_win)
        wfs_dlg.addVectorLayer.connect(lambda url: iface.addVectorLayer(url, name, "WFS"))
        wfs_dlg.show()


    # CSV区切り自動判定失敗時のダイアログ抑制用フラグ（1回目だけ表示）
    _csv_delim_dialog_answer = None

    def _open_csv(self, full_path):
        # CSVを属性テーブルまたはポイントレイヤとして読み込む（区切り文字自動判定＆緯度経度カラム自動検出）
        self.msg_log_debug(u'add CSV file: {0}'.format(full_path))
        name = os.path.basename(full_path)
        delimiters = [',', ';', '\t', ':', ' ']
        delimiter_names = {',': 'カンマ', ';': 'セミコロン', '\t': 'タブ', ':': 'コロン', ' ': 'スペース'}
        delimiter_counts = {d: 0 for d in delimiters}
        lines = []
        encodings = [
            'utf-8', 'utf-8-sig', 'utf-16', 'cp932', 'shift_jis',
            'euc-jp', 'windows-1252', 'iso-8859-1', 'ascii'
        ]
        delimiter = None
        detected_encoding = None
        for enc in encodings:
            try:
                with open(full_path, encoding=enc) as f:
                    for _ in range(5):
                        line = f.readline()
                        if not line:
                            break
                        lines.append(line)
                for line in lines:
                    for d in delimiters:
                        delimiter_counts[d] += line.count(d)
                sorted_delims = sorted(delimiter_counts.items(), key=lambda x: x[1], reverse=True)
                if len(sorted_delims) > 1 and sorted_delims[0][1] > 0 and sorted_delims[0][1] >= 2 * sorted_delims[1][1]:
                    delimiter = sorted_delims[0][0]
                    self.msg_log_debug(f"CSV delimiter auto-detected: '{delimiter}' ({delimiter_names.get(delimiter, delimiter)}) [{enc}]")
                elif sorted_delims[0][1] > 0 and sorted_delims[1][1] == 0:
                    delimiter = sorted_delims[0][0]
                    self.msg_log_debug(f"CSV delimiter auto-detected (only one type found): '{delimiter}' ({delimiter_names.get(delimiter, delimiter)}) [{enc}]")
                else:
                    self.msg_log_debug(f"CSV delimiter auto-detect ambiguous: {delimiter_counts} [{enc}]")
                    # --- 1回目だけダイアログ表示し、以降は抑制 ---
                    if Util._csv_delim_dialog_answer is None:
                        msg = f"CSVファイルの区切り文字が自動判定できませんでした: {full_path}\nカンマ・セミコロン・タブ・コロン・スペースのいずれかで明確に区切られている必要があります。"
                        QMessageBox.warning(self.main_win, self.dlg_caption, msg)
                        Util._csv_delim_dialog_answer = True
                    return
                detected_encoding = enc
                # 先頭行からカラム名を取得（クォート除去強化＆デバッグ出力追加）
                header = lines[0] if lines else ''
                columns = [col.strip().replace('"','').replace("'",'') for col in header.strip().split(delimiter)] if header else []
                self.msg_log_debug(f"CSV columns: {columns}")
                # 緯度経度カラム名候補
                lat_candidates = ['lat', 'latitude', 'y']
                lon_candidates = ['lon', 'lng', 'long', 'longitude', 'x']
                # lat_candidates/lon_candidatesリストは不要。判定は下記関数で行う。

                def match_lat_col(c):
                    cl = c.lower()
                    # 完全一致（lat_candidatesのいずれか）
                    if cl in lat_candidates:
                        return True
                    # サフィックス一致: _lat, -lat, _latitude, -latitude, _y, -y など
                    for b in lat_candidates:
                        if cl.endswith('_' + b) or cl.endswith('-' + b):
                            return True
                    return False

                def match_lon_col(c):
                    cl = c.lower()
                    if cl in lon_candidates:
                        return True
                    for b in lon_candidates:
                        if cl.endswith('_' + b) or cl.endswith('-' + b):
                            return True
                    return False
                lat_col = None
                lon_col = None
                # まず日本語カラム名（部分一致）を優先
                for c in columns:
                    if ('緯度' in c) and lat_col is None:
                        lat_col = c
                    if ('経度' in c) and lon_col is None:
                        lon_col = c
                # 日本語でなければ自動判定
                if not (lat_col and lon_col):
                    lat_col = next((c for c in columns if match_lat_col(c)), None)
                    lon_col = next((c for c in columns if match_lon_col(c)), None)
                # 日本語カラム名が両方見つかった場合のみ数値判定
                def is_float(s):
                    try:
                        # 前後の空白・クォートを除去してから判定
                        return float(s.strip().strip('"\'')) is not None
                    except:
                        return False
                if lat_col and lon_col:
                    lat_idx = columns.index(lat_col)
                    lon_idx = columns.index(lon_col)
                    valid_count = 0
                    for row in lines[1:6]:
                        vals = row.strip().split(delimiter)
                        if len(vals) > max(lat_idx, lon_idx):
                            if is_float(vals[lat_idx]) and is_float(vals[lon_idx]):
                                valid_count += 1
                    if valid_count >= 2:
                        self.msg_log_debug(f"緯度経度カラム自動検出: lat={lat_col}, lon={lon_col} (数値判定OK) [{valid_count}行]")
                    else:
                        self.msg_log_debug(f"緯度経度カラム候補はあるが数値でない: lat={lat_col}, lon={lon_col}")
                        lat_col = None
                        lon_col = None
                else:
                    self.msg_log_debug(f"緯度経度カラムが見つかりません: columns={columns}")
                break
            except Exception as e:
                self.msg_log_debug(f"CSV delimiter auto-detect failed with {enc}: {e}")
                lines = []
                delimiter_counts = {d: 0 for d in delimiters}
        else:
            QMessageBox.warning(self.main_win, self.dlg_caption, f"CSVファイルの区切り文字自動判定に失敗しました: {full_path}\nUTF-8/CP932/ANSI/Shift_JIS/ISO-8859-1のいずれでも開けませんでした。")
            return
        # QgsVectorLayerのURIにdelimiterとencodingパラメータを付与
        uri = f"file:///{full_path}?delimiter={delimiter}&encoding={detected_encoding}"
        # 緯度経度カラムがあればポイントレイヤとして追加
        if lat_col and lon_col:
            uri += f"&xField={lon_col}&yField={lat_col}&crs=EPSG:4326"
            lyr = QgsVectorLayer(uri, name, "delimitedtext")
            if not lyr.isValid():
                QMessageBox.warning(self.main_win, self.dlg_caption, f"CSVファイルの読み込みに失敗しました: {full_path}")
                return
            QgsProject.instance().addMapLayer(lyr)
            self.msg_log_debug(f"CSVをポイントレイヤとして追加しました: {full_path} (delimiter={delimiter}, encoding={detected_encoding}, xField={lon_col}, yField={lat_col})")
        else:
            lyr = QgsVectorLayer(uri, name, "delimitedtext")
            if not lyr.isValid():
                QMessageBox.warning(self.main_win, self.dlg_caption, f"CSVファイルの読み込みに失敗しました: {full_path}")
                return
            if lyr.wkbType() == 100:  # QgsWkbTypes.NoGeometry == 100
                QgsProject.instance().addMapLayer(lyr)
                self.msg_log_debug(f"CSVを属性テーブルとして追加しました: {full_path} (delimiter={delimiter}, encoding={detected_encoding})")
            else:
                from qgis.utils import iface
                if iface is not None:
                    iface.addVectorLayer(uri, name, "delimitedtext")
                else:
                    QMessageBox.warning(self.main_win, self.dlg_caption, "QGISインターフェースが利用できません (iface is None)。CSVレイヤを追加できません。")


    def __open_with_system(self, file_name):
        code = None
        if sys.platform.startswith('darwin'):
            code = subprocess.call(('open', file_name))
        elif os.name == 'nt':
            win_code = os.startfile(file_name)
            if win_code != 0:
                code = -1
        elif os.name == 'posix':
            code = subprocess.call(('xdg-open', file_name))
        self.msg_log_debug(u'Exit Code: {0}'.format(code))
        return code

    def __is_geojson(self, file_path):
        try:
            with open(file_path) as json_file:
                data = json.load(json_file)

                if data.get('features') is not None:
                    self.msg_log_debug('is_geojson: "features" found')
                    return True
                elif data.get('type') =="FeatureCollection":
                    self.msg_log_debug('is_geojson: "FeatureCollection" found')
                    return True
                else:
                    return False
        except:
            self.msg_log_debug(u'Error reading json'.format(sys.exc_info()[1]))
            return False

    def dlg_information(self, msg):
        QMessageBox.information(self.main_win, self.dlg_caption, msg)

    def dlg_warning(self, msg):
        QMessageBox.warning(self.main_win, self.dlg_caption, msg)

    def dlg_yes_no(self, msg):
        return QMessageBox.question(
            self.main_win,
            self.dlg_caption,
            msg,
            QMessageBox.Yes,
            QMessageBox.No
        )

    def msg_log_debug(self, msg):
        if self.settings.debug is True:
            QgsMessageLog.logMessage(msg, self.dlg_caption, Qgis.Info)

    def msg_log_warning(self, msg):
        QgsMessageLog.logMessage(msg, self.dlg_caption, Qgis.Warning)

    def msg_log_error(self, msg):
        QgsMessageLog.logMessage(msg, self.dlg_caption, Qgis.Critical)

    def msg_log_last_exception(self):
        exc_type, exc_value, exc_traceback = sys.exc_info()
        self.msg_log_error(
            u'\nexc_type: {}\nexc_value: {}\nexc_traceback: {}'
            .format(exc_type, exc_value, exc_traceback)
        )

    def remove_newline(self, url):
        if '\r\n' in url:
            self.msg_log_debug(u'Windows style new line found in resource url')
            url = url.replace('\r\n', '')
        if '\n' in url:
            self.msg_log_debug(u'Linux style new line found in resource url')
            url = url.replace('\n', '')
        return url

    def resolve(self, name, base_path=None):
        """http://gis.stackexchange.com/a/130031/8673"""
        if not base_path:
            base_path = os.path.dirname(os.path.realpath(__file__))
        return os.path.join(base_path, name)

    def open_in_manager(self, file_path):
        """http://stackoverflow.com/a/6631329/1504487"""
        self.msg_log_debug(
            u'open_in_manager, os.name: {} platform: {}\npath: {}'
            .format(os.name, sys.platform, file_path)
        )
        if sys.platform == 'darwin':
            subprocess.Popen(['open', file_path])
        elif sys.platform == 'linux' or sys.platform == 'linux2':
            subprocess.Popen(['xdg-open', file_path])
        elif os.name == 'nt' or sys.platform == 'win32':
            file_path = os.path.normpath(file_path)
            self.msg_log_debug(u'normalized path: {}'.format(file_path))
            subprocess.Popen(['explorer', file_path])

    def str2bool(self, v):
        """http://stackoverflow.com/a/715468/1504487"""
        return v.lower() in ("yes", "true", "t", "1")
