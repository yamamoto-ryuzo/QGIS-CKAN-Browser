# QGIS-CKAN-Browser 配布用ZIP作成スクリプト
# 実行するとCKAN-Browserディレクトリと必要ファイルをまとめてZIP化します

import os
import zipfile

# 配布に含めるファイル・ディレクトリ
INCLUDE = [
    'CKAN-Browser',
    'LICENSE',
    'README.md',
    'plugins.xml',
    'logo-license.txt',
]

# 出力ファイル名
OUTPUT_ZIP = 'CKANBrowser.zip'


def zipdir(path, ziph, arc_prefix=''):
    for root, dirs, files in os.walk(path):
        for file in files:
            abs_path = os.path.join(root, file)
            rel_path = os.path.relpath(abs_path, os.path.dirname(path))
            arcname = os.path.join(arc_prefix, rel_path)
            ziph.write(abs_path, arcname)


def main():
    with zipfile.ZipFile(OUTPUT_ZIP, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for item in INCLUDE:
            if os.path.isdir(item):
                zipdir(item, zipf, arc_prefix=item)
            elif os.path.isfile(item):
                zipf.write(item, item)
    print(f'配布用ZIP {OUTPUT_ZIP} を作成しました')


if __name__ == '__main__':
    main()
