# -*- coding: utf-8 -*-
"""
PDF 学情报告生成器（使用 reportlab）
"""
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import os


# ========== 注册中文字体 ==========
def _register_fonts():
    """注册中文字体"""
    # Windows 系统字体路径
    font_paths = [
        "C:/Windows/Fonts/simhei.ttf",       # 黑体
        "C:/Windows/Fonts/simsun.ttc",        # 宋体
        "C:/Windows/Fonts/msyh.ttc",          # 微软雅黑
        "C:/Windows/Fonts/msyhbd.ttc",        # 微软雅黑粗体
    ]

    registered = False
    for path in font_paths:
        if os.path.exists(path):
            try:
                if "msyh.ttc" in path and not registered:
                    pdfmetrics.registerFont(TTFont("MSYaHei", path))
                    registered = True
                elif "msyhbd.ttc" in path:
                    pdfmetrics.registerFont(TTFont("MSYaHei-Bold", path))
                elif "simhei.ttf" in path and not registered:
                    pdfmetrics.registerFont(TTFont("SimHei", path))
                    registered = True
            except Exception as e:
                print(f"⚠️ 字体注册失败 {path}: {e}")

    return "MSYaHei" if registered and "MSYaHei" in pdfmetrics.getRegisteredFontNames() else (
        "SimHei" if "SimHei" in pdfmetrics.getRegisteredFontNames() else "Helvetica"
    )


