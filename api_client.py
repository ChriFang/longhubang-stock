import requests
import pandas as pd
from datetime import datetime, timedelta
import time
from typing import Optional, Dict, List
import config

class YouZiAPI:
    """游资龙虎榜API客户端"""
    
    def __init__(self):
        self.base_url = config.API_BASE_URL
        self.rate_limit = config.API_RATE_LIMIT
        self.last_request_time = 0
        self.request_count = 0
        
    def _rate_limit_check(self):
        """速率限制检查"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        # 确保每秒不超过限制
        if time_since_last < 1.0 / self.rate_limit:
            time.sleep(1.0 / self.rate_limit - time_since_last)
        
        self.last_request_time = time.time()
        self.request_count += 1
    
    def get_youzi_data(self, date: str) -> Optional[pd.DataFrame]:
        """
        获取指定日期的游资数据
        
        Args:
            date: 日期字符串，格式 YYYY-MM-DD
            
        Returns:
            pandas DataFrame 或 None
        """
        try:
            self._rate_limit_check()
            
            params = {'date': date}
            response = requests.get(self.base_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 20000 and data.get('msg') == 'success':
                    records = data.get('data', [])
                    if records:
                        df = pd.DataFrame(records)
                        # 数据类型转换
                        numeric_columns = ['mrje', 'mcje', 'jlrje']
                        for col in numeric_columns:
                            if col in df.columns:
                                df[col] = pd.to_numeric(df[col], errors='coerce')
                        
                        # 添加日期列
                        df['rq'] = pd.to_datetime(df['rq'])
                        return df
            else:
                print(f"API请求失败: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"网络请求错误: {e}")
        except Exception as e:
            print(f"数据处理错误: {e}")
            
        return None
    
    def get_date_range_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        获取日期范围内的所有数据
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            合并后的DataFrame
        """
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        all_data = []
        current_dt = start_dt
        
        while current_dt <= end_dt:
            date_str = current_dt.strftime('%Y-%m-%d')
            print(f"获取 {date_str} 的数据...")
            
            df = self.get_youzi_data(date_str)
            if df is not None and not df.empty:
                all_data.append(df)
            
            current_dt += timedelta(days=1)
            # 避免过于频繁的请求
            time.sleep(0.1)
        
        if all_data:
            return pd.concat(all_data, ignore_index=True)
        else:
            return pd.DataFrame()