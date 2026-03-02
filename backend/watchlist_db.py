# 自选股数据模型和存储层
import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "watchlist.db")

def get_db():
    """获取数据库连接"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """初始化数据库表"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 自选分组表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS watchlist_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1,
            name VARCHAR(50) NOT NULL,
            color VARCHAR(10) DEFAULT '#409EFF',
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 自选股票表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS watchlist_stocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1,
            group_id INTEGER NOT NULL,
            symbol VARCHAR(20) NOT NULL,
            stock_name VARCHAR(50),
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (group_id) REFERENCES watchlist_groups(id) ON DELETE CASCADE,
            UNIQUE(user_id, group_id, symbol)
        )
    ''')
    
    # 创建默认分组（如果不存在）
    cursor.execute('SELECT COUNT(*) FROM watchlist_groups')
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO watchlist_groups (user_id, name, color, sort_order)
            VALUES (1, '我的自选', '#409EFF', 0)
        ''')
    
    conn.commit()
    conn.close()

# ==================== 分组操作 ====================

def get_all_groups(user_id: int = 1) -> List[Dict]:
    """获取用户所有分组"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT g.*, 
               (SELECT COUNT(*) FROM watchlist_stocks WHERE group_id = g.id) as stock_count
        FROM watchlist_groups g
        WHERE g.user_id = ?
        ORDER BY g.sort_order
    ''', (user_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def create_group(user_id: int, name: str, color: str = '#409EFF') -> Dict:
    """创建新分组"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 获取最大排序值
    cursor.execute('SELECT MAX(sort_order) FROM watchlist_groups WHERE user_id = ?', (user_id,))
    max_order = cursor.fetchone()[0] or -1
    
    cursor.execute('''
        INSERT INTO watchlist_groups (user_id, name, color, sort_order)
        VALUES (?, ?, ?, ?)
    ''', (user_id, name, color, max_order + 1))
    
    group_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {"id": group_id, "name": name, "color": color, "sort_order": max_order + 1}

def update_group(group_id: int, name: str = None, color: str = None) -> bool:
    """更新分组"""
    conn = get_db()
    cursor = conn.cursor()
    
    updates = []
    params = []
    if name:
        updates.append("name = ?")
        params.append(name)
    if color:
        updates.append("color = ?")
        params.append(color)
    
    if not updates:
        return False
    
    updates.append("updated_at = CURRENT_TIMESTAMP")
    params.append(group_id)
    
    cursor.execute(f'''
        UPDATE watchlist_groups SET {', '.join(updates)}
        WHERE id = ?
    ''', params)
    
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    
    return affected > 0

def delete_group(group_id: int) -> bool:
    """删除分组（级联删除自选股）"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 先删除组内自选股
    cursor.execute('DELETE FROM watchlist_stocks WHERE group_id = ?', (group_id,))
    # 再删除分组
    cursor.execute('DELETE FROM watchlist_groups WHERE id = ?', (group_id,))
    
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    
    return affected > 0

# ==================== 自选股操作 ====================

def get_watchlist_stocks(group_id: int, user_id: int = 1) -> List[Dict]:
    """获取分组内自选股列表（不含实时行情）"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, group_id, symbol, stock_name, sort_order, created_at
        FROM watchlist_stocks
        WHERE user_id = ? AND group_id = ?
        ORDER BY sort_order
    ''', (user_id, group_id))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def add_stock(user_id: int, group_id: int, symbol: str, stock_name: str = '') -> bool:
    """添加自选股"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 获取最大排序值
    cursor.execute('''
        SELECT MAX(sort_order) FROM watchlist_stocks 
        WHERE user_id = ? AND group_id = ?
    ''', (user_id, group_id))
    max_order = cursor.fetchone()[0] or -1
    
    try:
        cursor.execute('''
            INSERT INTO watchlist_stocks (user_id, group_id, symbol, stock_name, sort_order)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, group_id, symbol, stock_name, max_order + 1))
        conn.commit()
        added = True
    except sqlite3.IntegrityError:
        added = False  # 已存在
    finally:
        conn.close()
    
    return added

def remove_stock(stock_id: int, user_id: int = 1) -> bool:
    """删除自选股"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        DELETE FROM watchlist_stocks WHERE id = ? AND user_id = ?
    ''', (stock_id, user_id))
    
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    
    return affected > 0

def move_stock(stock_id: int, new_group_id: int, user_id: int = 1) -> bool:
    """移动自选股到其他分组"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 获取新分组的最大排序值
    cursor.execute('''
        SELECT MAX(sort_order) FROM watchlist_stocks 
        WHERE user_id = ? AND group_id = ?
    ''', (user_id, new_group_id))
    max_order = cursor.fetchone()[0] or -1
    
    cursor.execute('''
        UPDATE watchlist_stocks 
        SET group_id = ?, sort_order = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND user_id = ?
    ''', (new_group_id, max_order + 1, stock_id, user_id))
    
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    
    return affected > 0

def is_in_watchlist(user_id: int, symbol: str, group_id: int = None) -> bool:
    """检查股票是否在自选列表中"""
    conn = get_db()
    cursor = conn.cursor()
    
    if group_id:
        cursor.execute('''
            SELECT COUNT(*) FROM watchlist_stocks 
            WHERE user_id = ? AND symbol = ? AND group_id = ?
        ''', (user_id, symbol, group_id))
    else:
        cursor.execute('''
            SELECT COUNT(*) FROM watchlist_stocks 
            WHERE user_id = ? AND symbol = ?
        ''', (user_id, symbol))
    
    count = cursor.fetchone()[0]
    conn.close()
    
    return count > 0

# 初始化数据库
init_db()
