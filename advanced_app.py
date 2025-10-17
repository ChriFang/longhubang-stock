import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from analysis import YouZiAnalyzer
from database import YouZiDatabase
import config

# 页面配置
st.set_page_config(
    page_title="游资AI分析系统",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化
@st.cache_resource
def init_database():
    return YouZiDatabase()

@st.cache_resource
def init_analyzer():
    return YouZiAnalyzer(init_database())

db = init_database()
analyzer = init_analyzer()

# 侧边栏
st.sidebar.title("🤖 游资AI分析")

# 主页面
st.title("🎯 游资AI智能分析系统")

# 功能选择
analysis_type = st.sidebar.selectbox(
    "选择分析类型",
    ["游资排名", "胜率分析", "交易模式分析", "AI综合分析", "趋势预测"]
)

if analysis_type == "游资排名":
    st.header("📊 游资排名分析")
    
    col1, col2 = st.columns(2)
    with col1:
        ranking_metric = st.selectbox(
            "排名指标",
            ["总买入金额", "胜率", "交易次数"],
            key="ranking_metric"
        )
    with col2:
        days = st.slider("分析天数", 7, 365, 30, key="ranking_days")
    
    metric_map = {
        "总买入金额": "total_amount",
        "胜率": "win_rate", 
        "交易次数": "frequency"
    }
    
    if st.button("生成排名", type="primary"):
        with st.spinner("正在生成排名..."):
            ranking_df = analyzer.get_youzi_ranking(metric_map[ranking_metric], days)
            
            if not ranking_df.empty:
                st.success(f"成功生成 {len(ranking_df)} 位游资排名")
                
                # 显示排名表格
                st.dataframe(ranking_df, width='stretch', height=400)
                
                # 可视化图表
                if ranking_metric == "总买入金额":
                    fig = px.bar(ranking_df.head(10), x='yzmc', y='总买入金额',
                                title='游资买入金额Top10')
                    st.plotly_chart(fig, use_container_width=True)
                elif ranking_metric == "胜率":
                    fig = px.bar(ranking_df.head(10), x='yzmc', y='胜率',
                                title='游资胜率Top10')
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("暂无数据，请先获取数据")

elif analysis_type == "胜率分析":
    st.header("🎯 游资胜率分析")
    
    # 获取所有游资列表
    db_info = db.get_date_range()
    if db_info['total_records'] > 0:
        df = db.get_records_by_date('2020-01-01', datetime.now().strftime('%Y-%m-%d'))
        youzi_list = df['yzmc'].unique().tolist()
        
        selected_youzi = st.selectbox("选择游资", youzi_list)
        days = st.slider("分析周期(天)", 30, 365, 90)
        
        if st.button("分析胜率", type="primary"):
            with st.spinner("正在分析胜率..."):
                win_rate_data = analyzer.calculate_win_rate(selected_youzi, days)
                
                if win_rate_data['total_trades'] > 0:
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("总交易次数", win_rate_data['total_trades'])
                    with col2:
                        st.metric("胜率", f"{win_rate_data['win_rate']}%")
                    with col3:
                        st.metric("盈利交易", win_rate_data['profitable_trades'])
                    with col4:
                        st.metric("平均盈利", f"{win_rate_data['avg_profit']:,.0f}")
                    
                    # 胜率图表
                    fig = go.Figure()
                    fig.add_trace(go.Indicator(
                        mode="gauge+number",
                        value=win_rate_data['win_rate'],
                        title={'text': "胜率"},
                        domain={'x': [0, 1], 'y': [0, 1]},
                        gauge={
                            'axis': {'range': [0, 100]},
                            'bar': {'color': "green"},
                            'steps': [
                                {'range': [0, 40], 'color': "lightgray"},
                                {'range': [40, 70], 'color': "yellow"},
                                {'range': [70, 100], 'color': "lightgreen"}
                            ]
                        }
                    ))
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("该游资在选定周期内无交易记录")
    else:
        st.info("请先获取数据后再进行分析")

elif analysis_type == "交易模式分析":
    st.header("🔍 交易模式分析")
    
    db_info = db.get_date_range()
    if db_info['total_records'] > 0:
        df = db.get_records_by_date('2020-01-01', datetime.now().strftime('%Y-%m-%d'))
        youzi_list = df['yzmc'].unique().tolist()
        
        selected_youzi = st.selectbox("选择游资", youzi_list, key="pattern_youzi")
        
        if st.button("分析交易模式", type="primary"):
            with st.spinner("正在分析交易模式..."):
                pattern_data = analyzer.analyze_trading_patterns(selected_youzi)
                
                if pattern_data:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("交易天数", pattern_data['trading_days'])
                    with col2:
                        st.metric("总交易次数", pattern_data['total_trades'])
                    with col3:
                        st.metric("日均交易", pattern_data['avg_trades_per_day'])
                    
                    # 金额统计
                    st.subheader("💰 金额分布")
                    amount_stats = pattern_data['amount_stats']
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("最小金额", f"{amount_stats['min_amount']:,.0f}")
                    with col2:
                        st.metric("最大金额", f"{amount_stats['max_amount']:,.0f}")
                    with col3:
                        st.metric("平均金额", f"{amount_stats['avg_amount']:,.0f}")
                    with col4:
                        st.metric("中位数", f"{amount_stats['median_amount']:,.0f}")
                    
                    # 股票偏好
                    st.subheader("📈 股票偏好")
                    stock_df = pd.DataFrame(list(pattern_data['stock_preferences'].items()),
                                          columns=['股票名称', '交易次数'])
                    st.dataframe(stock_df, width='stretch')
                    
                    # 概念偏好
                    st.subheader("🏷️ 概念偏好")
                    concept_df = pd.DataFrame(list(pattern_data['concept_preferences'].items()),
                                           columns=['概念', '出现次数'])
                    st.dataframe(concept_df, width='stretch')
                else:
                    st.warning("无法分析该游资的交易模式")
    else:
        st.info("请先获取数据后再进行分析")

elif analysis_type == "AI综合分析":
    st.header("🤖 AI智能综合分析")
    
    db_info = db.get_date_range()
    if db_info['total_records'] > 0:
        df = db.get_records_by_date('2020-01-01', datetime.now().strftime('%Y-%m-%d'))
        youzi_list = df['yzmc'].unique().tolist()
        
        selected_youzi = st.selectbox("选择游资", youzi_list, key="ai_youzi")
        
        if st.button("生成AI分析", type="primary"):
            with st.spinner("AI正在分析中..."):
                ai_insights = analyzer.generate_ai_insights(selected_youzi)
                
                if 'error' not in ai_insights:
                    st.success("AI分析完成")
                    
                    # 显示分析结果
                    st.subheader("📋 分析摘要")
                    st.info(ai_insights['summary'])
                    
                    st.subheader("🎯 关键见解")
                    for insight in ai_insights['insights']:
                        st.write(f"• {insight}")
                    
                    st.subheader("⚠️ 风险水平")
                    risk_level = ai_insights['risk_level']
                    if risk_level == '高风险':
                        st.error(f"风险等级: {risk_level}")
                    elif risk_level == '中风险':
                        st.warning(f"风险等级: {risk_level}")
                    else:
                        st.success(f"风险等级: {risk_level}")
                    
                    st.subheader("💡 投资建议")
                    st.info(ai_insights['recommendation'])
                else:
                    st.warning(ai_insights['error'])
    else:
        st.info("请先获取数据后再进行分析")

elif analysis_type == "趋势预测":
    st.header("🔮 股票趋势预测")
    
    st.info("""
    **趋势预测功能说明：**
    - 基于游资活动数据预测短期趋势
    - 分析游资净流入、参与数量等指标
    - 提供趋势方向和置信度
    """)
    
    stock_code = st.text_input("输入股票代码", placeholder="例如: 001337")
    
    if st.button("预测趋势", type="primary"):
        if stock_code:
            with st.spinner("正在分析趋势..."):
                prediction = analyzer.predict_trend(stock_code)
                
                if prediction['trend'] != 'unknown':
                    st.subheader("📊 预测结果")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if prediction['trend'] == 'bullish':
                            st.success("📈 看涨趋势")
                        elif prediction['trend'] == 'bearish':
                            st.error("📉 看跌趋势")
                        else:
                            st.info("➡️ 中性趋势")
                    
                    with col2:
                        st.metric("置信度", f"{prediction['confidence']}%")
                    
                    # 详细信息
                    st.subheader("📋 分析指标")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("总买入金额", f"{prediction['total_buy_amount']:,.0f}")
                    with col2:
                        st.metric("净流入", f"{prediction['net_inflow']:,.0f}")
                    with col3:
                        st.metric("游资数量", prediction['youzi_count'])
                else:
                    st.warning("数据不足，无法进行预测")
        else:
            st.warning("请输入股票代码")

# 页脚信息
st.sidebar.markdown("---")
st.sidebar.info("""
**AI分析功能说明：**
- 胜率分析：基于历史数据计算游资盈利能力
- 模式分析：识别游资的交易习惯和偏好
- AI分析：综合评估游资的投资价值
- 趋势预测：基于游资活动预测股票短期走势
""")