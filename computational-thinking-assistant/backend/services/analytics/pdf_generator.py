# -*- coding: utf-8 -*-
"""
PDF 学情报告生成器（使用 reportlab）
"""
from io import BytesIO
from datetime import datetime
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


def _register_fonts():
    """注册中文字体"""
    font_candidates = [
        ("MSYaHei", "C:/Windows/Fonts/msyh.ttc"),
        ("MSYaHei", "C:/Windows/Fonts/msyhbd.ttc"),
        ("SimHei",  "C:/Windows/Fonts/simhei.ttf"),
        ("SimSun",  "C:/Windows/Fonts/simsun.ttc"),
    ]
    bold_candidates = [
        ("MSYaHei-Bold", "C:/Windows/Fonts/msyhbd.ttc"),
        ("SimHei",       "C:/Windows/Fonts/simhei.ttf"),
    ]

    registered_name = "Helvetica"
    for name, path in font_candidates:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont(name, path))
                registered_name = name
                break
            except Exception:
                continue

    registered_bold = registered_name
    for name, path in bold_candidates:
        if os.path.exists(path) and name not in pdfmetrics.getRegisteredFontNames():
            try:
                pdfmetrics.registerFont(TTFont(name, path))
                registered_bold = name
                break
            except Exception:
                continue

    return registered_name, registered_bold


