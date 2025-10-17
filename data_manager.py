import pandas as pd
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from cachetools import TTLCache
import config

class DataManager:
    """数据管理器，负责缓存和数据持久化"""
    
    def __init__(self):
        self.cache = TTLCache(
            maxsize=config.MAX_CACHE_SIZE, 
            ttl=config.CACHE_EXPIRY_HOURS * 3600
        )
        self.cache_file = config.CACHE_FILE
        
    def save_to_cache(self, key: str, data: pd.DataFrame):
        """保存数据到缓存"""
        try:
            # 内存缓存
            self.cache[key] = data.copy()
            
            # 文件缓存
            if not data.empty:
                # 创建数据副本并转换Timestamp为字符串
                data_to_cache = data.copy()
                if 'rq' in data_to_cache.columns:
                    data_to_cache['rq'] = data_to_cache['rq'].dt.strftime('%Y-%m-%d')
                
                cache_data = self._load_cache_file()
                cache_data[key] = {
                    'timestamp': datetime.now().isoformat(),
                    'data': data_to_cache.to_dict('records')
                }
                self._save_cache_file(cache_data)
                
        except Exception as e:
            print(f"缓存保存错误: {e}")
    
    def load_from_cache(self, key: str) -> Optional[pd.DataFrame]:
        """从缓存加载数据"""
        try:
            # 先检查内存缓存
            if key in self.cache:
                return self.cache[key].copy()
            
            # 检查文件缓存
            cache_data = self._load_cache_file()
            if key in cache_data:
                cached_item = cache_data[key]
                cached_time = datetime.fromisoformat(cached_item['timestamp'])
                
                # 检查是否过期
                if datetime.now() - cached_time < timedelta(hours=config.CACHE_EXPIRY_HOURS):
                    df = pd.DataFrame(cached_item['data'])
                    # 恢复数据类型
                    if 'rq' in df.columns:
                        df['rq'] = pd.to_datetime(df['rq'])
                    numeric_columns = ['mrje', 'mcje', 'jlrje']
                    for col in numeric_columns:
                        if col in df.columns:
                            df[col] = pd.to_numeric(df[col], errors='coerce')
                    
                    # 更新内存缓存
                    self.cache[key] = df.copy()
                    return df
                    
        except Exception as e:
            print(f"缓存加载错误: {e}")
            
        return None
    
    def _load_cache_file(self) -> Dict:
        """加载缓存文件"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return {}
    
    def _save_cache_file(self, data: Dict):
        """保存缓存文件"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"缓存文件保存错误: {e}")
    
    def clear_old_cache(self, days: int = 7):
        """清理过期缓存"""
        try:
            cache_data = self._load_cache_file()
            cutoff_time = datetime.now() - timedelta(days=days)
            
            keys_to_remove = []
            for key, item in cache_data.items():
                cached_time = datetime.fromisoformat(item['timestamp'])
                if cached_time < cutoff_time:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                if key in cache_data:
                    del cache_data[key]
                if key in self.cache:
                    del self.cache[key]
            
            self._save_cache_file(cache_data)
            print(f"清理了 {len(keys_to_remove)} 个过期缓存")
            
        except Exception as e:
            print(f"缓存清理错误: {e}")