"""
AI分析模块 - 使用 DeepSeek 大模型进行龙虎榜深度分析
"""

import os
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from openai import OpenAI
from dotenv import load_dotenv
import json
import config

# 加载环境变量
load_dotenv()


class AILongHuAnalyzer:
    """龙虎榜AI分析器 - 基于DeepSeek"""
    
    def __init__(self):
        """初始化AI分析器"""
        self.api_key = os.getenv('DEEPSEEK_API_KEY')
        if not self.api_key or self.api_key == 'your_api_key_here':
            raise ValueError("请在.env文件中配置有效的DEEPSEEK_API_KEY")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
        )
        self.model = config.AI_MODEL
        
        # 系统角色设定
        self.system_prompt = """你是一位资深的龙虎榜打板专家，拥有超过15年的A股实战经验。
你擅长从龙虎榜数据中发掘投资机会，对游资席位、资金流向、题材炒作有深刻理解。

你的分析框架：
1. 买入资金的"含金量"分析：
   - 识别顶级游资席位（如章盟主、赵老哥等）vs 普通游资
   - 判断是单一主力主攻还是多家游资合力
   - 评估游资的历史战绩和操盘风格

2. 净买入额的绝对值分析：
   - 评估资金规模（大额资金 vs 小打小闹）
   - 判断资金的真实性和持续性
   - 分析资金流入的力度和决心

3. 卖出方的压力分析：
   - 识别是主力获利了结还是散户/小资金离场
   - 评估卖出压力的性质和强度
   - 判断筹码结构的变化

4. 机构共振分析：
   - 检查是否有机构席位同时买入
   - 评估机构+游资共振的意义
   - 判断题材的想象空间和持续性

请用专业、精准、实战的语言给出分析，并提供明确的操作建议。"""

    def _chat(self, prompt: str, max_tokens: int) -> str:
        """调用DeepSeek聊天补全接口"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            top_p=0.8,
            max_tokens=max_tokens,
            stream=False
        )
        return response.choices[0].message.content or ""

    def analyze_stock_opportunity(self, stock_data: pd.DataFrame, stock_name: str) -> Dict[str, any]:
        """
        分析单只股票的龙虎榜数据，给出AI投资策略
        
        Args:
            stock_data: 该股票的龙虎榜数据
            stock_name: 股票名称
            
        Returns:
            AI分析结果
        """
        try:
            # 准备分析数据
            analysis_context = self._prepare_stock_context(stock_data, stock_name)
            
            # 调用AI进行分析
            prompt = f"""请深度分析以下龙虎榜数据，推演次日投资机会，给出投资策略：

【股票名称】{stock_name}
【上榜日期】{analysis_context['date']}
【股票代码】{analysis_context['code']}
【相关概念】{analysis_context['concepts']}

【买入方数据】
{analysis_context['buy_side']}

【卖出方数据】
{analysis_context['sell_side']}

【资金统计】
- 总买入金额：{analysis_context['total_buy']:.2f}万元
- 总卖出金额：{analysis_context['total_sell']:.2f}万元
- 净流入金额：{analysis_context['net_inflow']:.2f}万元
- 买入游资数量：{analysis_context['buyer_count']}家
- 卖出游资数量：{analysis_context['seller_count']}家

请从以下维度进行深度分析：
1. 买入资金含金量评估（游资等级、单一主攻vs多家合力）
2. 净买入额的绝对值评估（真金白银vs小打小闹）
3. 卖出方压力分析（主力了结vs散户离场）
4. 机构共振分析（是否有机构参与）
5. 次日投资机会推演
6. 具体操作策略（买入时机、止盈止损位）

