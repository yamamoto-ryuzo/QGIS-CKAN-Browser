

# CKAN-Browser プラグイン（yamamoto版）
# CKAN-Browser Plugin (yamamoto version)


# 開発方針 / Development Policy
東京オープンデータハッカソン（ビジュアライズ部門）への参加をきっかけに、東京オープンデータをQGISで検索・変換・取り込み・装飾まで簡単にできるよう機能強化を行います。
https://odhackathon.metro.tokyo.lg.jp/

Inspired by participation in the Tokyo Open Data Hackathon (Visualization Division), this version aims to make it easier to search, convert, import, and style Tokyo open data in QGIS through enhanced features.
https://odhackathon.metro.tokyo.lg.jp/

　【参考】  
・DATA GO.JP:
　https://www.data.go.jp/data/api/3
・G空間情報センター:
　https://www.geospatial.jp/ckan/api/3
・東京都オープンデータカタログサイト
　 https://catalog.data.metro.tokyo.lg.jp/api/3
・地質調査総合センターデータカタログ
　https://data.gsj.jp/gkan/api/3
・姫路市・播磨圏域連携中枢都市圏オープンデータカタログサイト
　https://city.himeji.gkan.jp/gkan/api/3
・ビッグデータ&オープンデータ・イニシアティブ九州
　https://data.bodik.jp/

## 概要 / Overview
QGIS用CKAN-Browserプラグインの拡張・修正版です。
CKANオープンデータポータルからデータセットを検索・取得し、QGIS上で活用できます。

This is an enhanced and modified version of the CKAN-Browser plugin for QGIS.
You can search and download datasets from CKAN open data portals and use them in QGIS.


## 主な追加・修正機能 / Main Added & Improved Features
- ローカルSQLiteキャッシュ検索時もカテゴリ（グループ）フィルタが有効
    - Category (group) filter is available even when searching local SQLite cache
- CSVファイルの区切り文字自動判定（カンマ・セミコロン・タブ・コロン・スペース対応）
    - Automatic delimiter detection for CSV files (comma, semicolon, tab, colon, space)
- CSVファイルの文字コード自動判定（UTF-8/CP932）とQGISレイヤ追加時のencoding自動指定
    - Automatic encoding detection for CSV files (UTF-8/CP932) and auto-setting when adding as QGIS layer
- CSVに緯度経度カラムがあれば自動でポイントジオメトリ化
    - Automatic point geometry creation if latitude/longitude columns exist in CSV
- UIの一部改善
    - Some UI improvements
- バージョン・更新履歴は `metadata_yamamoto.txt`, `Changlog_yamamoto.txt` で管理
    - Version and changelog are managed in `metadata_yamamoto.txt` and `Changlog_yamamoto.txt`


## 使い方 / How to Use
1. QGISで本プラグインを有効化
    - Enable this plugin in QGIS
2. CKANサーバを選択し、検索・カテゴリ・データ形式で絞り込み
    - Select a CKAN server, filter by search, category, and data format
3. データセットを選択し、リソースをダウンロード・地図に追加
    - Select a dataset, download resources, and add them to the map
4. CSVの場合は自動で区切り文字・文字コード・ジオメトリ判定
    - For CSV, delimiter, encoding, and geometry are detected automatically


## 注意事項 / Notes
- QGIS 3.x/4.x対応
    - Supports QGIS 3.x/4.x
- 旧バージョンとの互換性に注意
    - Be careful about compatibility with older versions
- 詳細なバージョン履歴は `Changlog_yamamoto.txt` を参照
    - See `Changlog_yamamoto.txt` for detailed version history


## 主な改修PYファイル / Main Modified Python Files
- `ckan_browser_dialog.py`（UI・検索・カテゴリ・リソース処理）
    - UI, search, category, resource handling
- `util.py`（CSV自動判定・レイヤ追加・各種ユーティリティ）
    - CSV auto-detection, layer addition, utilities


## バージョン・更新履歴 / Version & Changelog
- バージョン情報は `metadata_yamamoto.txt` を参照
    - See `metadata_yamamoto.txt` for version info
- 更新履歴は `Changlog_yamamoto.txt` を参照
    - See `Changlog_yamamoto.txt` for changelog


## 連絡先 / Contact
- GitHub: [yamamoto-ryuzo](https://github.com/yamamoto-ryuzo)