class PDFReportGenerator:
    """PDF 学情报告生成器"""

    # 主题颜色
    COLOR_PRIMARY = colors.HexColor("#667eea")
    COLOR_SECONDARY = colors.HexColor("#764ba2")
    COLOR_SUCCESS = colors.HexColor("#28a745")
    COLOR_WARNING = colors.HexColor("#ffc107")
    COLOR_DANGER = colors.HexColor("#dc3545")
    COLOR_LIGHT_BG = colors.HexColor("#f5f7fa")
    COLOR_BORDER = colors.HexColor("#e0e0e0")
    COLOR_TEXT = colors.HexColor("#333333")
    COLOR_MUTED = colors.HexColor("#666666")

    def __init__(self):
        self.font_name = _register_fonts()
        self.font_bold = (
            "MSYaHei-Bold" if "MSYaHei-Bold" in pdfmetrics.getRegisteredFontNames()
            else self.font_name
        )
        self._init_styles()

    def _init_styles(self):
        """初始化段落样式"""
        fn = self.font_name
        fb = self.font_bold

        self.styles = {
            # ⭐ 封面标题：28->14
            'title': ParagraphStyle('title', fontName=fb, fontSize=14,
                                    textColor=self.COLOR_PRIMARY, alignment=TA_CENTER, spaceAfter=4),
            # ⭐ 副标题：14->10
            'subtitle': ParagraphStyle('subtitle', fontName=fn, fontSize=10,
                                       textColor=self.COLOR_MUTED, alignment=TA_CENTER, spaceAfter=4),
            # ⭐ 元信息：11->9
            'meta': ParagraphStyle('meta', fontName=fn, fontSize=9,
                                   textColor=self.COLOR_MUTED, alignment=TA_CENTER, spaceAfter=3),
            # ⭐ 章节标题
            'h1': ParagraphStyle('h1', fontName=fb, fontSize=12,
                                 textColor=self.COLOR_PRIMARY, spaceBefore=10, spaceAfter=5),
            'h2': ParagraphStyle('h2', fontName=fb, fontSize=10,
                                 textColor=self.COLOR_TEXT, spaceBefore=6, spaceAfter=3),
            'section_title': ParagraphStyle('section_title', fontName=fb, fontSize=12,
                                            textColor=self.COLOR_PRIMARY, spaceBefore=10, spaceAfter=5),
            'subsection_title': ParagraphStyle('subsection_title', fontName=fb, fontSize=10,
                                               textColor=self.COLOR_TEXT, spaceBefore=6, spaceAfter=3),
            # ⭐ 正文
            'body': ParagraphStyle('body', fontName=fn, fontSize=9,
                                   textColor=self.COLOR_TEXT, spaceAfter=3, leading=13),
            'small': ParagraphStyle('small', fontName=fn, fontSize=8,
                                    textColor=self.COLOR_MUTED, spaceAfter=2),
            # ⭐ 卡片数值：原来太大，改小
            'card_value': ParagraphStyle('card_value', fontName=fb, fontSize=13,
                                         textColor=self.COLOR_PRIMARY, alignment=TA_CENTER),
            'card_label': ParagraphStyle('card_label', fontName=fn, fontSize=8,
                                          textColor=self.COLOR_MUTED, alignment=TA_CENTER),
            'tag_high': ParagraphStyle('tag_high', fontName=fn, fontSize=8,
                                       textColor=colors.HexColor("#721c24")),
            'tag_medium': ParagraphStyle('tag_medium', fontName=fn, fontSize=8,
                                         textColor=colors.HexColor("#856404")),
            'tag_low': ParagraphStyle('tag_low', fontName=fn, fontSize=8,
                                      textColor=colors.HexColor("#155724")),
        }

    def generate(self, report_data: dict) -> bytes:
        """
        生成 PDF 并返回字节内容

        Args:
            report_data: 报告数据字典（与 /api/analytics/report 返回格式一致）

        Returns:
            bytes: PDF 文件内容
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
            title="学情分析报告",
            author="计算思维课程助手系统",
        )

        story = []

        # ========== 1. 封面 ==========
        story += self._build_cover(report_data)

        # ========== 2. 概览数据 ==========
        story += self._build_overview(report_data)

        # ========== 3. 综合评分 ==========
        story += self._build_score(report_data)

        # ========== 4. 知识点掌握 ==========
        story += self._build_knowledge(report_data)

        # ========== 5. 薄弱环节 ==========
        story += self._build_weakness(report_data)

        # ========== 6. 学习建议 ==========
        story += self._build_recommendations(report_data)

        # ========== 7. 页脚 ==========
        story += self._build_footer(report_data)

        doc.build(story)
        return buffer.getvalue()

    # ========== 封面 ==========
    def _build_cover(self, data: dict) -> list:
        """封面"""
        story = []
        fn = self.font_name
        fb = self.font_bold

        story.append(Spacer(1, 1.0 * cm))

        # ⭐ emoji 单独一行，字号缩小
        story.append(Paragraph("📊", ParagraphStyle(
            'cover_icon', fontName=fn, fontSize=16, alignment=TA_CENTER, spaceAfter=2)))

        story.append(Paragraph("学情分析报告", ParagraphStyle(
            'cover_title', fontName=fb, fontSize=14,
            textColor=self.COLOR_PRIMARY, alignment=TA_CENTER, spaceAfter=4)))

        story.append(Paragraph("计算思维课程助手系统", ParagraphStyle(
            'cover_subtitle', fontName=fn, fontSize=10,
            textColor=self.COLOR_MUTED, alignment=TA_CENTER, spaceAfter=6)))

        story.append(Spacer(1, 0.3 * cm))
        story.append(HRFlowable(width="80%", thickness=1, color=self.COLOR_PRIMARY))
        story.append(Spacer(1, 0.4 * cm))

        # 学生信息
        user_info = data.get('user_info') or {}
        username = (
            user_info.get('nickname') or
            user_info.get('username') or
            user_info.get('name') or
            '未知学生'
        )
        period_days = data.get('period_days', 30)
        generated_at = data.get('generated_at', '')
        if generated_at:
            try:
                dt = datetime.fromisoformat(generated_at.replace('Z', '+00:00'))
                generated_at = dt.strftime('%Y年%m月%d日 %H:%M')
            except Exception:
                pass

        meta_style = ParagraphStyle('meta2', fontName=fn, fontSize=9,
                                    textColor=self.COLOR_MUTED, alignment=TA_CENTER, spaceAfter=3)
        for line in [
            f"学生：{username}",
            f"统计周期：最近 {period_days} 天",
            f"生成时间：{generated_at}",
        ]:
            story.append(Paragraph(line, meta_style))

        # 综合评分卡
        score = data.get('score')
        if score:
            story.append(Spacer(1, 0.6 * cm))
            score_table = Table(
                [[
                    Paragraph(f"<b>{round(score.get('total', 0))}</b>", ParagraphStyle(
                        'snum', fontName=fb, fontSize=22,   # ⭐ 原36->22
                        textColor=self.COLOR_PRIMARY, alignment=TA_CENTER)),
                    Paragraph(f"<b>{score.get('grade', '-')}</b>", ParagraphStyle(
                        'sgrade', fontName=fb, fontSize=16,  # ⭐ 原22->16
                        textColor=self.COLOR_SECONDARY, alignment=TA_CENTER)),
                    Paragraph(score.get('grade_text', ''), ParagraphStyle(
                        'stext', fontName=fn, fontSize=10,   # ⭐ 原14->10
                        textColor=self.COLOR_MUTED, alignment=TA_CENTER)),
                ]],
                colWidths=[4 * cm, 3.5 * cm, 6 * cm]
            )
            score_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BACKGROUND', (0, 0), (-1, -1), self.COLOR_LIGHT_BG),
                ('BOX', (0, 0), (-1, -1), 0.5, self.COLOR_BORDER),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(score_table)

        story.append(Spacer(1, 0.8 * cm))
        return story

    # ========== 概览数据 ==========
    def _build_overview(self, data: dict) -> list:
        """学习概览章节"""
        overview = data.get('overview', {})
        story = []
        fn = self.font_name
        fb = self.font_bold

        # ⭐ 使用正确的样式键 'h1'，也可用 'section_title'（两者现在都存在）
        story.append(Paragraph("一、学习概览", self.styles['section_title']))
        story.append(HRFlowable(width="100%", thickness=0.5, color=self.COLOR_BORDER))
        story.append(Spacer(1, 0.3 * cm))

        # 概览数据卡片
        cards = [
            ("📚", f"{overview.get('total_duration_hours', 0):.1f}", "学习时长(h)"),
            ("💬", str(overview.get('question_count', 0)), "提问次数"),
            ("💻", str(overview.get('code_count', 0)), "代码提交"),
            ("✅", f"{overview.get('accuracy', 0)}%", "代码正确率"),
            ("📅", str(overview.get('active_days', 0)), "活跃天数"),
            ("👁️", str(overview.get('view_count', 0)), "知识点查看"),
        ]

        card_data = [[
            Table(
                [[Paragraph(icon, ParagraphStyle('icon', fontName=fn, fontSize=18, alignment=TA_CENTER))],
                 [Paragraph(value, self.styles['card_value'])],
                 [Paragraph(label, self.styles['card_label'])]],
                colWidths=[2.5 * cm]
            )
            for icon, value, label in cards
        ]]

        overview_table = Table(card_data, colWidths=[2.5 * cm] * 6)
        overview_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, 0), (-1, -1), self.COLOR_LIGHT_BG),
            ('BOX', (0, 0), (-1, -1), 0.5, self.COLOR_BORDER),
            ('INNERGRID', (0, 0), (-1, -1), 0.3, self.COLOR_BORDER),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(overview_table)
        story.append(Spacer(1, 0.4 * cm))
        return story

    # ========== 综合评分 ==========
    def _build_score(self, data: dict) -> list:
        """综合评分章节"""
        score = data.get('score')
        if not score:
            return []

        story = []
        fn = self.font_name
        fb = self.font_bold

        story.append(Paragraph("二、综合评分", self.styles['h1']))
        story.append(HRFlowable(width="100%", thickness=0.5, color=self.COLOR_BORDER))
        story.append(Spacer(1, 0.3 * cm))

        breakdown = score.get('breakdown', {})
        label_map = {'time': '学习时长', 'activity': '活跃程度', 'code': '代码质量', 'knowledge': '学习广度'}
        max_map = {'time': 25, 'activity': 25, 'code': 30, 'knowledge': 20}

        # ⭐ 表头字体缩小
        table_data = [[
            Paragraph('<b>评分项</b>', ParagraphStyle('th', fontName=fb, fontSize=9,    # ⭐ 原11
                                                      textColor=colors.white, alignment=TA_CENTER)),
            Paragraph('<b>得分</b>', ParagraphStyle('th', fontName=fb, fontSize=9,
                                                    textColor=colors.white, alignment=TA_CENTER)),
            Paragraph('<b>满分</b>', ParagraphStyle('th', fontName=fb, fontSize=9,
                                                    textColor=colors.white, alignment=TA_CENTER)),
            Paragraph('<b>完成度</b>', ParagraphStyle('th', fontName=fb, fontSize=9,
                                                      textColor=colors.white, alignment=TA_CENTER)),
        ]]

        for key, label in label_map.items():
            val = breakdown.get(key, 0)
            mx = max_map.get(key, 25)
            pct = f"{int(val / mx * 100)}%"
            table_data.append([
                Paragraph(label, ParagraphStyle('td', fontName=fn, fontSize=9,    # ⭐ 原10
                                                textColor=self.COLOR_TEXT)),
                Paragraph(str(val), ParagraphStyle('td', fontName=fn, fontSize=9,
                                                   textColor=self.COLOR_PRIMARY, alignment=TA_CENTER)),
                Paragraph(str(mx), ParagraphStyle('td', fontName=fn, fontSize=9,
                                                   textColor=self.COLOR_MUTED, alignment=TA_CENTER)),
                Paragraph(pct, ParagraphStyle('td', fontName=fn, fontSize=9,
                                              textColor=self.COLOR_TEXT, alignment=TA_CENTER)),
            ])

        score_table = Table(table_data, colWidths=[4 * cm, 3 * cm, 3 * cm, 4 * cm])
        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.COLOR_PRIMARY),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.COLOR_LIGHT_BG]),
            ('GRID', (0, 0), (-1, -1), 0.3, self.COLOR_BORDER),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),     # ⭐ 减少行高
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(score_table)
        story.append(Spacer(1, 0.3 * cm))
        return story

    # ========== 知识点掌握 ==========
    def _build_knowledge(self, data: dict) -> list:
        elements = []
        s = self.styles
        knowledge = data.get("knowledge_mastery", [])

        elements.append(Paragraph("三、知识点掌握情况", s["section_title"]))
        elements.append(HRFlowable(
            width="100%", thickness=1,
            color=self.COLOR_BORDER, spaceAfter=8
        ))

        if not knowledge:
            elements.append(Paragraph("暂无知识点学习记录", s["muted"]))
            return elements

        rows = [["知识点", "查看次数", "掌握度", "状态"]]
        for item in knowledge[:15]:
            mastery = item.get("mastery", 0) or 0
            if mastery >= 80:
                status = "已掌握"
            elif mastery >= 60:
                status = "基本掌握"
            else:
                status = "需加强"
            rows.append([
                item.get("topic", "—"),
                str(item.get("total_count", 0)),
                f"{mastery:.0f}%",
                status,
            ])

        table = Table(rows, colWidths=[7 * cm, 3 * cm, 3 * cm, 4 * cm])
        table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), self.font_name),
            ("FONTNAME", (0, 0), (-1, 0), self.font_bold),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BACKGROUND", (0, 0), (-1, 0), self.COLOR_PRIMARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ROWBACKGROUND", (0, 1), (-1, -1), [colors.white, self.COLOR_LIGHT_BG]),
            ("GRID", (0, 0), (-1, -1), 0.5, self.COLOR_BORDER),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 0.3 * cm))

        return elements

    # ========== 薄弱环节 ==========
    def _build_weakness(self, data: dict) -> list:
        elements = []
        s = self.styles
        weakness = data.get("weaknesses", {})

        if not weakness:
            return elements

        elements.append(Paragraph("四、薄弱环节分析", s["section_title"]))
        elements.append(HRFlowable(
            width="100%", thickness=1,
            color=self.COLOR_BORDER, spaceAfter=8
        ))

        # 薄弱知识点
        weak_topics = weakness.get("weak_topics", [])
        if weak_topics:
            elements.append(Paragraph("薄弱知识点（正确率 < 60%）：", s["subsection"]))
            rows = [["知识点", "正确率", "练习次数"]]
            for t in weak_topics[:8]:
                rows.append([
                    t.get("topic", "—"),
                    f"{t.get('accuracy', 0):.0f}%",
                    str(t.get("attempts", 0)),
                ])
            table = Table(rows, colWidths=[8 * cm, 4 * cm, 5 * cm])
            table.setStyle(TableStyle([
                ("FONTNAME", (0, 0), (-1, -1), self.font_name),
                ("FONTNAME", (0, 0), (-1, 0), self.font_bold),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BACKGROUND", (0, 0), (-1, 0), self.COLOR_DANGER),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ROWBACKGROUND", (0, 1), (-1, -1), [colors.white, self.COLOR_LIGHT_BG]),
                ("GRID", (0, 0), (-1, -1), 0.5, self.COLOR_BORDER),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            elements.append(table)
            elements.append(Spacer(1, 0.2 * cm))

        # 高频错误
        freq_errors = weakness.get("frequent_errors", [])
        if freq_errors:
            elements.append(Paragraph("高频错误模式：", s["subsection"]))
            rows = [["错误类型", "描述", "出现次数"]]
            type_map = {"syntax": "语法错误", "logic": "逻辑错误", "concept": "概念错误"}
            for e in freq_errors[:5]:
                rows.append([
                    type_map.get(e.get("error_type", ""), e.get("error_type", "—")),
                    e.get("description", "—")[:30],
                    str(e.get("occurrence_count", 0)),
                ])
            table = Table(rows, colWidths=[4 * cm, 10 * cm, 3 * cm])
            table.setStyle(TableStyle([
                ("FONTNAME", (0, 0), (-1, -1), self.font_name),
                ("FONTNAME", (0, 0), (-1, 0), self.font_bold),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BACKGROUND", (0, 0), (-1, 0), self.COLOR_WARNING),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ROWBACKGROUND", (0, 1), (-1, -1), [colors.white, self.COLOR_LIGHT_BG]),
                ("GRID", (0, 0), (-1, -1), 0.5, self.COLOR_BORDER),
                ("ALIGN", (2, 0), (2, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            elements.append(table)

        elements.append(Spacer(1, 0.3 * cm))
        return elements

    # ========== 学习建议 ==========
    def _build_recommendations(self, data: dict) -> list:
        elements = []
        s = self.styles
        recs = data.get("recommendations", [])

        elements.append(Paragraph("五、个性化学习建议", s["section_title"]))
        elements.append(HRFlowable(
            width="100%", thickness=1,
            color=self.COLOR_BORDER, spaceAfter=8
        ))

        if not recs:
            elements.append(Paragraph("暂无建议", s["muted"]))
            return elements

        priority_map = {
            "high":   ("🔴 重点关注", self.COLOR_DANGER),
            "medium": ("🟡 建议改进", self.COLOR_WARNING),
            "low":    ("🟢 持续保持", self.COLOR_SUCCESS),
        }

        for i, rec in enumerate(recs, 1):
            priority = rec.get("priority", "low")
            label, label_color = priority_map.get(priority, ("—", self.COLOR_MUTED))

            row = Table(
                [[
                    Paragraph(f"{i}. {label}", ParagraphStyle(
                        "RecLabel", fontName=self.font_bold,
                        fontSize=9, textColor=label_color
                    )),
                    Paragraph(rec.get("content", ""), s["body"]),
                ]],
                colWidths=[3 * cm, 14 * cm],
            )
            row.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("BACKGROUND", (0, 0), (-1, -1),
                 colors.HexColor("#fff9f9") if priority == "high" else
                 colors.HexColor("#fffbf0") if priority == "medium" else
                 colors.HexColor("#f0fff4")),
                ("LINEBELOW", (0, 0), (-1, -1), 0.5, self.COLOR_BORDER),
            ]))
            elements.append(row)

        elements.append(Spacer(1, 0.3 * cm))
        return elements

    # ========== 页脚 ==========
    def _build_footer(self, data: dict) -> list:
        elements = []
        elements.append(Spacer(1, 0.5 * cm))
        elements.append(HRFlowable(
            width="100%", thickness=1,
            color=self.COLOR_BORDER, spaceAfter=6
        ))
        elements.append(Paragraph(
            f"本报告由计算思维课程助手系统自动生成 · {datetime.now().strftime('%Y年%m月%d日')}",
            ParagraphStyle(
                "Footer", fontName=self.font_name,
                fontSize=8, textColor=self.COLOR_MUTED,
                alignment=TA_CENTER,
            )
        ))
        return elements