请给出专业、实战的分析意见。"""

            ai_analysis = self._chat(prompt, max_tokens=2000)
            
            return {
                'success': True,
                'stock_name': stock_name,
                'analysis': ai_analysis,
                'context': analysis_context,
                'model': self.model,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'stock_name': stock_name
            }
    
    def analyze_market_hotspots(self, df: pd.DataFrame, date: str) -> Dict[str, any]:
        """
        分析当日市场热点和整体资金流向
        
        Args:
            df: 当日所有龙虎榜数据
            date: 日期
            
        Returns:
            市场热点分析结果
        """
        try:
            # 准备市场数据
            market_context = self._prepare_market_context(df, date)
            
            prompt = f"""请分析{date}的龙虎榜数据，找出市场热点和投资机会：

【市场概况】
- 上榜股票数量：{market_context['stock_count']}只
- 总成交金额：{market_context['total_amount']:.2f}亿元
- 活跃游资数量：{market_context['active_youzi']}家
- 净流入前5股票：
{market_context['top_inflow_stocks']}

【热门概念板块】
{market_context['hot_concepts']}

【最活跃游资】
{market_context['active_youzi_list']}

【机构参与情况】
{market_context['institution_status']}

请从以下角度分析：
1. 当日市场主线和热点板块
2. 资金流向特征和偏好
3. 顶级游资的动向和目标
4. 机构资金的介入情况
5. 次日重点关注的方向
6. 整体操作策略建议

给出专业、全面的市场分析。"""

            market_analysis = self._chat(prompt, max_tokens=2500)
            
            return {
                'success': True,
                'date': date,
                'analysis': market_analysis,
                'context': market_context,
                'model': self.model,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'date': date
            }
    
    def analyze_youzi_style(self, youzi_data: pd.DataFrame, youzi_name: str) -> Dict[str, any]:
        """
        分析游资的操盘风格和特点
        
        Args:
            youzi_data: 游资的历史操作数据
            youzi_name: 游资名称
            
        Returns:
            游资风格分析结果
        """
        try:
            # 准备游资数据
            youzi_context = self._prepare_youzi_context(youzi_data, youzi_name)
            
            prompt = f"""请深度分析游资"{youzi_name}"的操盘风格和投资特点：

【基本数据】
- 分析周期：最近{youzi_context['days']}天
- 操作次数：{youzi_context['trade_count']}次
- 总买入金额：{youzi_context['total_buy']:.2f}万元
- 平均买入金额：{youzi_context['avg_buy']:.2f}万元
- 净流入金额：{youzi_context['net_inflow']:.2f}万元
- 胜率：{youzi_context['win_rate']:.1f}%

【高频操作股票】
{youzi_context['favorite_stocks']}

【偏好概念板块】
{youzi_context['favorite_concepts']}

【近期操作记录】
{youzi_context['recent_operations']}

请分析：
1. 该游资的等级评定（顶级/一线/二线游资）
2. 操盘风格特点（激进/稳健、短线/中线）
3. 选股偏好和规律
4. 资金运作特点
5. 跟随该游资的注意事项
6. 当前重点关注的方向

