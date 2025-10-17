import os
from datetime import datetime, timedelta

# API配置
API_BASE_URL = "https://www.stockapi.com.cn/v1/youzi/all"
API_RATE_LIMIT = 40  # 每秒请求次数
FREE_QUOTA_PER_DAY = 1000  # 每日免费请求次数

# 数据配置
CACHE_EXPIRY_HOURS = 24  # 缓存过期时间（小时）
MAX_CACHE_SIZE = 1000  # 最大缓存条目数

# 应用配置
DEFAULT_DATE_RANGE_DAYS = 30  # 默认查询天数
PAGE_SIZE = 20  # 每页显示条数

# 文件路径
DATA_DIR = "data"
CACHE_FILE = os.path.join(DATA_DIR, "youzi_cache.json")
DATABASE_FILE = os.path.join(DATA_DIR, "youzi.db")

# AI分析配置
AI_ANALYSIS_ENABLED = True  # 是否启用AI分析功能
AI_MODEL = "glm-4-flash"  # 使用的AI模型

# 创建数据目录
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)