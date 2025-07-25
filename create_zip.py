
import os
import zipfile


# 必要最小限のファイル・ディレクトリのみを配布ZIPに含める
PLUGIN_DIR = 'CKAN-Browser'
INCLUDE = [
    'LICENSE',
    'plugins.xml',
    'README.md',
]
# 除外したいファイル・ディレクトリ（例: __pycache__, .git, テストや開発用スクリプト等）
EXCLUDE_DIRS = {'__pycache__', '.git', 'scripts', 'img', 'tests'}
EXCLUDE_FILES = {'build.sh', 'Makefile', 'pylintrc', 'logo-license.txt'}
ZIP_NAME = 'CKANBrowser.zip'

def zip_with_plugin_dir_minimal(ziph, plugin_dir):
    for root, dirs, files in os.walk(plugin_dir):
        # 除外ディレクトリをスキップ
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for file in files:
            if file in EXCLUDE_FILES:
                continue
            abs_path = os.path.join(root, file)
            rel_path = os.path.join(plugin_dir, os.path.relpath(abs_path, plugin_dir))
            ziph.write(abs_path, rel_path)

def main():
    with zipfile.ZipFile(ZIP_NAME, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zip_with_plugin_dir_minimal(zipf, PLUGIN_DIR)
        for item in INCLUDE:
            if os.path.isfile(item):
                zipf.write(item, os.path.basename(item))
    print(f'{ZIP_NAME} を作成しました（最小構成でCKAN-Browserディレクトリごと格納）')

if __name__ == '__main__':
    main()