给出专业的游资画像分析。"""

            youzi_analysis = self._chat(prompt, max_tokens=2000)
            
            return {
                'success': True,
                'youzi_name': youzi_name,
                'analysis': youzi_analysis,
                'context': youzi_context,
                'model': self.model,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'youzi_name': youzi_name
            }
    
    def _prepare_stock_context(self, stock_data: pd.DataFrame, stock_name: str) -> Dict:
        """准备股票分析上下文"""
        # 按买入卖出分组
        buy_data = stock_data[stock_data['mrje'] > 0].copy()
        sell_data = stock_data[stock_data['mcje'] > 0].copy()
        
        # 买入方信息
        buy_info = []
        for _, row in buy_data.iterrows():
            buy_info.append(
                f"  {row['yzmc']}（{row['yyb']}）: 买入{row['mrje']/10000:.2f}万元"
            )
        
        # 卖出方信息
        sell_info = []
        for _, row in sell_data.iterrows():
            sell_info.append(
                f"  {row['yzmc']}（{row['yyb']}）: 卖出{row['mcje']/10000:.2f}万元"
            )
        
        # 获取概念
        concepts = stock_data['gl'].dropna().values
        concept_str = concepts[0] if len(concepts) > 0 else "无"
        
        # 获取股票代码
        code = stock_data['gpdm'].values[0] if len(stock_data) > 0 else ""
        
        # 获取日期
        date = stock_data['rq'].dt.strftime('%Y-%m-%d').values[0] if len(stock_data) > 0 else ""
        
        return {
            'stock_name': stock_name,
            'code': code,
            'date': date,
            'concepts': concept_str,
            'buy_side': '\n'.join(buy_info) if buy_info else "无买入数据",
            'sell_side': '\n'.join(sell_info) if sell_info else "无卖出数据",
            'total_buy': stock_data['mrje'].sum() / 10000,
            'total_sell': stock_data['mcje'].sum() / 10000,
            'net_inflow': stock_data['jlrje'].sum() / 10000,
            'buyer_count': len(buy_data),
            'seller_count': len(sell_data)
        }
    
    def _prepare_market_context(self, df: pd.DataFrame, date: str) -> Dict:
        """准备市场分析上下文"""
        # 按股票统计
        stock_stats = df.groupby(['gpmc', 'gpdm']).agg({
            'mrje': 'sum',
            'mcje': 'sum',
            'jlrje': 'sum'
        }).reset_index()
        
        # 净流入前5
        top_inflow = stock_stats.nlargest(5, 'jlrje')
        top_inflow_str = '\n'.join([
            f"  {row['gpmc']}（{row['gpdm']}）: 净流入{row['jlrje']/10000:.2f}万元"
            for _, row in top_inflow.iterrows()
        ])
        
        # 概念统计
        concept_counts = {}
        for concepts in df['gl'].dropna():
            for concept in str(concepts).split(','):
                concept = concept.strip()
                if concept:
                    concept_counts[concept] = concept_counts.get(concept, 0) + 1
        
        hot_concepts = sorted(concept_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        hot_concepts_str = '\n'.join([
            f"  {concept}: {count}次"
            for concept, count in hot_concepts
        ])
        
        # 活跃游资
        youzi_stats = df.groupby('yzmc').agg({
            'mrje': 'sum',
            'yzmc': 'count'
        }).rename(columns={'yzmc': 'count'}).reset_index()
        youzi_stats = youzi_stats.sort_values('mrje', ascending=False).head(10)
        
        active_youzi_str = '\n'.join([
            f"  {row['yzmc']}: 买入{row['mrje']/10000:.2f}万元（{row['count']}次）"
            for _, row in youzi_stats.iterrows()
        ])
        
        # 检查机构参与
        institution_keywords = ['机构专用', '机构', '基金']
        institution_data = df[df['yzmc'].str.contains('|'.join(institution_keywords), na=False)]
        institution_count = len(institution_data)
        institution_amount = institution_data['mrje'].sum() / 10000
        
        institution_status = f"机构参与{institution_count}次，买入{institution_amount:.2f}万元"
        
        return {
            'stock_count': df['gpmc'].nunique(),
            'total_amount': df['mrje'].sum() / 100000000,
            'active_youzi': df['yzmc'].nunique(),
            'top_inflow_stocks': top_inflow_str,
            'hot_concepts': hot_concepts_str if hot_concepts_str else "暂无概念数据",
            'active_youzi_list': active_youzi_str,
            'institution_status': institution_status
        }
    
    def analyze_opportunity_stocks(self, df: pd.DataFrame, date: str, top_n: int = 10) -> Dict[str, any]:
        """
        从所有龙虎榜股票中筛选次日大概率上涨的机会股票
        
        Args:
            df: 当日所有龙虎榜数据
            date: 日期
            top_n: 返回前N只股票
            
        Returns:
            机会股票分析结果
        """
        try:
            # 按股票分组统计
            stock_analysis = []
            
            for stock_name in df['gpmc'].unique():
                stock_data = df[df['gpmc'] == stock_name].copy()
                
                # 基础数据
                stock_code = stock_data['gpdm'].values[0]
                concepts = stock_data['gl'].dropna().values[0] if len(stock_data['gl'].dropna()) > 0 else "无"
                
                # 1. 买入资金含金量评估
                buy_data = stock_data[stock_data['mrje'] > 0].copy()
                top_youzi_keywords = ['章', '赵', '徐', '吴', '方新侠', '成都', '杭州', '温州', '佛山']
                top_youzi_count = sum(buy_data['yzmc'].str.contains('|'.join(top_youzi_keywords), na=False))
                buyer_count = len(buy_data)
                
                # 资金含金量评分 (0-30分)
                money_quality_score = 0
                if top_youzi_count >= 2:
                    money_quality_score = 30
                elif top_youzi_count == 1:
                    money_quality_score = 20
                elif buyer_count >= 3:
                    money_quality_score = 15
                elif buyer_count >= 2:
                    money_quality_score = 10
                else:
                    money_quality_score = 5
                
                # 2. 净买入额评估
                total_buy = stock_data['mrje'].sum()
                total_sell = stock_data['mcje'].sum()
                net_inflow = stock_data['jlrje'].sum()
                
                # 净买入额评分 (0-25分)
                net_inflow_score = 0
                if net_inflow > 10000000:  # 超过1000万
                    net_inflow_score = 25
                elif net_inflow > 5000000:  # 超过500万
                    net_inflow_score = 20
                elif net_inflow > 2000000:  # 超过200万
                    net_inflow_score = 15
                elif net_inflow > 0:
                    net_inflow_score = 10
                else:
                    net_inflow_score = 0
                
                # 3. 卖出方压力评估
                sell_data = stock_data[stock_data['mcje'] > 0].copy()
                seller_count = len(sell_data)
                
                # 检查是否有大额卖出
                if len(sell_data) > 0:
                    max_sell = sell_data['mcje'].max()
                    avg_buy = buy_data['mrje'].mean() if len(buy_data) > 0 else 0
                    
                    # 卖出压力评分 (0-20分，压力越小分数越高)
                    sell_pressure_score = 20
                    if max_sell > avg_buy * 1.5:  # 有大额卖出
                        sell_pressure_score = 5
                    elif seller_count >= 3:  # 多方卖出
                        sell_pressure_score = 10
                    elif seller_count == 2:
                        sell_pressure_score = 15
                else:
                    sell_pressure_score = 20  # 无卖出最佳
                
                # 4. 机构共振检查
                institution_keywords = ['机构专用', '机构', '基金']
                institution_buy = buy_data[buy_data['yzmc'].str.contains('|'.join(institution_keywords), na=False)]
                has_institution = len(institution_buy) > 0
                
                # 机构共振评分 (0-15分)
                institution_score = 0
                if has_institution and buyer_count >= 2:  # 机构+游资共振
                    institution_score = 15
                elif has_institution:  # 仅机构
                    institution_score = 10
                elif buyer_count >= 3:  # 多游资共振
                    institution_score = 8
                
                # 5. 其他加分项
                bonus_score = 0
                
                # 买卖比例
                if total_sell > 0:
                    buy_sell_ratio = total_buy / total_sell
                    if buy_sell_ratio > 3:  # 买入远大于卖出
                        bonus_score += 5
                    elif buy_sell_ratio > 2:
                        bonus_score += 3
                
                # 单一主力主攻
                if len(buy_data) > 0:
                    max_buy = buy_data['mrje'].max()
                    if max_buy > total_buy * 0.6:  # 单一主力占比超60%
                        bonus_score += 3
                
                # 热门概念
                hot_concepts = ['人工智能', 'AI', '芯片', '半导体', '新能源', '锂电池', 
                               '光伏', '军工', '数字经济', '元宇宙', '游戏']
                if any(keyword in str(concepts) for keyword in hot_concepts):
                    bonus_score += 2
                
                # 总分计算 (满分100分)
                total_score = money_quality_score + net_inflow_score + sell_pressure_score + institution_score + bonus_score
                
                stock_analysis.append({
                    'stock_name': stock_name,
                    'stock_code': stock_code,
                    'concepts': concepts,
                    'total_score': min(total_score, 100),  # 最高100分
                    'money_quality_score': money_quality_score,
                    'net_inflow_score': net_inflow_score,
                    'sell_pressure_score': sell_pressure_score,
                    'institution_score': institution_score,
                    'bonus_score': bonus_score,
                    'total_buy': total_buy,
                    'total_sell': total_sell,
                    'net_inflow': net_inflow,
                    'buyer_count': buyer_count,
                    'seller_count': seller_count,
                    'has_institution': has_institution,
                    'top_youzi_count': top_youzi_count,
                    'buy_data': buy_data,
                    'sell_data': sell_data
                })
            
            # 按总分排序
            stock_analysis.sort(key=lambda x: x['total_score'], reverse=True)
            top_stocks = stock_analysis[:top_n]
            
            # 准备AI分析的上下文
            analysis_context = self._prepare_opportunity_context(top_stocks, date)
            
            # 调用AI进行深度分析
            prompt = f"""请作为资深龙虎榜打板专家，深度分析{date}的龙虎榜数据，找出次日大概率上涨的机会股票。

