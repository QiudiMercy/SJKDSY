"""
导入成都 POI 数据 (371K 行) 到 SQLite 'poi' 表
使用方法: python scripts/import_poi.py
"""
import csv
import sys
import os
import sqlite3

# 确保可以导入项目模块
_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_script_dir)
_src_path = os.path.join(_project_root, 'scr', 'takeme')
sys.path.insert(0, _src_path)

from core.config import dbmanager

CSV_PATH = os.path.join(_project_root, 'chengdu_poi.csv')
BATCH_SIZE = 10000

def main():
    print("开始批量导入 POI 数据...")
    db_path = dbmanager.db_url
    
    if not os.path.exists(CSV_PATH):
        print(f"找不到 POI 数据源文件 '{CSV_PATH}'，跳过导入。")
        return
        
    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:

        cursor.execute("SELECT COUNT(*) FROM poi")
        count_before = cursor.fetchone()[0]
        print(f"现有 POI 数据: {count_before} 条")
        
        if count_before > 0:
            cursor.execute("DELETE FROM poi")
            conn.commit()
            print("已清空现有数据")
            
        imported = 0
        skipped = 0
        batch = []
        
        with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    lng_str, lat_str = row['location'].split(',')
                    lng = float(lng_str.strip())
                    lat = float(lat_str.strip())
                    
                    raw_type = row['type'].strip()
                    poi_type = raw_type.split(';')[0]
                    
                    batch.append((
                        row['id'].strip(),
                        row['name'].strip(),
                        poi_type,
                        lng,
                        lat
                    ))
                    imported += 1
                    
                    if len(batch) >= BATCH_SIZE:
                        cursor.executemany(
                            "INSERT OR IGNORE INTO poi (poi_uid, name, type, lng, lat) VALUES (?, ?, ?, ?, ?)",
                            batch
                        )
                        conn.commit()
                        print(f"已导入 {imported} 条...")
                        batch = []
                except Exception:
                    skipped += 1
                    continue
                    
        if batch:
            cursor.executemany(
                "INSERT OR IGNORE INTO poi (poi_uid, name, type, lng, lat) VALUES (?, ?, ?, ?, ?)",
                batch
            )
            conn.commit()
            
        cursor.execute("SELECT COUNT(*) FROM poi")
        final_count = cursor.fetchone()[0]
        
        print(f"\n导入完成！共 {final_count} 条（成功 {imported}，跳过 {skipped}）")
        
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    main()
