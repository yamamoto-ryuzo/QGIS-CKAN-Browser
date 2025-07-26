

import os
import zipfile
import fnmatch

# 配布対象ディレクトリとZIP名
PLUGIN_DIR = 'CKAN-Browser'
ZIP_NAME = 'CKANBrowser.zip'

# ルートに含める追加ファイル
INCLUDE = [
    'LICENSE',
    'plugins.xml',
    'README.md',
]

# 除外パターン
EXCLUDE_DIRS = {'__pycache__', '.git', 'scripts', 'img', 'tests'}
EXCLUDE_FILES = {'build.sh', 'Makefile', 'pylintrc', 'logo-license.txt'}
EXCLUDE_PATTERNS = ['*.pyc', '*.pyo', '*.zip', '.DS_Store']

def should_exclude(name):
    for pat in EXCLUDE_PATTERNS:
        if fnmatch.fnmatch(name, pat):
            return True
    return False

def zip_plugin_dir(ziph, plugin_dir):
    for root, dirs, files in os.walk(plugin_dir):
        # 除外ディレクトリ
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for file in files:
            if file in EXCLUDE_FILES or should_exclude(file):
                continue
            abs_path = os.path.join(root, file)
            rel_path = os.path.relpath(abs_path, os.path.dirname(plugin_dir))
            ziph.write(abs_path, rel_path)

def main():
    with zipfile.ZipFile(ZIP_NAME, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zip_plugin_dir(zipf, PLUGIN_DIR)
        for item in INCLUDE:
            if os.path.isfile(item):
                zipf.write(item, os.path.basename(item))
    print(f'{ZIP_NAME} を作成しました（CKAN-Browserディレクトリごと格納）')

if __name__ == '__main__':
    main()