【市场概况】
- 上榜股票总数：{len(stock_analysis)}只
- 分析日期：{date}

【AI智能评分Top {top_n}】
{analysis_context['top_stocks_detail']}

【评分维度说明】
1. 买入资金含金量 (0-30分)：顶级游资加分多，普通游资加分少
2. 净买入额评分 (0-25分)：真金白银越多分数越高
3. 卖出压力评分 (0-20分)：压力越小分数越高
4. 机构共振评分 (0-15分)：机构+游资共振最高分
5. 其他加分项 (0-10分)：买卖比例、主力集中度、热门概念等

请从以下角度进行专业分析：

1. **综合推荐股票**（从Top {top_n}中挑选2-3只最有潜力的）
   - 说明推荐理由
   - 评估次日上涨概率
   - 给出参考买点

2. **资金含金量分析**
   - 哪些股票有顶级游资参与？
   - 是单一主攻还是多家合力？
   - 游资组合的质量如何？

3. **资金共振分析**（重点关注）
   - 哪些股票存在机构+游资共振？
   - 哪些股票存在多游资联手？
   - 共振的强度和意义如何？

4. **卖出压力评估**
   - 哪些股票卖方压力小？
   - 是否有主力获利了结的迹象？
   - 筹码结构是否健康？

5. **风险提示**
   - 哪些股票需要谨慎对待？
   - 可能存在的风险点
   - 止损位建议

