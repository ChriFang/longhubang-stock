import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import os
from typing import List, Dict, Optional, Any
import config

class YouZiDatabase:
    """游资龙虎榜数据库管理类"""
    
    def __init__(self, db_path: str = "data/youzi.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表结构"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建主表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS youzi_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rq DATE NOT NULL,
                yzmc TEXT NOT NULL,
                yyb TEXT NOT NULL,
                sblx TEXT,
                gpdm TEXT NOT NULL,
                gpmc TEXT NOT NULL,
                mrje REAL NOT NULL,
                mcje REAL NOT NULL,
                jlrje REAL NOT NULL,
                gl TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(rq, yzmc, gpdm)
            )
        ''')
        
        # 创建游资分析表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS youzi_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                yzmc TEXT NOT NULL,
                analysis_date DATE NOT NULL,
                total_trades INTEGER,
                win_rate REAL,
                avg_profit REAL,
                total_profit REAL,
                favorite_stocks TEXT,
                risk_level TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(yzmc, analysis_date)
            )
        ''')
        
        # 创建股票分析表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gpdm TEXT NOT NULL,
                gpmc TEXT NOT NULL,
                analysis_date DATE NOT NULL,
                total_youzi_count INTEGER,
                total_buy_amount REAL,
                avg_buy_amount REAL,
                youzi_list TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(gpdm, analysis_date)
            )
        ''')
        
        # 创建AI分析历史记录主表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_analysis_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_date DATE NOT NULL,
                analysis_type TEXT NOT NULL,
                total_stocks INTEGER,
                top_n INTEGER,
                ai_model TEXT,
                ai_analysis TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建AI分析股票评分详情表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_stock_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_id INTEGER NOT NULL,
                rank_number INTEGER NOT NULL,
                stock_code TEXT NOT NULL,
                stock_name TEXT NOT NULL,
                concepts TEXT,
                total_score REAL NOT NULL,
                money_quality_score INTEGER,
                net_inflow_score INTEGER,
                sell_pressure_score INTEGER,
                institution_score INTEGER,
                bonus_score INTEGER,
                total_buy REAL,
                total_sell REAL,
                net_inflow REAL,
                buyer_count INTEGER,
                seller_count INTEGER,
                has_institution INTEGER,
                top_youzi_count INTEGER,
                buy_details TEXT,
                sell_details TEXT,
                FOREIGN KEY (analysis_id) REFERENCES ai_analysis_history(id)
            )
        ''')
        
        # 创建索引以提高查询性能
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_rq ON youzi_records(rq)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_yzmc ON youzi_records(yzmc)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_gpdm ON youzi_records(gpdm)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_rq_yzmc ON youzi_records(rq, yzmc)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ai_analysis_date ON ai_analysis_history(analysis_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ai_stock_analysis_id ON ai_stock_scores(analysis_id)')
        
        conn.commit()
        conn.close()
    
    def save_records(self, df: pd.DataFrame):
        """保存记录到数据库"""
        if df.empty:
            return
        
        conn = sqlite3.connect(self.db_path)
        
        # 准备数据 - 确保数据类型正确
        records = []
        for _, row in df.iterrows():
            # 处理日期类型，转换为字符串
            rq_value = row.get('rq')
            if hasattr(rq_value, 'strftime'):
                rq_value = rq_value.strftime('%Y-%m-%d')
            elif rq_value is None:
                rq_value = ''
            
            record = (
                rq_value, 
                str(row.get('yzmc', '')), 
                str(row.get('yyb', '')), 
                str(row.get('sblx', '')),
                str(row.get('gpdm', '')), 
                str(row.get('gpmc', '')), 
                float(row.get('mrje', 0)),
                float(row.get('mcje', 0)), 
                float(row.get('jlrje', 0)), 
                str(row.get('gl', ''))
            )
            records.append(record)
        
        # 批量插入（忽略重复记录）
        cursor = conn.cursor()
        cursor.executemany('''
            INSERT OR IGNORE INTO youzi_records 
            (rq, yzmc, yyb, sblx, gpdm, gpmc, mrje, mcje, jlrje, gl)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', records)
        
        conn.commit()
        conn.close()
        
        print(f"成功保存 {len(records)} 条记录到数据库")
    
    def get_records_by_date(self, start_date: str, end_date: str) -> pd.DataFrame:
        """根据日期范围获取记录"""
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT rq, yzmc, yyb, sblx, gpdm, gpmc, mrje, mcje, jlrje, gl
            FROM youzi_records 
            WHERE rq BETWEEN ? AND ?
            ORDER BY rq DESC, mrje DESC
        '''
        
        df = pd.read_sql_query(query, conn, params=[start_date, end_date])
        conn.close()
        
        # 转换数据类型
        if not df.empty:
            df['rq'] = pd.to_datetime(df['rq'])
            numeric_cols = ['mrje', 'mcje', 'jlrje']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    
    def get_youzi_performance(self, yzmc: str, days: int = 30) -> Dict[str, Any]:
        """获取游资表现数据"""
        conn = sqlite3.connect(self.db_path)
        
        # 获取游资的基本交易数据
        query = '''
            SELECT 
                COUNT(*) as total_trades,
                SUM(mrje) as total_buy_amount,
                AVG(mrje) as avg_buy_amount,
                SUM(jlrje) as net_inflow,
                COUNT(DISTINCT gpdm) as unique_stocks
            FROM youzi_records 
            WHERE yzmc = ? AND rq >= date('now', ?)
        '''
        
        cursor = conn.cursor()
        cursor.execute(query, (yzmc, f'-{days} days'))
        result = cursor.fetchone()
        
        # 获取最近交易的股票
        stock_query = '''
            SELECT gpdm, gpmc, COUNT(*) as trade_count, AVG(mrje) as avg_amount
            FROM youzi_records 
            WHERE yzmc = ? AND rq >= date('now', ?)
            GROUP BY gpdm, gpmc
            ORDER BY trade_count DESC
            LIMIT 10
        '''
        
        cursor.execute(stock_query, (yzmc, f'-{days} days'))
        stocks = cursor.fetchall()
        
        conn.close()
        
        if result:
            performance = {
                'total_trades': result[0],
                'total_buy_amount': result[1] or 0,
                'avg_buy_amount': result[2] or 0,
                'net_inflow': result[3] or 0,
                'unique_stocks': result[4] or 0,
                'recent_stocks': [
                    {'code': s[0], 'name': s[1], 'count': s[2], 'avg_amount': s[3] or 0}
                    for s in stocks
                ]
            }
            return performance
        else:
            return {}
    
    def get_stock_analysis(self, gpdm: str, days: int = 30) -> Dict[str, Any]:
        """获取股票分析数据"""
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT 
                gpmc,
                COUNT(DISTINCT yzmc) as youzi_count,
                SUM(mrje) as total_buy_amount,
                AVG(mrje) as avg_buy_amount,
                COUNT(*) as total_records
            FROM youzi_records 
            WHERE gpdm = ? AND rq >= date('now', ?)
            GROUP BY gpmc
        '''
        
        cursor = conn.cursor()
        cursor.execute(query, (gpdm, f'-{days} days'))
        result = cursor.fetchone()
        
        # 获取最近的游资操作
        youzi_query = '''
            SELECT yzmc, rq, mrje, jlrje
            FROM youzi_records 
            WHERE gpdm = ? AND rq >= date('now', ?)
            ORDER BY rq DESC
            LIMIT 20
        '''
        
        cursor.execute(youzi_query, (gpdm, f'-{days} days'))
        youzi_records = cursor.fetchall()
        
        conn.close()
        
        if result:
            analysis = {
                'stock_name': result[0],
                'youzi_count': result[1],
                'total_buy_amount': result[2] or 0,
                'avg_buy_amount': result[3] or 0,
                'total_records': result[4],
                'recent_operations': [
                    {'yzmc': y[0], 'date': y[1], 'buy_amount': y[2], 'net_inflow': y[3]}
                    for y in youzi_records
                ]
            }
            return analysis
        else:
            return {}
    
    def get_date_range(self) -> Dict[str, Any]:
        """获取数据库中的日期范围"""
        conn = sqlite3.connect(self.db_path)
        
        cursor = conn.cursor()
        cursor.execute('SELECT MIN(rq), MAX(rq) FROM youzi_records')
        result = cursor.fetchone()
        cursor.execute('SELECT COUNT(*) FROM youzi_records')
        count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'min_date': result[0],
            'max_date': result[1],
            'total_records': count
        }
    
    def backup_database(self, backup_path: Optional[str] = None):
        """备份数据库"""
        if backup_path is None:
            backup_path = f"data/youzi_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        
        import shutil
        shutil.copy2(self.db_path, backup_path)
        print(f"数据库已备份到: {backup_path}")
    
    def save_ai_analysis(self, analysis_result: Dict[str, Any]) -> int:
        """
        保存AI分析历史记录
        
        Args:
            analysis_result: AI分析结果字典
            
        Returns:
            analysis_id: 分析记录ID
        """
        if not analysis_result.get('success'):
            return -1
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 保存主记录
            cursor.execute('''
                INSERT INTO ai_analysis_history 
                (analysis_date, analysis_type, total_stocks, top_n, ai_model, ai_analysis)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                analysis_result['date'],
                'opportunity_stocks',
                analysis_result['total_stocks'],
                len(analysis_result['top_stocks']),
                analysis_result['model'],
                analysis_result['ai_analysis']
            ))
            
            analysis_id = cursor.lastrowid
            
            # 保存股票评分详情
            for i, stock in enumerate(analysis_result['top_stocks'], 1):
                # 准备买入方详情
                buy_details = []
                for _, row in stock['buy_data'].iterrows():
                    buy_details.append(f"{row['yzmc']}:{row['mrje']/10000:.2f}万")
                buy_details_str = '|'.join(buy_details)
                
                # 准备卖出方详情
                sell_details = []
                for _, row in stock['sell_data'].iterrows():
                    sell_details.append(f"{row['yzmc']}:{row['mcje']/10000:.2f}万")
                sell_details_str = '|'.join(sell_details) if sell_details else ''
                
                cursor.execute('''
                    INSERT INTO ai_stock_scores 
                    (analysis_id, rank_number, stock_code, stock_name, concepts,
                     total_score, money_quality_score, net_inflow_score, 
                     sell_pressure_score, institution_score, bonus_score,
                     total_buy, total_sell, net_inflow,
                     buyer_count, seller_count, has_institution, top_youzi_count,
                     buy_details, sell_details)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    analysis_id,
                    i,
                    stock['stock_code'],
                    stock['stock_name'],
                    stock['concepts'],
                    stock['total_score'],
                    stock['money_quality_score'],
                    stock['net_inflow_score'],
                    stock['sell_pressure_score'],
                    stock['institution_score'],
                    stock['bonus_score'],
                    stock['total_buy'],
                    stock['total_sell'],
                    stock['net_inflow'],
                    stock['buyer_count'],
                    stock['seller_count'],
                    1 if stock['has_institution'] else 0,
                    stock['top_youzi_count'],
                    buy_details_str,
                    sell_details_str
                ))
            
            conn.commit()
            print(f"成功保存AI分析记录，ID: {analysis_id}")
            return analysis_id
            
        except Exception as e:
            conn.rollback()
            print(f"保存AI分析记录失败: {e}")
            return -1
        finally:
            conn.close()
    
    def get_ai_analysis_history(self, days: int = 30) -> pd.DataFrame:
        """
        获取AI分析历史记录列表
        
        Args:
            days: 获取最近N天的记录
            
        Returns:
            DataFrame: 历史记录列表
        """
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT 
                id,
                analysis_date,
                analysis_type,
                total_stocks,
                top_n,
                ai_model,
                created_at
            FROM ai_analysis_history 
            WHERE analysis_date >= date('now', ?)
            ORDER BY created_at DESC
        '''
        
        df = pd.read_sql_query(query, conn, params=[f'-{days} days'])
        conn.close()
        
        return df
    
    def get_ai_analysis_detail(self, analysis_id: int) -> Dict[str, Any]:
        """
        获取AI分析详情
        
        Args:
            analysis_id: 分析记录ID
            
        Returns:
            Dict: 分析详情
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取主记录
        cursor.execute('''
            SELECT 
                analysis_date,
                analysis_type,
                total_stocks,
                top_n,
                ai_model,
                ai_analysis,
                created_at
            FROM ai_analysis_history 
            WHERE id = ?
        ''', (analysis_id,))
        
        main_record = cursor.fetchone()
        
        if not main_record:
            conn.close()
            return {}
        
        # 获取股票评分详情
        cursor.execute('''
            SELECT 
                rank_number,
                stock_code,
                stock_name,
                concepts,
                total_score,
                money_quality_score,
                net_inflow_score,
                sell_pressure_score,
                institution_score,
                bonus_score,
                total_buy,
                total_sell,
                net_inflow,
                buyer_count,
                seller_count,
                has_institution,
                top_youzi_count,
                buy_details,
                sell_details
            FROM ai_stock_scores 
            WHERE analysis_id = ?
            ORDER BY rank_number
        ''', (analysis_id,))
        
        stock_scores = cursor.fetchall()
        conn.close()
        
        # 组装返回数据
        result = {
            'analysis_id': analysis_id,
            'analysis_date': main_record[0],
            'analysis_type': main_record[1],
            'total_stocks': main_record[2],
            'top_n': main_record[3],
            'ai_model': main_record[4],
            'ai_analysis': main_record[5],
            'created_at': main_record[6],
            'stock_scores': []
        }
        
        for score in stock_scores:
            stock_info = {
                'rank': score[0],
                'stock_code': score[1],
                'stock_name': score[2],
                'concepts': score[3],
                'total_score': score[4],
                'money_quality_score': score[5],
                'net_inflow_score': score[6],
                'sell_pressure_score': score[7],
                'institution_score': score[8],
                'bonus_score': score[9],
                'total_buy': score[10],
                'total_sell': score[11],
                'net_inflow': score[12],
                'buyer_count': score[13],
                'seller_count': score[14],
                'has_institution': score[15] == 1,
                'top_youzi_count': score[16],
                'buy_details': score[17].split('|') if score[17] else [],
                'sell_details': score[18].split('|') if score[18] else []
            }
            result['stock_scores'].append(stock_info)
        
        return result
    
    def delete_ai_analysis(self, analysis_id: int) -> bool:
        """
        删除AI分析记录
        
        Args:
            analysis_id: 分析记录ID
            
        Returns:
            bool: 是否删除成功
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 删除股票评分详情
            cursor.execute('DELETE FROM ai_stock_scores WHERE analysis_id = ?', (analysis_id,))
            
            # 删除主记录
            cursor.execute('DELETE FROM ai_analysis_history WHERE id = ?', (analysis_id,))
            
            conn.commit()
            print(f"成功删除AI分析记录，ID: {analysis_id}")
            return True
            
        except Exception as e:
            conn.rollback()
            print(f"删除AI分析记录失败: {e}")
            return False
        finally:
            conn.close()