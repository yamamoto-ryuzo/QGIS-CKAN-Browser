
# CKAN-Browser プラグイン（yamamoto版）

## 概要
QGIS用CKAN-Browserプラグインの拡張・修正版です。  
CKANオープンデータポータルからデータセットを検索・取得し、QGIS上で活用できます。

## 主な追加・修正機能
- ローカルSQLiteキャッシュ検索時もカテゴリ（グループ）フィルタが有効
- CSVファイルの区切り文字自動判定（カンマ・セミコロン・タブ・コロン・スペース対応）
- CSVファイルの文字コード自動判定（UTF-8/CP932）とQGISレイヤ追加時のencoding自動指定
- CSVに緯度経度カラムがあれば自動でポイントジオメトリ化
- UIの一部改善
- バージョン・更新履歴は `metadata_yamamoto.txt`, `Changlog_yamamoto.txt` で管理

## 使い方
1. QGISで本プラグインを有効化
2. CKANサーバを選択し、検索・カテゴリ・データ形式で絞り込み
3. データセットを選択し、リソースをダウンロード・地図に追加
4. CSVの場合は自動で区切り文字・文字コード・ジオメトリ判定

## 注意事項
- QGIS 3.x/4.x対応
- 旧バージョンとの互換性に注意
- 詳細なバージョン履歴は `Changlog_yamamoto.txt` を参照

## 主な改修PYファイル
- `ckan_browser_dialog.py`（UI・検索・カテゴリ・リソース処理）
- `util.py`（CSV自動判定・レイヤ追加・各種ユーティリティ）

## バージョン・更新履歴
- バージョン情報は `metadata_yamamoto.txt` を参照
- 更新履歴は `Changlog_yamamoto.txt` を参照

## 連絡先
- GitHub: [yamamoto-ryuzo](https://github.com/yamamoto-ryuzo)
