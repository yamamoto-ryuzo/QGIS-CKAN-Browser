import sqlite3
import os
import json

def save_ckan_packages_to_sqlite(db_path, packages):
    # ログ出力は呼び出し元で行うこと
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # テーブル作成
    c.execute('''CREATE TABLE IF NOT EXISTS packages (
        id TEXT PRIMARY KEY,
        title TEXT,
        notes TEXT,
        author TEXT,
        author_email TEXT,
        license_id TEXT,
        raw_json TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS resources (
        id TEXT PRIMARY KEY,
        package_id TEXT,
        format TEXT,
        url TEXT,
        name TEXT,
        raw_json TEXT,
        FOREIGN KEY(package_id) REFERENCES packages(id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS groups (
        id TEXT PRIMARY KEY,
        name TEXT,
        title TEXT,
        description TEXT,
        raw_json TEXT
    )''')
    # データ挿入
    for pkg in packages:
        c.execute('''INSERT OR REPLACE INTO packages (id, title, notes, author, author_email, license_id, raw_json) VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (
                pkg.get('id'),
                pkg.get('title'),
                pkg.get('notes'),
                pkg.get('author'),
                pkg.get('author_email'),
                pkg.get('license_id'),
                json.dumps(pkg, ensure_ascii=False)
            )
        )
        for res in pkg.get('resources', []):
            c.execute('''INSERT OR REPLACE INTO resources (id, package_id, format, url, name, raw_json) VALUES (?, ?, ?, ?, ?, ?)''',
                (
                    res.get('id'),
                    pkg.get('id'),
                    res.get('format'),
                    res.get('url'),
                    res.get('name'),
                    json.dumps(res, ensure_ascii=False)
                )
            )
    conn.commit()
    conn.close()
    # ログ出力は呼び出し元で行うこと

def save_ckan_groups_to_sqlite(db_path, groups):
    """
    CKANグループリストをSQLiteに保存
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS groups (
        id TEXT PRIMARY KEY,
        name TEXT,
        title TEXT,
        description TEXT,
        raw_json TEXT
    )''')
    c.execute('DELETE FROM groups')
    for group in groups:
        c.execute('''INSERT OR REPLACE INTO groups (id, name, title, description, raw_json) VALUES (?, ?, ?, ?, ?)''',
            (
                group.get('id'),
                group.get('name'),
                group.get('title'),
                group.get('description'),
                json.dumps(group, ensure_ascii=False)
            )
        )
    conn.commit()
    conn.close()

if __name__ == '__main__':
    # 例: all_results = ... (全データセットのリスト)
    # save_ckan_packages_to_sqlite('ckan_cache.db', all_results)
    pass