class PDFReportGenerator:
    COLOR_PRIMARY   = colors.HexColor("#667eea")
    COLOR_SECONDARY = colors.HexColor("#764ba2")
    COLOR_SUCCESS   = colors.HexColor("#28a745")
    COLOR_WARNING   = colors.HexColor("#ffc107")
    COLOR_DANGER    = colors.HexColor("#dc3545")
    COLOR_LIGHT_BG  = colors.HexColor("#f5f7fa")
    COLOR_BORDER    = colors.HexColor("#e0e0e0")
    COLOR_TEXT      = colors.HexColor("#333333")
    COLOR_MUTED     = colors.HexColor("#666666")

    # ⭐ emoji → 纯文字映射（解决方框问题）
    ICON_LABELS = {
        "learning":   "[学习]",
        "question":   "[提问]",
        "code":       "[代码]",
        "correct":    "[正确]",
        "active":     "[活跃]",
        "knowledge":  "[知识]",
        "fire":       "[热度]",
        "chart":      "[统计]",
        "report":     "[报告]",
        "star":       "[*]",
        "warn":       "[!]",
        "ok":         "[OK]",
        "book":       "[知识块]",
    }

    def __init__(self):
        self.font_name, self.font_bold = _register_fonts()
        self._init_styles()

    def _init_styles(self):
        fn = self.font_name
        fb = self.font_bold
        self.styles = {
            'cover_title': ParagraphStyle(
                'cover_title', fontName=fb, fontSize=14,
                textColor=self.COLOR_PRIMARY, alignment=TA_CENTER, spaceAfter=4),
            'cover_subtitle': ParagraphStyle(
                'cover_subtitle', fontName=fn, fontSize=10,
                textColor=self.COLOR_MUTED, alignment=TA_CENTER, spaceAfter=4),
            'meta': ParagraphStyle(
                'meta', fontName=fn, fontSize=9,
                textColor=self.COLOR_MUTED, alignment=TA_CENTER, spaceAfter=3),
            'section_title': ParagraphStyle(
                'section_title', fontName=fb, fontSize=12,
                textColor=self.COLOR_PRIMARY, spaceBefore=10, spaceAfter=5),
            'subsection_title': ParagraphStyle(
                'subsection_title', fontName=fb, fontSize=10,
                textColor=self.COLOR_TEXT, spaceBefore=6, spaceAfter=3),
            'subsection': ParagraphStyle(
                'subsection', fontName=fb, fontSize=10,
                textColor=self.COLOR_TEXT, spaceBefore=6, spaceAfter=3),
            'body': ParagraphStyle(
                'body', fontName=fn, fontSize=9,
                textColor=self.COLOR_TEXT, spaceAfter=3, leading=13),
            'small': ParagraphStyle(
                'small', fontName=fn, fontSize=8,
                textColor=self.COLOR_MUTED, spaceAfter=2),
            'muted': ParagraphStyle(
                'muted', fontName=fn, fontSize=9,
                textColor=self.COLOR_MUTED, spaceAfter=3),
            'card_value': ParagraphStyle(
                'card_value', fontName=fb, fontSize=13,
                textColor=self.COLOR_PRIMARY, alignment=TA_CENTER),
            'card_label': ParagraphStyle(
                'card_label', fontName=fn, fontSize=8,
                textColor=self.COLOR_MUTED, alignment=TA_CENTER),
            'tag_high': ParagraphStyle(
                'tag_high', fontName=fn, fontSize=8,
                textColor=colors.HexColor("#721c24")),
            'tag_medium': ParagraphStyle(
                'tag_medium', fontName=fn, fontSize=8,
                textColor=colors.HexColor("#856404")),
            'tag_low': ParagraphStyle(
                'tag_low', fontName=fn, fontSize=8,
                textColor=colors.HexColor("#155724")),
        }

    # ⭐ 清除 emoji，防止方框
    @staticmethod
    def _safe(text: str) -> str:
        """过滤掉无法被中文字体渲染的字符"""
        if not text:
            return text or ''
        result = []
        for ch in str(text):
            cp = ord(ch)
            # 保留：ASCII + 中文基本区 + 中文扩展区 + 中文标点
            if (cp < 0x2000 or
                0x2E80 <= cp <= 0x9FFF or
                0xF900 <= cp <= 0xFAFF or
                0xFF00 <= cp <= 0xFFEF or
                0x20000 <= cp <= 0x2A6DF):
                result.append(ch)
            else:
                result.append('')  # 直接丢弃 emoji
        return ''.join(result)

    def generate(self, report_data: dict) -> bytes:
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=A4,
            rightMargin=2*cm, leftMargin=2*cm,
            topMargin=2*cm,  bottomMargin=2*cm,
            title="学情分析报告",
            author="计算思维课程助手系统",
        )
        story = []
        story += self._build_cover(report_data)
        story += self._build_overview(report_data)
        story += self._build_score(report_data)
        story += self._build_knowledge(report_data)
        story += self._build_weakness(report_data)
        story += self._build_chunk_heat(report_data)
        story += self._build_recommendations(report_data)
        story += self._build_footer(report_data)
        doc.build(story)
        return buffer.getvalue()

    # ========== 封面 ==========
    def _build_cover(self, data: dict) -> list:
        story = []
        fn = self.font_name
        fb = self.font_bold
        s = self.styles

        story.append(Spacer(1, 1.0*cm))
        # ⭐ 用纯文字替代 emoji 图标
        story.append(Paragraph(
            "[ 学情分析报告 ]",
            ParagraphStyle('cover_icon', fontName=fb, fontSize=16,
                           textColor=self.COLOR_PRIMARY, alignment=TA_CENTER, spaceAfter=2)
        ))
        story.append(Paragraph("计算思维课程助手系统", s['cover_subtitle']))
        story.append(Spacer(1, 0.3*cm))
        story.append(HRFlowable(width="80%", thickness=1, color=self.COLOR_PRIMARY))
        story.append(Spacer(1, 0.4*cm))

        user_info   = data.get('user_info') or {}
        username    = (user_info.get('nickname') or
                       user_info.get('username') or
                       user_info.get('name') or '未知学生')
        period_days = data.get('period_days', 30)
        generated_at = data.get('generated_at', '')
        if generated_at:
            try:
                dt = datetime.fromisoformat(generated_at.replace('Z', '+00:00'))
                generated_at = dt.strftime('%Y年%m月%d日 %H:%M')
            except Exception:
                pass

        for line in [
            f"学生：{self._safe(username)}",
            f"统计周期：最近 {period_days} 天",
            f"生成时间：{generated_at}",
        ]:
            story.append(Paragraph(line, s['meta']))

        score = data.get('score')
        if score:
            story.append(Spacer(1, 0.6*cm))
            score_table = Table([[
                Paragraph(f"<b>{round(score.get('total', 0))}</b>",
                          ParagraphStyle('snum', fontName=fb, fontSize=22,
                                         textColor=self.COLOR_PRIMARY, alignment=TA_CENTER)),
                Paragraph(f"<b>{score.get('grade', '-')}</b>",
                          ParagraphStyle('sgrade', fontName=fb, fontSize=16,
                                         textColor=self.COLOR_SECONDARY, alignment=TA_CENTER)),
                Paragraph(self._safe(score.get('grade_text', '')),
                          ParagraphStyle('stext', fontName=fn, fontSize=10,
                                         textColor=self.COLOR_MUTED, alignment=TA_CENTER)),
            ]], colWidths=[4*cm, 3.5*cm, 6*cm])
            score_table.setStyle(TableStyle([
                ('ALIGN',   (0,0), (-1,-1), 'CENTER'),
                ('VALIGN',  (0,0), (-1,-1), 'MIDDLE'),
                ('BACKGROUND', (0,0), (-1,-1), self.COLOR_LIGHT_BG),
                ('BOX',     (0,0), (-1,-1), 0.5, self.COLOR_BORDER),
                ('TOPPADDING',    (0,0), (-1,-1), 8),
                ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ]))
            story.append(score_table)
        story.append(Spacer(1, 0.8*cm))
        return story

    # ========== 学习概览 ==========
    def _build_overview(self, data: dict) -> list:
        story = []
        s = self.styles
        fn = self.font_name
        fb = self.font_bold

        story.append(Paragraph("一、学习概览", s['section_title']))
        story.append(HRFlowable(width="100%", thickness=0.5,
                                color=self.COLOR_BORDER, spaceAfter=6))

        overview = data.get('overview') or {}
        # ⭐ 全部用纯文字标签
        cards = [
            ("[时长]", f"{overview.get('total_duration_hours', 0)}", "学习时长(h)"),
            ("[提问]", str(overview.get('question_count', 0)),        "提问次数"),
            ("[代码]", str(overview.get('code_count', 0)),            "代码提交"),
            ("[正确]", f"{overview.get('accuracy', 0)}%",             "代码正确率"),
            ("[活跃]", str(overview.get('active_days', 0)),           "活跃天数"),
            ("[知识]", str(overview.get('view_count', 0)),            "涉及知识点"),
        ]

        row_icons   = [Paragraph(c[0], s['card_value'])  for c in cards]
        row_values  = [Paragraph(c[1], s['card_value'])  for c in cards]
        row_labels  = [Paragraph(c[2], s['card_label'])  for c in cards]

        col_w = [2.8*cm] * 6
        t = Table([row_icons, row_values, row_labels], colWidths=col_w)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), self.COLOR_LIGHT_BG),
            ('BOX',        (0,0), (-1,-1), 0.5, self.COLOR_BORDER),
            ('INNERGRID',  (0,0), (-1,-1), 0.3, self.COLOR_BORDER),
            ('ALIGN',      (0,0), (-1,-1), 'CENTER'),
            ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING',    (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.5*cm))
        return story

    # ========== 综合评分 ==========
    def _build_score(self, data: dict) -> list:
        story = []
        s = self.styles
        fn = self.font_name
        fb = self.font_bold

        story.append(Paragraph("二、综合评分", s['section_title']))
        story.append(HRFlowable(width="100%", thickness=0.5,
                                color=self.COLOR_BORDER, spaceAfter=6))

        score = data.get('score') or {}
        details = score.get('details') or {}
        score_map = {
            'time':      ('[时长] 学习时长', 25),
            'activity':  ('[活跃] 活跃程度', 25),
            'code':      ('[代码] 代码质量', 30),
            'knowledge': ('[知识] 学习广度', 20),
        }

        rows = [[
            Paragraph('维度', s['body']),
            Paragraph('得分', s['body']),
            Paragraph('满分', s['body']),
        ]]
        for key, (label, full) in score_map.items():
            val = details.get(key, 0) or 0
            rows.append([
                Paragraph(label, s['body']),
                Paragraph(str(round(val, 1)), s['body']),
                Paragraph(str(full), s['muted']),
            ])

        t = Table(rows, colWidths=[9*cm, 3*cm, 3*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), self.COLOR_PRIMARY),
            ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
            ('FONTNAME',   (0,0), (-1,0), fb),
            ('ALIGN',      (0,0), (-1,-1), 'CENTER'),
            ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, self.COLOR_LIGHT_BG]),
            ('BOX',        (0,0), (-1,-1), 0.5, self.COLOR_BORDER),
            ('INNERGRID',  (0,0), (-1,-1), 0.3, self.COLOR_BORDER),
            ('TOPPADDING',    (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.5*cm))
        return story

    # ========== 知识点掌握 ==========
    def _build_knowledge(self, data: dict) -> list:
        story = []
        s = self.styles
        fn = self.font_name
        fb = self.font_bold

        story.append(Paragraph("三、知识点掌握", s['section_title']))
        story.append(HRFlowable(width="100%", thickness=0.5,
                                color=self.COLOR_BORDER, spaceAfter=6))

        mastery_list = data.get('knowledge_mastery') or []
        if not mastery_list:
            story.append(Paragraph("暂无知识点学习数据", s['body']))
            story.append(Spacer(1, 0.3*cm))
            return story

        rows = [[
            Paragraph('知识点', s['body']),
            Paragraph('掌握度', s['body']),
            Paragraph('学习次数', s['body']),
            Paragraph('状态', s['body']),
        ]]
        for item in mastery_list[:15]:
            mastery = item.get('mastery', 0) or 0
            if mastery >= 80:
                status_text = '已掌握'
                style_key = 'tag_low'
            elif mastery >= 60:
                status_text = '基本掌握'
                style_key = 'tag_medium'
            else:
                status_text = '需加强'
                style_key = 'tag_high'

            rows.append([
                Paragraph(self._safe(str(item.get('topic', ''))), s['body']),
                Paragraph(f"{mastery}%", s['body']),
                Paragraph(str(item.get('total_count', 0)), s['body']),
                Paragraph(status_text, s[style_key]),
            ])

        t = Table(rows, colWidths=[8*cm, 3*cm, 3*cm, 2.5*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), self.COLOR_PRIMARY),
            ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
            ('FONTNAME',   (0,0), (-1,0), fb),
            ('ALIGN',      (0,0), (-1,-1), 'CENTER'),
            ('ALIGN',      (0,1), (0,-1),  'LEFT'),
            ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, self.COLOR_LIGHT_BG]),
            ('BOX',        (0,0), (-1,-1), 0.5, self.COLOR_BORDER),
            ('INNERGRID',  (0,0), (-1,-1), 0.3, self.COLOR_BORDER),
            ('TOPPADDING',    (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('FONTSIZE',   (0,0), (-1,-1), 8),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.5*cm))
        return story

    # ========== 薄弱环节 ==========
    def _build_weakness(self, data: dict) -> list:
        story = []
        s = self.styles
        fn = self.font_name
        fb = self.font_bold

        story.append(Paragraph("四、薄弱环节分析", s['section_title']))
        story.append(HRFlowable(width="100%", thickness=0.5,
                                color=self.COLOR_BORDER, spaceAfter=6))

        weaknesses = data.get('weaknesses') or {}
        weak_topics = weaknesses.get('weak_topics') or []
        frequent_errors = weaknesses.get('frequent_errors') or []

        if not weak_topics and not frequent_errors:
            story.append(Paragraph("暂未发现明显薄弱环节，继续保持！", s['body']))
            story.append(Spacer(1, 0.3*cm))
            return story

        if weak_topics:
            story.append(Paragraph("薄弱知识点", s['subsection_title']))
            rows = [[
                Paragraph('知识点', s['body']),
                Paragraph('正确率', s['body']),
                Paragraph('练习次数', s['body']),
            ]]
            for item in weak_topics[:8]:
                rows.append([
                    Paragraph(self._safe(str(item.get('topic', ''))), s['body']),
                    Paragraph(f"{item.get('accuracy', 0)}%", s['tag_high']),
                    Paragraph(str(item.get('total', 0)), s['body']),
                ])
            t = Table(rows, colWidths=[9*cm, 3.5*cm, 3*cm])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), self.COLOR_DANGER),
                ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
                ('FONTNAME',   (0,0), (-1,0), fb),
                ('ALIGN',      (0,0), (-1,-1), 'CENTER'),
                ('ALIGN',      (0,1), (0,-1),  'LEFT'),
                ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, self.COLOR_LIGHT_BG]),
                ('BOX',        (0,0), (-1,-1), 0.5, self.COLOR_BORDER),
                ('INNERGRID',  (0,0), (-1,-1), 0.3, self.COLOR_BORDER),
                ('TOPPADDING',    (0,0), (-1,-1), 4),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                ('FONTSIZE',   (0,0), (-1,-1), 8),
            ]))
            story.append(t)
            story.append(Spacer(1, 0.3*cm))

        if frequent_errors:
            story.append(Paragraph("高频错误模式", s['subsection_title']))
            rows = [[
                Paragraph('错误类型', s['body']),
                Paragraph('描述', s['body']),
                Paragraph('出现次数', s['body']),
            ]]
            type_map = {'syntax': '语法错误', 'logic': '逻辑错误', 'concept': '概念错误'}
            for item in frequent_errors[:5]:
                rows.append([
                    Paragraph(type_map.get(item.get('error_type', ''), '其他'), s['body']),
                    Paragraph(self._safe(str(item.get('description', '')))[:40], s['small']),
                    Paragraph(str(item.get('count', 0)), s['body']),
                ])
            t = Table(rows, colWidths=[3*cm, 10*cm, 2.5*cm])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), self.COLOR_WARNING),
                ('FONTNAME',   (0,0), (-1,0), fb),
                ('ALIGN',      (0,0), (-1,-1), 'CENTER'),
                ('ALIGN',      (1,1), (1,-1),  'LEFT'),
                ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, self.COLOR_LIGHT_BG]),
                ('BOX',        (0,0), (-1,-1), 0.5, self.COLOR_BORDER),
                ('INNERGRID',  (0,0), (-1,-1), 0.3, self.COLOR_BORDER),
                ('TOPPADDING',    (0,0), (-1,-1), 4),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                ('FONTSIZE',   (0,0), (-1,-1), 8),
            ]))
            story.append(t)

        story.append(Spacer(1, 0.5*cm))
        return story

    # ========== 知识块引用热度 ==========
    def _build_chunk_heat(self, data: dict) -> list:
        story = []
        s = self.styles
        fn = self.font_name
        fb = self.font_bold

        story.append(Paragraph("五、知识块引用热度", s['section_title']))
        story.append(HRFlowable(width="100%", thickness=0.5,
                                color=self.COLOR_BORDER, spaceAfter=6))

        chunk_stats = data.get('knowledge_chunk_stats') or {}
        items = chunk_stats.get('items') or chunk_stats.get('chunks') or []
        total_retrieved = chunk_stats.get('total_retrieved') or chunk_stats.get('total_refs') or 0
        total_chunks    = chunk_stats.get('total_chunks') or len(items)

        if not items:
            story.append(Paragraph("暂无知识块引用数据", s['body']))
            story.append(Spacer(1, 0.3*cm))
            return story

        # 汇总卡片
        summary_data = [
            [Paragraph(str(total_retrieved), s['card_value']),
             Paragraph(str(total_chunks),    s['card_value'])],
            [Paragraph('总引用次数',          s['card_label']),
             Paragraph('上榜知识块数',        s['card_label'])],
        ]
        summary_table = Table(summary_data, colWidths=[8*cm, 8*cm])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), self.COLOR_LIGHT_BG),
            ('BOX',        (0,0), (-1,-1), 0.5, self.COLOR_BORDER),
            ('INNERGRID',  (0,0), (-1,-1), 0.3, self.COLOR_BORDER),
            ('ALIGN',      (0,0), (-1,-1), 'CENTER'),
            ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING',    (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.3*cm))

        # 排行表
        story.append(Paragraph("引用排行 Top 10", s['subsection_title']))
        rows = [[
            Paragraph('排名', s['body']),
            Paragraph('来源', s['body']),
            Paragraph('章节', s['body']),
            Paragraph('引用次数', s['body']),
        ]]
        rank_labels = {0: '第1', 1: '第2', 2: '第3'}
        for i, item in enumerate(items[:10], 0):
            rank_text = rank_labels.get(i, str(i+1))
            rows.append([
                Paragraph(rank_text, s['body']),
                Paragraph(self._safe(str(item.get('source', '')))[:20], s['small']),
                Paragraph(self._safe(str(item.get('chapter', '')))[:30], s['body']),
                Paragraph(str(item.get('retrieved_count', 0)), s['body']),
            ])

        t = Table(rows, colWidths=[2*cm, 4*cm, 9*cm, 2.5*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), self.COLOR_PRIMARY),
            ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
            ('FONTNAME',   (0,0), (-1,0), fb),
            ('FONTSIZE',   (0,0), (-1,-1), 8),
            ('ALIGN',      (0,0), (-1,-1), 'CENTER'),
            ('ALIGN',      (2,1), (2,-1),  'LEFT'),
            ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, self.COLOR_LIGHT_BG]),
            ('BOX',        (0,0), (-1,-1), 0.5, self.COLOR_BORDER),
            ('INNERGRID',  (0,0), (-1,-1), 0.3, self.COLOR_BORDER),
            ('TOPPADDING',    (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.5*cm))
        return story

    # ========== 学习建议 ==========
    def _build_recommendations(self, data: dict) -> list:
        story = []
        s = self.styles
        fn = self.font_name
        fb = self.font_bold

        story.append(Paragraph("六、个性化学习建议", s['section_title']))
        story.append(HRFlowable(width="100%", thickness=0.5,
                                color=self.COLOR_BORDER, spaceAfter=6))

        recommendations = data.get('recommendations') or []
        if not recommendations:
            story.append(Paragraph("继续保持良好的学习状态！", s['body']))
            story.append(Spacer(1, 0.3*cm))
            return story

        priority_label = {'high': '[重点]', 'medium': '[建议]', 'low': '[保持]'}
        priority_color = {
            'high':   self.COLOR_DANGER,
            'medium': self.COLOR_WARNING,
            'low':    self.COLOR_SUCCESS,
        }

        for rec in recommendations:
            priority = rec.get('priority', 'low')
            label    = priority_label.get(priority, '[提示]')
            color    = priority_color.get(priority, self.COLOR_MUTED)
            title    = self._safe(str(rec.get('title', '')))
            content  = self._safe(str(rec.get('content', '')))

            rec_table = Table([[
                Paragraph(f"<b>{label} {title}</b>",
                          ParagraphStyle('rec_title', fontName=fb, fontSize=9,
                                         textColor=color)),
                Paragraph(content,
                          ParagraphStyle('rec_body', fontName=fn, fontSize=8,
                                         textColor=self.COLOR_TEXT, leading=12)),
            ]], colWidths=[4*cm, 12.5*cm])
            rec_table.setStyle(TableStyle([
                ('VALIGN',    (0,0), (-1,-1), 'TOP'),
                ('TOPPADDING',    (0,0), (-1,-1), 4),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                ('LEFTPADDING',   (0,0), (-1,-1), 6),
                ('BOX',       (0,0), (-1,-1), 0.3, self.COLOR_BORDER),
                ('BACKGROUND',(0,0), (-1,-1), self.COLOR_LIGHT_BG),
            ]))
            story.append(rec_table)
            story.append(Spacer(1, 0.2*cm))

        story.append(Spacer(1, 0.3*cm))
        return story

    # ========== 页脚 ==========
    def _build_footer(self, data: dict) -> list:
        story = []
        s = self.styles
        fn = self.font_name

        story.append(HRFlowable(width="100%", thickness=0.5,
                                color=self.COLOR_BORDER, spaceAfter=6))

        generated_at = data.get('generated_at', '')
        if generated_at:
            try:
                dt = datetime.fromisoformat(generated_at.replace('Z', '+00:00'))
                generated_at = dt.strftime('%Y年%m月%d日 %H:%M')
            except Exception:
                pass

        story.append(Paragraph(
            f"报告生成时间：{generated_at}    |    计算思维课程助手系统",
            ParagraphStyle('footer', fontName=fn, fontSize=8,
                           textColor=self.COLOR_MUTED, alignment=TA_CENTER)
        ))
        return story