# 多言語対応QGISプラグインのためのtsファイル雛形自動生成スクリプト
# 対応言語: en, fr, de, es, it, pt, ja, zh, ru, hi
# 既存のCKANBrowser_ja.ts等を参考に、なければ新規作成
import os
import shutil

i18n_dir = os.path.join(os.path.dirname(__file__), 'CKAN-Browser', 'i18n')
base_ts = os.path.join(i18n_dir, 'CKANBrowser_en.ts')
lang_codes = [
    ('en', 'en'),
    ('fr', 'fr'),
    ('de', 'de'),
    ('es', 'es'),
    ('it', 'it'),
    ('pt', 'pt'),
    ('ja', 'ja'),
    ('zh', 'zh_CN'),
    ('ru', 'ru'),
    ('hi', 'hi'),
]

for code, qtcode in lang_codes:
    ts_name = f'CKANBrowser_{code}.ts'
    ts_path = os.path.join(i18n_dir, ts_name)
    if not os.path.exists(ts_path):
        # 英語雛形をコピーして新規作成
        shutil.copy(base_ts, ts_path)
        with open(ts_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        # 言語コードを書き換え
        with open(ts_path, 'w', encoding='utf-8') as f:
            for line in lines:
                if line.strip().startswith('<TS'):
                    f.write(f'<TS version="2.1" language="{qtcode}">\n')
                else:
                    f.write(line)
        print(f'Created {ts_name}')
    else:
        print(f'Exists {ts_name}')
print('tsファイル雛形の準備が完了しました。')
