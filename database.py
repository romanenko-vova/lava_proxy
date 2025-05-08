"""
Модуль для работы с базой данных.
Содержит функции для инициализации базы данных и работы с UTM-метками.
"""

import aiosqlite
from typing import Optional, Dict
from config import DB_PATH
from datetime import datetime


async def init_db():
    """Инициализирует базу данных и создает таблицу, если она не существует."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Создаем основную таблицу, если она не существует
        await db.execute('''
        CREATE TABLE IF NOT EXISTS utm_metrics (
            contract_id TEXT PRIMARY KEY,
            utm_source TEXT NOT NULL,
            utm_content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Проверяем, существует ли столбец updated_at
        cursor = await db.execute("PRAGMA table_info(utm_metrics)")
        columns = await cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        # Если updated_at отсутствует, добавляем его
        if "updated_at" not in column_names:
            print("Adding updated_at column to utm_metrics table")
            try:
                await db.execute('''
                ALTER TABLE utm_metrics 
                ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ''')
                
                # Обновляем значения updated_at для существующих записей
                await db.execute('''
                UPDATE utm_metrics 
                SET updated_at = created_at 
                WHERE updated_at IS NULL
                ''')
                
            except Exception as e:
                print(f"Error updating table schema: {e}")
        
        await db.commit()
    print("Database initialized")


async def store_utm_metrics(contract_id: str, utm_data: dict):
    """Сохраняет UTM-метки для контракта в базу данных."""
    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute('''
            INSERT OR REPLACE INTO utm_metrics (contract_id, utm_source, utm_content, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ''', (
                contract_id,
                utm_data.get("utm_source", ""),
                utm_data.get("utm_content", ""),
                current_time,
                current_time
            ))
            await db.commit()
            print(f"Stored UTM metrics for contract {contract_id}: {utm_data}")
    except Exception as e:
        print(f"Error storing UTM metrics: {e}")
        raise


async def update_utm_metrics_timestamp(contract_id: str):
    """Обновляет timestamp для существующей записи при повторном платеже."""
    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute('''
            UPDATE utm_metrics 
            SET updated_at = ? 
            WHERE contract_id = ?
            ''', (current_time, contract_id))
            await db.commit()
            print(f"Updated timestamp for contract {contract_id}")
            
            # Проверяем, была ли обновлена запись
            cursor = await db.execute('''
            SELECT contract_id FROM utm_metrics WHERE contract_id = ?
            ''', (contract_id,))
            row = await cursor.fetchone()
            return row is not None
            
    except Exception as e:
        print(f"Error updating UTM metrics timestamp: {e}")
        return False


async def get_utm_metrics(contract_id: str) -> Optional[dict]:
    """Получает UTM-метки по contractId из базы данных."""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute('''
            SELECT utm_source, utm_content, created_at, updated_at
            FROM utm_metrics
            WHERE contract_id = ?
            ''', (contract_id,)) as cursor:
                row = await cursor.fetchone()
                
                if row:
                    return {
                        "utm_source": row[0],
                        "utm_content": row[1],
                        "created_at": row[2],
                        "updated_at": row[3]
                    }
                return None
    except Exception as e:
        print(f"Error getting UTM metrics: {e}")
        return None 