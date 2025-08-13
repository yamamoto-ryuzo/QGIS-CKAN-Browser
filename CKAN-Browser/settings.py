# -*- coding: utf-8 -*-

from PyQt5.QtCore import QSettings
import os
import configparser

from qgis.core import QgsMessageLog, Qgis


class Settings:

    def __init__(self):
        self.debug = True
        self.results_limit = 50
        self.request_timeout = 15
        self.ckan_url = None
        self.selected_ckan_servers = ''
        self.custom_servers = {}
        self.authcfg = None
        self.cache_dir = None
        self.DLG_CAPTION = u'CKAN-Browser'
        self.KEY_CACHE_DIR = 'ckan_browser/cache_dir'
        self.KEY_CKAN_API = 'ckan_browser/ckan_api'
        self.KEY_AUTHCFG = 'ckan_browser/authcfg'
        self.KEY_AUTH_PROPAGATE = 'ckan_browser/auth_propagate'
        self.KEY_SELECTED_CKAN_SERVERS = 'ckan_browser/selected_ckan_servers'
        self.KEY_CUSTOM_SERVERS = 'ckan_browser/custom_ckan_servers'
        self.KEY_SHOW_DEBUG_INFO = 'ckan_browser/show_debug_info'
        self.version = self._determine_version()

    def load(self):
        import json
        qgis_settings = QSettings()
        self.cache_dir = qgis_settings.value(self.KEY_CACHE_DIR, '')
        if self.cache_dir is None:
            self.cache_dir = ''
        self.ckan_url = qgis_settings.value(self.KEY_CKAN_API, 'https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/')
        # サーバリストはキャッシュフォルダに保存
        if not self.cache_dir:
            # デフォルトキャッシュディレクトリ
            self.cache_dir = os.path.join(os.path.expanduser('~'), '.ckan_browser_cache')
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir, exist_ok=True)
        servers_path = os.path.join(self.cache_dir, 'ckan_servers.json')
        if os.path.exists(servers_path):
            try:
                with open(servers_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.selected_ckan_servers = data.get('selected_ckan_servers', '')
                    # 既存データがstrの場合はtype=CKANでラップ
                    loaded_custom = data.get('custom_servers', {})
                    new_custom = {}
                    for name, val in loaded_custom.items():
                        if isinstance(val, dict) and 'url' in val and 'type' in val:
                            new_custom[name] = val
                        elif isinstance(val, str):
                            new_custom[name] = {'url': val, 'type': 'CKAN'}
                        else:
                            # 不正な形式はスキップ
                            continue
                    self.custom_servers = new_custom
            except Exception:
                self.selected_ckan_servers = ''
                self.custom_servers = {}
        else:
            self.selected_ckan_servers = ''
            self.custom_servers = {}
        self.debug = qgis_settings.value(self.KEY_SHOW_DEBUG_INFO, False, bool)
        self.authcfg = qgis_settings.value(self.KEY_AUTHCFG, '')
        self.auth_propagate = qgis_settings.value(self.KEY_AUTH_PROPAGATE, False, bool)

    def save(self):
        import json
        qgis_settings = QSettings()
        qgis_settings.setValue(self.KEY_CACHE_DIR, self.cache_dir)
        qgis_settings.setValue(self.KEY_CKAN_API, self.ckan_url)
        qgis_settings.setValue(self.KEY_AUTHCFG, self.authcfg)
        qgis_settings.setValue(self.KEY_AUTH_PROPAGATE, self.auth_propagate)
        qgis_settings.setValue(self.KEY_SHOW_DEBUG_INFO, self.debug)
        # サーバリストはキャッシュフォルダに保存
        if not self.cache_dir:
            self.cache_dir = os.path.join(os.path.expanduser('~'), '.ckan_browser_cache')
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir, exist_ok=True)
        servers_path = os.path.join(self.cache_dir, 'ckan_servers.json')
        # custom_serversの値は{name: {url, type}}形式で保存
        data = {
            'selected_ckan_servers': self.selected_ckan_servers,
            'custom_servers': self.custom_servers
        }
        try:
            with open(servers_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            QgsMessageLog.logMessage(f'Failed to save ckan_servers.json: {e}', 'CKAN-Browser', Qgis.Warning)

    def _determine_version(self):
        """http://gis.stackexchange.com/a/169266/8673"""
        # error handling?
        config = configparser.ConfigParser()
        config.read(os.path.join(os.path.dirname(__file__), 'metadata.txt'))

        return config.get('general', 'version')