6. **操作策略**
   - 具体的买入时机建议
   - 仓位控制建议
   - 止盈止损位设置

请给出专业、实战、有针对性的分析意见。"""

            ai_analysis = self._chat(prompt, max_tokens=3000)
            
            return {
                'success': True,
                'date': date,
                'total_stocks': len(stock_analysis),
                'top_stocks': top_stocks,
                'all_stocks': stock_analysis,
                'ai_analysis': ai_analysis,
                'context': analysis_context,
                'model': self.model,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'date': date
            }
    
    def _prepare_opportunity_context(self, top_stocks: List[Dict], date: str) -> Dict:
        """准备机会股票分析上下文"""
        stocks_detail = []
        
        for i, stock in enumerate(top_stocks, 1):
            # 买入方信息
            buy_info = []
            for _, row in stock['buy_data'].iterrows():
                buy_info.append(f"    {row['yzmc']}: {row['mrje']/10000:.2f}万")
            
            # 卖出方信息
            sell_info = []
            for _, row in stock['sell_data'].iterrows():
                sell_info.append(f"    {row['yzmc']}: {row['mcje']/10000:.2f}万")
            
            stock_detail = f"""
【第{i}名】{stock['stock_name']}（{stock['stock_code']}）
- 综合评分：{stock['total_score']:.1f}分
- 相关概念：{stock['concepts']}
- 评分明细：
  * 资金含金量：{stock['money_quality_score']}分（顶级游资{stock['top_youzi_count']}家，买方{stock['buyer_count']}家）
  * 净买入额：{stock['net_inflow_score']}分（净流入{stock['net_inflow']/10000:.2f}万）
  * 卖出压力：{stock['sell_pressure_score']}分（卖方{stock['seller_count']}家）
  * 机构共振：{stock['institution_score']}分（{'有机构' if stock['has_institution'] else '无机构'}）
  * 加分项：{stock['bonus_score']}分
