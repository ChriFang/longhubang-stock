import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from api_client import YouZiAPI
from data_manager import DataManager
from database import YouZiDatabase
from ai_analyzer import AILongHuAnalyzer
import config

# 页面配置
st.set_page_config(
    page_title="游资龙虎榜分析系统",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化
@st.cache_resource
def init_api():
    return YouZiAPI()

@st.cache_resource
def init_data_manager():
    return DataManager()

@st.cache_resource
def init_database():
    return YouZiDatabase()

@st.cache_resource
def init_ai_analyzer():
    try:
        return AILongHuAnalyzer()
    except Exception as e:
        return None

api_client = init_api()
data_manager = init_data_manager()
db = init_database()
ai_analyzer = init_ai_analyzer()

# 侧边栏
st.sidebar.title("📊 游资龙虎榜分析")

# 日期选择
st.sidebar.subheader("查询设置")
date_option = st.sidebar.radio(
    "查询方式",
    ["单日查询", "日期范围查询"]
)

if date_option == "单日查询":
    selected_date = st.sidebar.date_input(
        "选择日期",
        value=datetime.now() - timedelta(days=1),
        max_value=datetime.now() - timedelta(days=1)
    )
    start_date = end_date = selected_date.strftime('%Y-%m-%d')
else:
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.date_input(
            "开始日期",
            value=datetime.now() - timedelta(days=config.DEFAULT_DATE_RANGE_DAYS),
            max_value=datetime.now() - timedelta(days=1)
        )
    with col2:
        end_date = st.date_input(
            "结束日期",
            value=datetime.now() - timedelta(days=1),
            max_value=datetime.now() - timedelta(days=1)
        )
    
    start_date = start_date.strftime('%Y-%m-%d')
    end_date = end_date.strftime('%Y-%m-%d')

# 过滤选项
st.sidebar.subheader("数据过滤")
min_amount = st.sidebar.number_input(
    "最小金额(万元)", 
    min_value=0, 
    value=100, 
    step=50
) * 10000

# 主页面
st.title("🏦 游资龙虎榜跟踪分析系统")

# 数据获取
if st.sidebar.button("开始查询", type="primary"):
    with st.spinner("正在获取数据..."):
        cache_key = f"{start_date}_{end_date}"
        
        # 尝试从缓存加载
        df = data_manager.load_from_cache(cache_key)
        
        if df is None or df.empty:
            # 从API获取数据
            if start_date == end_date:
                df = api_client.get_youzi_data(start_date)
            else:
                df = api_client.get_date_range_data(start_date, end_date)
            
            if df is not None and not df.empty:
                # 保存到缓存
                data_manager.save_to_cache(cache_key, df)
        
        if df is not None and not df.empty:
            # 保存到数据库
            db.save_records(df)
            st.session_state.df = df
            st.success(f"成功获取 {len(df)} 条记录并保存到数据库")
        else:
            st.error("未获取到数据，请检查日期或网络连接")

# 数据显示
if 'df' in st.session_state and not st.session_state.df.empty:
    df = st.session_state.df
    
    # 数据过滤
    df_filtered = df[df['mrje'] >= min_amount].copy()
    
    # 基本信息
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("总记录数", len(df))
    with col2:
        st.metric("过滤后记录", len(df_filtered))
    with col3:
        total_amount = df_filtered['mrje'].sum() / 100000000
        st.metric("总买入金额(亿元)", f"{total_amount:.2f}")
    with col4:
        avg_amount = df_filtered['mrje'].mean() / 10000
        st.metric("平均买入(万元)", f"{avg_amount:.0f}")
    
    # 标签页
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 数据表格", "📈 趋势分析", "🏦 游资分析", "📋 股票分析", "🤖 AI深度分析", "🗃️ 数据库管理"
    ])
    
    with tab1:
        # 数据表格
        st.subheader("详细数据")
        
        # 列配置
        display_columns = ['rq', 'yzmc', 'yyb', 'gpmc', 'gpdm', 'mrje', 'mcje', 'jlrje', 'gl']
        column_config = {
            'rq': st.column_config.DateColumn("日期", format="YYYY-MM-DD"),
            'yzmc': "游资名称",
            'yyb': "营业部",
            'gpmc': "股票名称", 
            'gpdm': "股票代码",
            'mrje': st.column_config.NumberColumn("买入金额(元)", format="%.0f"),
            'mcje': st.column_config.NumberColumn("卖出金额(元)", format="%.0f"),
            'jlrje': st.column_config.NumberColumn("净流入(元)", format="%.0f"),
            'gl': "概念"
        }
        
        st.dataframe(
            df_filtered[display_columns],
            column_config=column_config,
            width='stretch',
            height=400
        )
    
    with tab2:
        # 趋势分析
        st.subheader("金额趋势分析")
        
        if start_date != end_date:
            # 按日期分组
            daily_stats = df_filtered.groupby('rq').agg({
                'mrje': 'sum',
                'mcje': 'sum', 
                'jlrje': 'sum',
                'yzmc': 'count'
            }).reset_index()
            daily_stats.rename(columns={'yzmc': 'count'}, inplace=True)
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=daily_stats['rq'], 
                y=daily_stats['mrje']/100000000,
                mode='lines+markers',
                name='买入金额(亿元)',
                line=dict(color='green', width=2)
            ))
            fig.add_trace(go.Scatter(
                x=daily_stats['rq'], 
                y=daily_stats['mcje']/100000000,
                mode='lines+markers', 
                name='卖出金额(亿元)',
                line=dict(color='red', width=2)
            ))
            
            fig.update_layout(
                title='游资买卖金额趋势',
                xaxis_title='日期',
                yaxis_title='金额(亿元)',
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # 游资活跃度
        st.subheader("游资活跃度排行")
        youzi_stats = df_filtered.groupby('yzmc').agg({
            'mrje': ['sum', 'count'],
            'jlrje': 'sum'
        }).round(0)
        youzi_stats.columns = ['总买入金额', '上榜次数', '净流入总额']
        youzi_stats = youzi_stats.sort_values('总买入金额', ascending=False)
        
        st.dataframe(youzi_stats.head(10), width='stretch')
    
    with tab3:
        # 游资分析
        st.subheader("游资详细分析")
        
        selected_youzi = st.selectbox(
            "选择游资",
            options=df_filtered['yzmc'].unique()
        )
        
        youzi_data = df_filtered[df_filtered['yzmc'] == selected_youzi]
        
        if not youzi_data.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("上榜次数", len(youzi_data))
                st.metric("总买入金额(万元)", f"{youzi_data['mrje'].sum()/10000:.0f}")
            
            with col2:
                st.metric("平均买入(万元)", f"{youzi_data['mrje'].mean()/10000:.0f}")
                st.metric("净流入总额(万元)", f"{youzi_data['jlrje'].sum()/10000:.0f}")
            
            # 最近操作
            st.write("最近操作记录:")
            recent_ops = youzi_data.sort_values('rq', ascending=False).head(10)
            st.dataframe(recent_ops[['rq', 'gpmc', 'mrje', 'mcje', 'jlrje']], width='stretch')
    
    with tab4:
        # 股票分析
        st.subheader("股票关注度分析")
        
        stock_stats = df_filtered.groupby(['gpmc', 'gpdm']).agg({
            'mrje': ['sum', 'count'],
            'yzmc': 'nunique'
        }).round(0)
        stock_stats.columns = ['总买入金额', '上榜次数', '游资数量']
        stock_stats = stock_stats.sort_values('总买入金额', ascending=False)
        
        st.dataframe(stock_stats.head(15), width='stretch')
    
    with tab5:
        # AI深度分析
        st.subheader("🤖 AI深度分析 - 基于 DeepSeek")
        
        # 检查AI分析器是否初始化成功
        if ai_analyzer is None:
            st.error("⚠️ AI分析功能未启用")
            st.info("""
            **启用AI分析功能的步骤：**
            
            1. 访问 [DeepSeek 开放平台](https://platform.deepseek.com/) 注册账号
            2. 在控制台获取 API Key
            3. 在项目根目录创建 `.env` 文件
            4. 在 `.env` 文件中添加：`DEEPSEEK_API_KEY=你的API密钥`
            5. 重启应用
            
            DeepSeek 提供 OpenAI 兼容接口，可直接用于本项目的龙虎榜分析功能。
            """)
        else:
            st.success("✅ AI分析引擎已就绪")
            
            # 选择分析类型
            analysis_type = st.selectbox(
                "选择分析类型",
                ["🎯 机会股票挖掘", "📜 历史分析记录", "单股深度分析", "市场热点分析", "游资风格分析"],
                key="ai_analysis_type"
            )
            
            if analysis_type == "🎯 机会股票挖掘":
                st.markdown("### 🎯 AI智能挖掘机会股票")
                st.info("""
                **AI将从所有龙虎榜股票中智能筛选次日大概率上涨的机会股票**
                
                评分维度：
                - 💎 买入资金含金量（0-30分）：顶级游资、多游资合力
                - 💰 净买入额（0-25分）：真金白银的硬实力
                - 📉 卖出压力（0-20分）：主力了结vs散户离场
                - 🤝 机构共振（0-15分）：机构+游资联动（重点关注）
                - ⭐ 其他加分项（0-10分）：买卖比、主力集中度、热门概念
                
                **满分100分，分数越高，次日上涨概率越大！**
                """)
                
                # 选择显示数量
                top_n = st.slider(
                    "显示Top N股票",
                    min_value=5,
                    max_value=20,
                    value=10,
                    step=5,
                    key="opportunity_top_n"
                )
                
                if st.button("🚀 开始AI智能挖掘", type="primary", key="ai_opportunity_analysis"):
                    with st.spinner("AI正在分析所有股票，挖掘投资机会..."):
                        # 获取分析日期
                        analysis_date = df_filtered['rq'].dt.strftime('%Y-%m-%d').values[0]
                        
                        # 调用AI分析
                        result = ai_analyzer.analyze_opportunity_stocks(df_filtered, analysis_date, top_n)
                        
                        if result['success']:
                            # 保存到数据库
                            analysis_id = db.save_ai_analysis(result)
                            if analysis_id > 0:
                                st.success(f"✅ AI分析完成！从{result['total_stocks']}只股票中筛选出{len(result['top_stocks'])}只机会股票（已保存到历史记录，ID: {analysis_id}）")
                            else:
                                st.success(f"✅ AI分析完成！从{result['total_stocks']}只股票中筛选出{len(result['top_stocks'])}只机会股票")
                            
                            # 显示评分排名
                            st.markdown("---")
                            st.markdown("### 📊 AI智能评分排名")
                            
                            # 创建评分表格
                            score_data = []
                            for i, stock in enumerate(result['top_stocks'], 1):
                                score_data.append({
                                    '排名': f"🏆 {i}" if i <= 3 else str(i),
                                    '股票名称': stock['stock_name'],
                                    '股票代码': stock['stock_code'],
                                    '综合评分': f"{stock['total_score']:.1f}",
                                    '资金含金量': f"{stock['money_quality_score']}分",
                                    '净买入额': f"{stock['net_inflow_score']}分",
                                    '卖出压力': f"{stock['sell_pressure_score']}分",
                                    '机构共振': f"{stock['institution_score']}分",
                                    '加分项': f"{stock['bonus_score']}分",
                                    '顶级游资': f"{stock['top_youzi_count']}家",
                                    '买方数': f"{stock['buyer_count']}家",
                                    '机构参与': '✅' if stock['has_institution'] else '❌',
                                    '净流入': f"{stock['net_inflow']/10000:.2f}万"
                                })
                            
                            score_df = pd.DataFrame(score_data)
                            st.dataframe(score_df, use_container_width=True, height=400)
                            
                            # 显示前3名的详细信息
                            st.markdown("### 🏆 Top 3 股票详情")
                            
                            for i, stock in enumerate(result['top_stocks'][:3], 1):
                                with st.expander(f"🏆 第{i}名：{stock['stock_name']}（{stock['stock_code']}）- {stock['total_score']:.1f}分", expanded=(i==1)):
                                    col1, col2, col3, col4 = st.columns(4)
                                    
                                    with col1:
                                        st.metric("综合评分", f"{stock['total_score']:.1f}分")
                                        st.metric("资金含金量", f"{stock['money_quality_score']}分")
                                    with col2:
                                        st.metric("净买入额", f"{stock['net_inflow_score']}分")
                                        st.metric("卖出压力", f"{stock['sell_pressure_score']}分")
                                    with col3:
                                        st.metric("机构共振", f"{stock['institution_score']}分")
                                        st.metric("加分项", f"{stock['bonus_score']}分")
                                    with col4:
                                        st.metric("顶级游资", f"{stock['top_youzi_count']}家")
                                        st.metric("净流入", f"{stock['net_inflow']/10000:.2f}万")
                                    
                                    st.write("**相关概念：**", stock['concepts'])
                                    
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.write("**买入方：**")
                                        for _, row in stock['buy_data'].iterrows():
                                            st.text(f"  {row['yzmc']}: {row['mrje']/10000:.2f}万")
                                    with col2:
                                        st.write("**卖出方：**")
                                        if len(stock['sell_data']) > 0:
                                            for _, row in stock['sell_data'].iterrows():
                                                st.text(f"  {row['yzmc']}: {row['mcje']/10000:.2f}万")
                                        else:
                                            st.text("  无卖出（最佳状态）")
                            
                            # AI专家分析
                            st.markdown("---")
                            st.markdown("### 🎯 AI专家深度分析")
                            st.markdown(result['ai_analysis'])
                            
                            # 下载按钮
                            st.markdown("---")
                            col1, col2 = st.columns(2)
                            with col1:
                                # 导出评分表格
                                csv_data = score_df.to_csv(index=False, encoding='utf-8-sig')
                                st.download_button(
                                    label="📥 下载评分表格（CSV）",
                                    data=csv_data,
                                    file_name=f"AI机会股票_{analysis_date}.csv",
                                    mime="text/csv"
                                )
                            with col2:
                                # 导出AI分析报告
                                report = f"""AI龙虎榜机会股票分析报告
日期：{result['date']}
分析时间：{result['timestamp']}
AI模型：{result['model']}
上榜股票总数：{result['total_stocks']}只
机会股票数：{len(result['top_stocks'])}只

=== AI专家分析 ===

{result['ai_analysis']}

=== 评分明细 ===

"""
                                for stock in result['top_stocks']:
                                    report += f"\n{stock['stock_name']}（{stock['stock_code']}）\n"
                                    report += f"综合评分：{stock['total_score']:.1f}分\n"
                                    report += f"- 资金含金量：{stock['money_quality_score']}分\n"
                                    report += f"- 净买入额：{stock['net_inflow_score']}分\n"
                                    report += f"- 卖出压力：{stock['sell_pressure_score']}分\n"
                                    report += f"- 机构共振：{stock['institution_score']}分\n"
                                    report += f"- 加分项：{stock['bonus_score']}分\n"
                                    report += f"净流入：{stock['net_inflow']/10000:.2f}万元\n"
                                    report += "-" * 50 + "\n"
                                
                                st.download_button(
                                    label="📥 下载分析报告（TXT）",
                                    data=report,
                                    file_name=f"AI分析报告_{analysis_date}.txt",
                                    mime="text/plain"
                                )
                            
                            # 使用提示
                            st.markdown("---")
                            st.warning("""
                            ⚠️ **投资提示**
                            
                            1. AI评分仅供参考，不构成投资建议
                            2. 高分股票次日上涨概率较大，但不是100%
                            3. 建议结合技术面、基本面综合判断
                            4. 注意设置止损止盈位，控制风险
                            5. 关注机构共振股票，往往有更大想象空间
                            6. 顶级游资参与的股票，关注度和活跃度更高
                            """)
                        else:
                            st.error(f"❌ 分析失败：{result['error']}")
            
            elif analysis_type == "📜 历史分析记录":
                st.markdown("### 📜 AI分析历史记录")
                st.info("查看过往的AI机会股票分析记录，支持回顾和对比")
                
                # 选择查询天数
                history_days = st.selectbox(
                    "查询范围",
                    [7, 15, 30, 60, 90],
                    index=2,
                    key="history_days"
                )
                
                # 获取历史记录
                history_df = db.get_ai_analysis_history(days=history_days)
                
                if not history_df.empty:
                    st.markdown(f"### 📊 最近{history_days}天的分析记录（共{len(history_df)}条）")
                    
                    # 显示历史记录列表
                    for idx, row in history_df.iterrows():
                        with st.expander(
                            f"📅 {row['analysis_date']} - 分析了{row['total_stocks']}只股票，筛选Top {row['top_n']} （记录ID: {row['id']}）",
                            expanded=False
                        ):
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("分析日期", row['analysis_date'])
                            with col2:
                                st.metric("上榜股票数", f"{row['total_stocks']}只")
                            with col3:
                                st.metric("筛选数量", f"Top {row['top_n']}")
                            with col4:
                                st.metric("AI模型", row['ai_model'])
                            
                            st.write(f"**创建时间：** {row['created_at']}")
                            
                            # 查看详情按钮
                            col1, col2 = st.columns([1, 3])
                            with col1:
                                if st.button(f"查看完整分析", key=f"view_{row['id']}"):
                                    st.session_state[f'show_detail_{row["id"]}'] = True
                            with col2:
                                if st.button(f"🗑️ 删除此记录", key=f"delete_{row['id']}", type="secondary"):
                                    if db.delete_ai_analysis(row['id']):
                                        st.success("记录已删除")
                                        st.rerun()
                                    else:
                                        st.error("删除失败")
                            
                            # 显示详情
                            if st.session_state.get(f'show_detail_{row["id"]}', False):
                                st.markdown("---")
                                detail = db.get_ai_analysis_detail(row['id'])
                                
                                if detail:
                                    # 显示评分表格
                                    st.markdown("#### 📊 AI智能评分排名")
                                    score_data = []
                                    for stock in detail['stock_scores']:
                                        score_data.append({
                                            '排名': f"🏆 {stock['rank']}" if stock['rank'] <= 3 else str(stock['rank']),
                                            '股票名称': stock['stock_name'],
                                            '股票代码': stock['stock_code'],
                                            '综合评分': f"{stock['total_score']:.1f}",
                                            '资金含金量': f"{stock['money_quality_score']}分",
                                            '净买入额': f"{stock['net_inflow_score']}分",
                                            '卖出压力': f"{stock['sell_pressure_score']}分",
                                            '机构共振': f"{stock['institution_score']}分",
                                            '加分项': f"{stock['bonus_score']}分",
                                            '顶级游资': f"{stock['top_youzi_count']}家",
                                            '机构参与': '✅' if stock['has_institution'] else '❌',
                                            '净流入': f"{stock['net_inflow']/10000:.2f}万"
                                        })
                                    
                                    score_df = pd.DataFrame(score_data)
                                    st.dataframe(score_df, use_container_width=True)
                                    
                                    # 显示Top 3详情
                                    st.markdown("#### 🏆 Top 3 股票详情")
                                    for stock in detail['stock_scores'][:3]:
                                        with st.expander(f"🏆 第{stock['rank']}名：{stock['stock_name']}（{stock['stock_code']}）- {stock['total_score']:.1f}分"):
                                            col1, col2, col3, col4 = st.columns(4)
                                            with col1:
                                                st.metric("综合评分", f"{stock['total_score']:.1f}分")
                                                st.metric("资金含金量", f"{stock['money_quality_score']}分")
                                            with col2:
                                                st.metric("净买入额", f"{stock['net_inflow_score']}分")
                                                st.metric("卖出压力", f"{stock['sell_pressure_score']}分")
                                            with col3:
                                                st.metric("机构共振", f"{stock['institution_score']}分")
                                                st.metric("加分项", f"{stock['bonus_score']}分")
                                            with col4:
                                                st.metric("顶级游资", f"{stock['top_youzi_count']}家")
                                                st.metric("净流入", f"{stock['net_inflow']/10000:.2f}万")
                                            
                                            st.write("**相关概念：**", stock['concepts'])
                                            
                                            col1, col2 = st.columns(2)
                                            with col1:
                                                st.write("**买入方：**")
                                                for buy_detail in stock['buy_details']:
                                                    st.text(f"  {buy_detail}")
                                            with col2:
                                                st.write("**卖出方：**")
                                                if stock['sell_details']:
                                                    for sell_detail in stock['sell_details']:
                                                        st.text(f"  {sell_detail}")
                                                else:
                                                    st.text("  无卖出（最佳状态）")
                                    
                                    # 显示AI分析
                                    st.markdown("#### 🎯 AI专家深度分析")
                                    st.markdown(detail['ai_analysis'])
                                    
                                    # 关闭详情按钮
                                    if st.button("收起详情", key=f"hide_{row['id']}"):
                                        st.session_state[f'show_detail_{row["id"]}'] = False
                                        st.rerun()
                else:
                    st.warning(f"最近{history_days}天没有AI分析记录")
                    st.info("使用「🎯 机会股票挖掘」功能进行分析后，记录会自动保存到这里")
            
            elif analysis_type == "单股深度分析":
                st.markdown("### 📈 单股深度分析")
                st.info("AI将从买入资金含金量、净买入额、卖出压力、机构共振等维度深度解析")
                
                # 选择股票
                stock_list = df_filtered['gpmc'].unique().tolist()
                selected_stock = st.selectbox(
                    "选择要分析的股票",
                    stock_list,
                    key="ai_stock"
                )
                
                if st.button("🚀 开始AI深度分析", type="primary", key="ai_stock_analysis"):
                    with st.spinner("AI正在深度分析中，请稍候..."):
                        # 获取该股票的数据
                        stock_data = df_filtered[df_filtered['gpmc'] == selected_stock]
                        
                        # 调用AI分析
                        result = ai_analyzer.analyze_stock_opportunity(stock_data, selected_stock)
                        
                        if result['success']:
                            st.success("✅ AI分析完成")
                            
                            # 显示分析结果
                            st.markdown("---")
                            st.markdown("### 📊 AI分析报告")
                            
                            # 基本信息
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("股票代码", result['context']['code'])
                            with col2:
                                st.metric("分析日期", result['context']['date'])
                            with col3:
                                st.metric("净流入", f"{result['context']['net_inflow']:.2f}万")
                            with col4:
                                st.metric("买方数量", f"{result['context']['buyer_count']}家")
                            
                            # AI分析内容
                            st.markdown("### 🎯 专家分析意见")
                            st.markdown(result['analysis'])
                            
                            # 显示原始数据
                            with st.expander("📋 查看原始数据"):
                                st.write("**买入方：**")
                                st.text(result['context']['buy_side'])
                                st.write("**卖出方：**")
                                st.text(result['context']['sell_side'])
                                st.write(f"**相关概念：** {result['context']['concepts']}")
                        else:
                            st.error(f"❌ 分析失败：{result['error']}")
            
            elif analysis_type == "市场热点分析":
                st.markdown("### 🔥 市场热点分析")
                st.info("AI将分析当日市场主线、热点板块、资金流向和次日机会")
                
                if st.button("🚀 开始市场分析", type="primary", key="ai_market_analysis"):
                    with st.spinner("AI正在分析市场热点..."):
                        # 获取分析日期
                        analysis_date = df_filtered['rq'].dt.strftime('%Y-%m-%d').values[0]
                        
                        # 调用AI分析
                        result = ai_analyzer.analyze_market_hotspots(df_filtered, analysis_date)
                        
                        if result['success']:
                            st.success("✅ 市场分析完成")
                            
                            # 显示市场概况
                            st.markdown("---")
                            st.markdown("### 📊 市场概况")
                            
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("上榜股票", f"{result['context']['stock_count']}只")
                            with col2:
                                st.metric("总成交额", f"{result['context']['total_amount']:.2f}亿")
                            with col3:
                                st.metric("活跃游资", f"{result['context']['active_youzi']}家")
                            with col4:
                                st.metric("分析日期", result['date'])
                            
                            # AI分析内容
                            st.markdown("### 🎯 市场深度分析")
                            st.markdown(result['analysis'])
                            
                            # 显示详细数据
                            with st.expander("📋 查看市场详情"):
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.write("**净流入前5股票：**")
                                    st.text(result['context']['top_inflow_stocks'])
                                    st.write("**热门概念：**")
                                    st.text(result['context']['hot_concepts'])
                                with col2:
                                    st.write("**最活跃游资：**")
                                    st.text(result['context']['active_youzi_list'])
                                    st.write("**机构参与：**")
                                    st.text(result['context']['institution_status'])
                        else:
                            st.error(f"❌ 分析失败：{result['error']}")
            
            elif analysis_type == "游资风格分析":
                st.markdown("### 🎭 游资风格分析")
                st.info("AI将分析游资的操盘风格、选股偏好、资金运作特点")
                
                # 选择游资
                youzi_list = df_filtered['yzmc'].unique().tolist()
                selected_youzi = st.selectbox(
                    "选择要分析的游资",
                    youzi_list,
                    key="ai_youzi"
                )
                
                # 选择分析周期
                analysis_days = st.slider(
                    "分析周期（天）",
                    min_value=7,
                    max_value=180,
                    value=30,
                    key="ai_youzi_days"
                )
                
                if st.button("🚀 开始游资分析", type="primary", key="ai_youzi_analysis"):
                    with st.spinner("AI正在分析游资风格..."):
                        # 获取游资历史数据
                        end_date = datetime.now().strftime('%Y-%m-%d')
                        start_date = (datetime.now() - timedelta(days=analysis_days)).strftime('%Y-%m-%d')
                        youzi_history = db.get_records_by_date(start_date, end_date)
                        youzi_data = youzi_history[youzi_history['yzmc'] == selected_youzi]
                        
                        if len(youzi_data) > 0:
                            # 调用AI分析
                            result = ai_analyzer.analyze_youzi_style(youzi_data, selected_youzi)
                            
                            if result['success']:
                                st.success("✅ 游资分析完成")
                                
                                # 显示基本数据
                                st.markdown("---")
                                st.markdown("### 📊 游资基本数据")
                                
                                col1, col2, col3, col4 = st.columns(4)
                                with col1:
                                    st.metric("操作次数", f"{result['context']['trade_count']}次")
                                with col2:
                                    st.metric("总买入额", f"{result['context']['total_buy']:.2f}万")
                                with col3:
                                    st.metric("胜率", f"{result['context']['win_rate']:.1f}%")
                                with col4:
                                    st.metric("净流入", f"{result['context']['net_inflow']:.2f}万")
                                
                                # AI分析内容
                                st.markdown("### 🎯 游资画像分析")
                                st.markdown(result['analysis'])
                                
                                # 显示详细数据
                                with st.expander("📋 查看操作详情"):
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.write("**高频操作股票：**")
                                        st.text(result['context']['favorite_stocks'])
                                    with col2:
                                        st.write("**偏好概念板块：**")
                                        st.text(result['context']['favorite_concepts'])
                                    
                                    st.write("**近期操作记录：**")
                                    st.text(result['context']['recent_operations'])
                            else:
                                st.error(f"❌ 分析失败：{result['error']}")
                        else:
                            st.warning(f"该游资在最近{analysis_days}天内无操作记录，请尝试扩大分析周期")
    
    with tab6:
        # 数据库管理
        st.subheader("数据库管理")
        
        # 数据库统计信息
        db_info = db.get_date_range()
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("总记录数", db_info.get('total_records', 0))
        with col2:
            st.metric("最早日期", db_info.get('min_date', '无数据'))
        with col3:
            st.metric("最新日期", db_info.get('max_date', '无数据'))
        
        # 数据库操作
        st.subheader("数据库操作")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("备份数据库", type="secondary"):
                db.backup_database()
                st.success("数据库备份完成")
        
        with col2:
            if st.button("查看数据库统计", type="secondary"):
                # 显示详细统计
                st.write("### 详细统计")
                st.json(db_info)
        
        # 高级分析功能预告
        st.subheader("高级分析功能（开发中）")
        st.info("""
        **即将推出的功能：**
        - 🎯 **游资胜率分析**: 分析游资的历史操作胜率
        - 📈 **盈利情况统计**: 计算游资的盈利能力和风险水平  
        - 🤖 **AI综合分析**: 使用机器学习分析游资操作模式
        - 📊 **模式识别**: 识别游资的操盘习惯和偏好
        - 🔮 **预测分析**: 基于历史数据的趋势预测
        """)

else:
    st.info("👈 请在侧边栏设置查询条件并点击'开始查询'")

# 页脚信息
st.sidebar.markdown("---")
st.sidebar.info(
    f"""
    **数据说明:**
    - 数据来源: {config.API_BASE_URL}
    - 更新频率: 交易日下午5点40
    - 免费额度: {config.FREE_QUOTA_PER_DAY}次/天
    - 速率限制: {config.API_RATE_LIMIT}次/秒
    """
)