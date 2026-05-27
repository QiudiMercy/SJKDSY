"""
导入成都 POI 数据 (371K 行) 到 SQLite 'poi' 数据表 (完全手写 SQL 方案)
使用方法: 在项目根目录下运行 python scripts/import_poi.py
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
    print("开始原生 SQL 批量导入 POI 数据...")
    db_path = dbmanager.db_url
    
    if not os.path.exists(CSV_PATH):
        print(f"错误: 找不到 POI 数据源文件 '{CSV_PATH}'。")
        print("如果您已经初始化了数据库 'takeme.db'，则无需再次导入数据。")
        return
        
    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. 检查 'poi' 表中数据条数
        cursor.execute("SELECT COUNT(*) FROM poi")
        count_before = cursor.fetchone()[0]
        print(f"现有 POI 数据: {count_before} 条")
        
        # 2. 清空旧数据
        if count_before > 0:
            cursor.execute("DELETE FROM poi")
            conn.commit()
            print("已清空现有数据")
            
        # 3. 开启事务高速批量导入
        imported = 0
        skipped = 0
        batch = []
        
        # 使用 utf-8-sig 处理可能存在的 BOM 头
        with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    # 解析经纬度: "103.849109,30.820077"
                    lng_str, lat_str = row['location'].split(',')
                    lng = float(lng_str.strip())
                    lat = float(lat_str.strip())
                    
                    # 归属分类分级，提取第一个
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
                    
        # 导入尾批
        if batch:
            cursor.executemany(
                "INSERT OR IGNORE INTO poi (poi_uid, name, type, lng, lat) VALUES (?, ?, ?, ?, ?)",
                batch
            )
            conn.commit()
            
        cursor.execute("SELECT COUNT(*) FROM poi")
        final_count = cursor.fetchone()[0]
        
        print(f"\n导入完成！")
        print(f"成功导入: {imported} 条")
        print(f"跳过: {skipped} 条")
        print(f"数据库总计: {final_count} 条")
        
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    main()
