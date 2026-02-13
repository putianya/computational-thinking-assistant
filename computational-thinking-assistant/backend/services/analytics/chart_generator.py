# -*- coding: utf-8 -*-
"""
图表数据生成器
为前端生成各种图表所需的数据格式
"""

from services.analytics.stats_calculator import StatsCalculator
from services.analytics.weakness_analyzer import WeaknessAnalyzer


class ChartGenerator:
    """图表数据生成器"""
    
    @staticmethod
    def generate_learning_trend_chart(user_id, days=30):
        """
        生成学习趋势图数据（折线图）
        
        Args:
            user_id: 用户ID
            days: 统计天数
        
        Returns:
            dict: ECharts 格式数据
        """
        trend_data = StatsCalculator.get_learning_trend(user_id, days)
        
        return {
            'title': f'最近 {days} 天学习趋势',
            'xAxis': {
                'type': 'category',
                'data': [item['date'] for item in trend_data]
            },
            'yAxis': [
                {
                    'type': 'value',
                    'name': '活动次数'
                },
                {
                    'type': 'value',
                    'name': '正确率 (%)',
                    'max': 100
                }
            ],
            'series': [
                {
                    'name': '总活动',
                    'type': 'line',
                    'data': [item['total_count'] for item in trend_data],
                    'smooth': True
                },
                {
                    'name': '代码提交',
                    'type': 'line',
                    'data': [item['code_count'] for item in trend_data],
                    'smooth': True
                },
                {
                    'name': '正确率',
                    'type': 'line',
                    'data': [item['accuracy'] for item in trend_data],
                    'yAxisIndex': 1,
                    'smooth': True,
                    'itemStyle': {'color': '#67C23A'}
                }
            ]
        }
    
    @staticmethod
    def generate_knowledge_mastery_chart(user_id, days=30):
        """
        生成知识点掌握度雷达图数据
        
        Args:
            user_id: 用户ID
            days: 统计天数
        
        Returns:
            dict: ECharts 雷达图数据
        """
        mastery_data = StatsCalculator.get_knowledge_mastery(user_id, days)
        
        # 取前8个最常见的知识点
        top_topics = mastery_data[:8]
        
        return {
            'title': '知识点掌握度',
            'radar': {
                'indicator': [
                    {'name': item['topic'], 'max': 100}
                    for item in top_topics
                ]
            },
            'series': [
                {
                    'type': 'radar',
                    'data': [
                        {
                            'value': [item['mastery'] for item in top_topics],
                            'name': '掌握度'
                        }
                    ]
                }
            ]
        }
    
    @staticmethod
    def generate_error_distribution_chart(user_id):
        """
        生成错误分布饼图数据
        
        Args:
            user_id: 用户ID
        
        Returns:
            dict: ECharts 饼图数据
        """
        error_data = StatsCalculator.get_error_distribution(user_id)
        distribution = error_data['distribution']
        
        # 类型映射
        type_names = {
            'syntax': '语法错误',
            'logic': '逻辑错误',
            'concept': '概念错误'
        }
        
        return {
            'title': '错误类型分布',
            'series': [
                {
                    'type': 'pie',
                    'radius': '55%',
                    'data': [
                        {
                            'value': dist['occurrences'],
                            'name': type_names.get(error_type, error_type)
                        }
                        for error_type, dist in distribution.items()
                        if dist['occurrences'] > 0
                    ],
                    'emphasis': {
                        'itemStyle': {
                            'shadowBlur': 10,
                            'shadowOffsetX': 0,
                            'shadowColor': 'rgba(0, 0, 0, 0.5)'
                        }
                    }
                }
            ]
        }
    
    @staticmethod
    def generate_code_quality_chart(user_id, days=30):
        """
        生成代码质量趋势图（折线图 + 移动平均）
        
        Args:
            user_id: 用户ID
            days: 统计天数
        
        Returns:
            dict: ECharts 数据
        """
        quality_data = StatsCalculator.get_code_quality_trend(user_id, days)
        
        return {
            'title': '代码质量趋势',
            'xAxis': {
                'type': 'category',
                'data': [f'第{i+1}次' for i in range(len(quality_data))]
            },
            'yAxis': {
                'type': 'value',
                'name': '评分',
                'max': 100
            },
            'series': [
                {
                    'name': '实际得分',
                    'type': 'line',
                    'data': [item['score'] for item in quality_data],
                    'itemStyle': {'color': '#409EFF'}
                },
                {
                    'name': '移动平均',
                    'type': 'line',
                    'data': [item.get('moving_avg', item['score']) for item in quality_data],
                    'smooth': True,
                    'itemStyle': {'color': '#67C23A'}
                }
            ]
        }
    
    @staticmethod
    def generate_activity_heatmap_chart(user_id, days=90):
        """
        生成活动热力图数据
        
        Args:
            user_id: 用户ID
            days: 统计天数
        
        Returns:
            dict: ECharts 热力图数据
        """
        heatmap_data = StatsCalculator.get_activity_heatmap(user_id, days)
        hourly_counts = heatmap_data['hourly_counts']
        
        # 构建数据点 [hour, day, count]
        # 简化版：只显示小时维度
        data_points = [
            [hour, 0, count]
            for hour, count in enumerate(hourly_counts)
        ]
        
        return {
            'title': '学习活跃时段',
            'xAxis': {
                'type': 'category',
                'data': [f'{i}:00' for i in range(24)],
                'name': '时间'
            },
            'yAxis': {
                'type': 'category',
                'data': ['活动量']
            },
            'visualMap': {
                'min': 0,
                'max': max(hourly_counts) if hourly_counts else 1,
                'calculable': True,
                'orient': 'horizontal',
                'left': 'center',
                'bottom': '0%'
            },
            'series': [
                {
                    'type': 'heatmap',
                    'data': data_points,
                    'label': {
                        'show': True
                    }
                }
            ]
        }