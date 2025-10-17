import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from database import YouZiDatabase

class YouZiAnalyzer:
    """游资数据分析器"""
    
    def __init__(self, db: YouZiDatabase):
        self.db = db
    
    def calculate_win_rate(self, yzmc: str, days: int = 90) -> Dict[str, any]:
        """
        计算游资胜率
        Args:
            yzmc: 游资名称
            days: 分析天数
        Returns:
            胜率分析结果
        """
        # 获取游资的历史数据
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        # 这里需要股票价格数据来计算实际盈亏
        # 暂时使用净流入作为盈利指标
        df = self.db.get_records_by_date(start_date, end_date)
        youzi_data = df[df['yzmc'] == yzmc].copy()
        
        if youzi_data.empty:
            return {
                'win_rate': 0,
                'total_trades': 0,
                'profitable_trades': 0,
                'avg_profit': 0,
                'total_profit': 0
            }
        
        # 简单策略：净流入为正视为盈利
        youzi_data['is_profitable'] = youzi_data['jlrje'] > 0
        profitable_trades = youzi_data['is_profitable'].sum()
        total_trades = len(youzi_data)
        win_rate = profitable_trades / total_trades if total_trades > 0 else 0
        
        return {
            'win_rate': round(win_rate * 100, 2),
            'total_trades': total_trades,
            'profitable_trades': profitable_trades,
            'avg_profit': youzi_data['jlrje'].mean(),
            'total_profit': youzi_data['jlrje'].sum()
        }
    
    def analyze_trading_patterns(self, yzmc: str) -> Dict[str, any]:
        """
        分析游资交易模式
        Args:
            yzmc: 游资名称
        Returns:
            交易模式分析
        """
        df = self.db.get_records_by_date('2020-01-01', datetime.now().strftime('%Y-%m-%d'))
        youzi_data = df[df['yzmc'] == yzmc].copy()
        
        if youzi_data.empty:
            return {}
        
        # 分析交易频率
        trading_days = youzi_data['rq'].nunique()
        total_trades = len(youzi_data)
        avg_trades_per_day = total_trades / trading_days if trading_days > 0 else 0
        
        # 分析股票偏好
        stock_preferences = youzi_data['gpmc'].value_counts().head(10).to_dict()
        
        # 分析金额分布
        amount_stats = {
            'min_amount': youzi_data['mrje'].min(),
            'max_amount': youzi_data['mrje'].max(),
            'avg_amount': youzi_data['mrje'].mean(),
            'median_amount': youzi_data['mrje'].median()
        }
        
        # 分析概念偏好
        concept_preferences = {}
        for concepts in youzi_data['gl'].dropna():
            for concept in concepts.split(','):
                concept_preferences[concept.strip()] = concept_preferences.get(concept.strip(), 0) + 1
        
        # 取前10个最偏好的概念
        top_concepts = dict(sorted(concept_preferences.items(), key=lambda x: x[1], reverse=True)[:10])
        
        return {
            'trading_days': trading_days,
            'total_trades': total_trades,
            'avg_trades_per_day': round(avg_trades_per_day, 2),
            'stock_preferences': stock_preferences,
            'amount_stats': amount_stats,
            'concept_preferences': top_concepts
        }
    
    def get_youzi_ranking(self, metric: str = 'total_amount', days: int = 30) -> pd.DataFrame:
        """
        获取游资排名
        Args:
            metric: 排名指标 (total_amount, win_rate, frequency)
            days: 分析天数
        Returns:
            游资排名DataFrame
        """
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        df = self.db.get_records_by_date(start_date, end_date)
        
        if df.empty:
            return pd.DataFrame()
        
        # 按游资分组统计
        youzi_stats = df.groupby('yzmc').agg({
            'mrje': ['sum', 'count', 'mean'],
            'jlrje': ['sum', 'mean']
        }).round(0)
        
        # 扁平化列名
        youzi_stats.columns = ['总买入金额', '交易次数', '平均买入金额', '净流入总额', '平均净流入']
        youzi_stats = youzi_stats.reset_index()
        
        # 计算胜率（简化版）
        def calculate_simple_win_rate(group):
            profitable = (group['jlrje'] > 0).sum()
            return profitable / len(group) if len(group) > 0 else 0
        
        win_rates = df.groupby('yzmc').apply(calculate_simple_win_rate)
        youzi_stats['胜率'] = (win_rates * 100).round(2)
        
        # 按指定指标排序
        if metric == 'total_amount':
            youzi_stats = youzi_stats.sort_values('总买入金额', ascending=False)
        elif metric == 'win_rate':
            youzi_stats = youzi_stats.sort_values('胜率', ascending=False)
        elif metric == 'frequency':
            youzi_stats = youzi_stats.sort_values('交易次数', ascending=False)
        
        return youzi_stats
    
    def predict_trend(self, gpdm: str, days: int = 7) -> Dict[str, any]:
        """
        预测股票趋势（简化版）
        Args:
            gpdm: 股票代码
            days: 预测天数
        Returns:
            趋势预测结果
        """
        # 获取股票的历史游资数据
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        df = self.db.get_records_by_date(start_date, end_date)
        stock_data = df[df['gpdm'] == gpdm].copy()
        
        if stock_data.empty:
            return {'trend': 'unknown', 'confidence': 0, 'message': '数据不足'}
        
        # 简单趋势分析：基于最近游资活动
        recent_data = stock_data.sort_values('rq', ascending=False).head(10)
        
        # 计算指标
        total_buy_amount = recent_data['mrje'].sum()
        net_inflow = recent_data['jlrje'].sum()
        youzi_count = recent_data['yzmc'].nunique()
        
        # 简单趋势判断
        if net_inflow > 0 and youzi_count >= 3:
            trend = 'bullish'
            confidence = min(80 + (net_inflow / total_buy_amount * 100), 95)
        elif net_inflow < 0:
            trend = 'bearish'
            confidence = min(70 + (abs(net_inflow) / total_buy_amount * 100), 90)
        else:
            trend = 'neutral'
            confidence = 50
        
        return {
            'trend': trend,
            'confidence': round(confidence, 2),
            'total_buy_amount': total_buy_amount,
            'net_inflow': net_inflow,
            'youzi_count': youzi_count,
            'recent_days': len(recent_data)
        }
    
    def generate_ai_insights(self, yzmc: str) -> Dict[str, any]:
        """
        生成AI综合分析见解
        Args:
            yzmc: 游资名称
        Returns:
            AI分析结果
        """
        patterns = self.analyze_trading_patterns(yzmc)
        win_rate = self.calculate_win_rate(yzmc)
        
        if not patterns:
            return {'error': '数据不足'}
        
        # 生成分析见解
        insights = []
        
        # 交易频率分析
        if patterns['avg_trades_per_day'] > 2:
            insights.append("高频交易者，操作活跃")
        elif patterns['avg_trades_per_day'] < 0.5:
            insights.append("低频交易者，精选个股")
        else:
            insights.append("中等频率交易者")
        
        # 金额偏好分析
        avg_amount = patterns['amount_stats']['avg_amount']
        if avg_amount > 10000000:  # 1000万以上
            insights.append("大资金操作，偏好高市值股票")
        elif avg_amount < 1000000:  # 100万以下
            insights.append("小资金操作，灵活性强")
        else:
            insights.append("中等资金规模")
        
        # 胜率分析
        if win_rate['win_rate'] > 60:
            insights.append("高胜率选手，选股能力强")
        elif win_rate['win_rate'] < 40:
            insights.append("胜率偏低，风险较高")
        else:
            insights.append("胜率中等，稳定性一般")
        
        # 股票偏好分析
        top_stocks = list(patterns['stock_preferences'].keys())[:3]
        if top_stocks:
            insights.append(f"偏好股票: {', '.join(top_stocks)}")
        
        # 概念偏好分析
        top_concepts = list(patterns['concept_preferences'].keys())[:3]
        if top_concepts:
            insights.append(f"关注概念: {', '.join(top_concepts)}")
        
        return {
            'insights': insights,
            'summary': f"{yzmc}是一位{insights[0].lower()}，{insights[1].lower()}。{insights[2]}",
            'risk_level': self.assess_risk_level(patterns, win_rate),
            'recommendation': self.generate_recommendation(patterns, win_rate)
        }
    
    def assess_risk_level(self, patterns: Dict, win_rate: Dict) -> str:
        """评估风险水平"""
        if win_rate['total_trades'] == 0:
            return '未知'
        
        risk_score = 0
        
        # 交易频率风险
        if patterns['avg_trades_per_day'] > 3:
            risk_score += 2
        elif patterns['avg_trades_per_day'] < 0.3:
            risk_score += 1
        
        # 胜率风险
        if win_rate['win_rate'] < 40:
            risk_score += 2
        elif win_rate['win_rate'] < 50:
            risk_score += 1
        
        # 金额分散风险
        if patterns['total_trades'] < 10:
            risk_score += 1
        
        if risk_score >= 3:
            return '高风险'
        elif risk_score >= 2:
            return '中风险'
        else:
            return '低风险'
    
    def generate_recommendation(self, patterns: Dict, win_rate: Dict) -> str:
        """生成投资建议"""
        if win_rate['total_trades'] == 0:
            return '数据不足，无法给出建议'
        
        if win_rate['win_rate'] > 60:
            return '建议关注，高胜率选手'
        elif win_rate['win_rate'] > 45:
            return '可适度关注，表现稳定'
        else:
            return '谨慎关注，风险较高'