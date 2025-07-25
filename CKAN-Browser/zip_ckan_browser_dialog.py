import zipfile
import os

def zip_ckan_browser_dialog():
    src = os.path.abspath(os.path.join(os.path.dirname(__file__), 'ckan_browser_dialog.py'))
    dst = os.path.join(os.path.dirname(src), 'ckan_browser_dialog.zip')
    with zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(src, arcname='ckan_browser_dialog.py')
    print('Created:', dst)

if __name__ == '__main__':
    zip_ckan_browser_dialog()