- 资金情况：
  * 总买入：{stock['total_buy']/10000:.2f}万
  * 总卖出：{stock['total_sell']/10000:.2f}万
  * 净流入：{stock['net_inflow']/10000:.2f}万
- 买入方：
{chr(10).join(buy_info) if buy_info else '    无'}
- 卖出方：
{chr(10).join(sell_info) if sell_info else '    无'}
"""
            stocks_detail.append(stock_detail)
        
        return {
            'top_stocks_detail': '\n'.join(stocks_detail),
            'date': date
        }
    
    def _prepare_youzi_context(self, youzi_data: pd.DataFrame, youzi_name: str) -> Dict:
        """准备游资分析上下文"""
        # 时间跨度
        days = (youzi_data['rq'].max() - youzi_data['rq'].min()).days + 1
        
        # 基本统计
        total_buy = youzi_data['mrje'].sum() / 10000
        avg_buy = youzi_data['mrje'].mean() / 10000
        net_inflow = youzi_data['jlrje'].sum() / 10000
        
        # 胜率计算
        profitable = (youzi_data['jlrje'] > 0).sum()
        win_rate = (profitable / len(youzi_data) * 100) if len(youzi_data) > 0 else 0
        
        # 高频股票
        stock_counts = youzi_data['gpmc'].value_counts().head(10)
        favorite_stocks_str = '\n'.join([
            f"  {stock}: {count}次"
            for stock, count in stock_counts.items()
        ])
        
        # 偏好概念
        concept_counts = {}
        for concepts in youzi_data['gl'].dropna():
            for concept in str(concepts).split(','):
                concept = concept.strip()
                if concept:
                    concept_counts[concept] = concept_counts.get(concept, 0) + 1
        
        favorite_concepts = sorted(concept_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        favorite_concepts_str = '\n'.join([
            f"  {concept}: {count}次"
            for concept, count in favorite_concepts
        ])
        
        # 近期操作
        recent = youzi_data.sort_values('rq', ascending=False).head(10)
        recent_ops_str = '\n'.join([
            f"  {row['rq'].strftime('%Y-%m-%d')} {row['gpmc']}: "
            f"买入{row['mrje']/10000:.2f}万元，净流入{row['jlrje']/10000:.2f}万元"
            for _, row in recent.iterrows()
        ])
        
        return {
            'youzi_name': youzi_name,
            'days': days,
            'trade_count': len(youzi_data),
            'total_buy': total_buy,
            'avg_buy': avg_buy,
            'net_inflow': net_inflow,
            'win_rate': win_rate,
            'favorite_stocks': favorite_stocks_str if favorite_stocks_str else "暂无数据",
            'favorite_concepts': favorite_concepts_str if favorite_concepts_str else "暂无数据",
            'recent_operations': recent_ops_str if recent_ops_str else "暂无数据"
        }


def test_ai_analyzer():
    """测试AI分析器"""
    try:
        analyzer = AILongHuAnalyzer()
        print("✓ AI分析器初始化成功")
        print(f"✓ API Key已配置: {analyzer.api_key[:10]}...")
        return True
    except Exception as e:
        print(f"✗ AI分析器初始化失败: {e}")
        return False


if __name__ == "__main__":
    # 测试代码
    test_ai_analyzer()

