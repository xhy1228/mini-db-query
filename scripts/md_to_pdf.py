# -*- coding: utf-8 -*-
"""
Markdown 转 PDF 工具

使用 reportlab 将 Markdown 文档转换为 PDF
支持中文
"""

import os
import re
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.cidfonts import UnicodeCIDFont


def register_chinese_font():
    """注册中文字体"""
    try:
        # 尝试使用CID字体（支持中文）
        pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
        return 'STSong-Light'
    except:
        # 如果CID字体不可用，使用默认字体
        return 'Helvetica'


def create_styles(font_name):
    """创建样式"""
    styles = getSampleStyleSheet()
    
    # 标题样式
    styles.add(ParagraphStyle(
        name='ChineseTitle',
        fontName=font_name,
        fontSize=24,
        leading=30,
        alignment=TA_CENTER,
        spaceAfter=20,
        textColor=colors.HexColor('#1890ff')
    ))
    
    # H1 样式
    styles.add(ParagraphStyle(
        name='ChineseH1',
        fontName=font_name,
        fontSize=18,
        leading=24,
        spaceBefore=20,
        spaceAfter=10,
        textColor=colors.HexColor('#262626')
    ))
    
    # H2 样式
    styles.add(ParagraphStyle(
        name='ChineseH2',
        fontName=font_name,
        fontSize=14,
        leading=20,
        spaceBefore=15,
        spaceAfter=8,
        textColor=colors.HexColor('#262626')
    ))
    
    # H3 样式
    styles.add(ParagraphStyle(
        name='ChineseH3',
        fontName=font_name,
        fontSize=12,
        leading=16,
        spaceBefore=10,
        spaceAfter=5,
        textColor=colors.HexColor('#595959')
    ))
    
    # 正文样式
    styles.add(ParagraphStyle(
        name='ChineseBody',
        fontName=font_name,
        fontSize=10,
        leading=16,
        spaceBefore=3,
        spaceAfter=3,
        textColor=colors.HexColor('#262626')
    ))
    
    # 代码样式
    styles.add(ParagraphStyle(
        name='ChineseCode',
        fontName='Courier',
        fontSize=9,
        leading=12,
        spaceBefore=5,
        spaceAfter=5,
        leftIndent=20,
        backColor=colors.HexColor('#f5f5f5')
    ))
    
    # 列表样式
    styles.add(ParagraphStyle(
        name='ChineseList',
        fontName=font_name,
        fontSize=10,
        leading=14,
        leftIndent=20,
        spaceBefore=2,
        spaceAfter=2
    ))
    
    return styles


def parse_markdown(text):
    """解析 Markdown 文本"""
    lines = text.split('\n')
    elements = []
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # 空行
        if not line:
            i += 1
            continue
        
        # 标题
        if line.startswith('# '):
            elements.append(('h1', line[2:]))
        elif line.startswith('## '):
            elements.append(('h2', line[3:]))
        elif line.startswith('### '):
            elements.append(('h3', line[4:]))
        elif line.startswith('#### '):
            elements.append(('h3', line[5:]))
        
        # 分隔线
        elif line.startswith('---'):
            elements.append(('hr', ''))
        
        # 表格
        elif line.startswith('|') and '|' in line[1:]:
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                table_lines.append(lines[i].strip())
                i += 1
            i -= 1
            elements.append(('table', table_lines))
        
        # 代码块
        elif line.startswith('```'):
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code_lines.append(lines[i])
                i += 1
            elements.append(('code', '\n'.join(code_lines)))
        
        # 列表
        elif line.startswith('- ') or line.startswith('* '):
            elements.append(('list', line[2:]))
        elif re.match(r'^\d+\. ', line):
            elements.append(('list', re.sub(r'^\d+\. ', '', line)))
        
        # 普通段落
        else:
            # 处理粗体和斜体
            line = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', line)
            line = re.sub(r'\*(.+?)\*', r'<i>\1</i>', line)
            line = re.sub(r'`(.+?)`', r'<font face="Courier" size="9">\1</font>', line)
            elements.append(('p', line))
        
        i += 1
    
    return elements


def md_to_pdf(md_file, pdf_file, title=None):
    """将 Markdown 文件转换为 PDF"""
    # 读取 Markdown 文件
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # 创建 PDF
    doc = SimpleDocTemplate(
        pdf_file,
        pagesize=A4,
        leftMargin=2*cm,
        rightMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # 注册中文字体
    font_name = register_chinese_font()
    styles = create_styles(font_name)
    
    # 解析 Markdown
    elements = parse_markdown(md_content)
    
    # 构建 PDF 内容
    story = []
    
    # 添加标题
    if title:
        story.append(Paragraph(title, styles['ChineseTitle']))
        story.append(Spacer(1, 0.5*cm))
    
    for elem_type, content in elements:
        if elem_type == 'h1':
            story.append(Paragraph(content, styles['ChineseH1']))
            story.append(Spacer(1, 0.3*cm))
        elif elem_type == 'h2':
            story.append(Paragraph(content, styles['ChineseH2']))
        elif elem_type == 'h3':
            story.append(Paragraph(content, styles['ChineseH3']))
        elif elem_type == 'p':
            story.append(Paragraph(content, styles['ChineseBody']))
        elif elem_type == 'list':
            story.append(Paragraph(f'• {content}', styles['ChineseList']))
        elif elem_type == 'code':
            for code_line in content.split('\n'):
                story.append(Paragraph(code_line, styles['ChineseCode']))
        elif elem_type == 'hr':
            story.append(Spacer(1, 0.3*cm))
        elif elem_type == 'table':
            # 简单表格处理
            table_data = []
            for tline in content:
                cells = [c.strip() for c in tline.split('|')[1:-1]]
                if cells and not all(c.startswith('-') for c in cells):
                    table_data.append(cells)
            
            if table_data:
                try:
                    t = Table(table_data)
                    t.setStyle(TableStyle([
                        ('FONTNAME', (0, 0), (-1, -1), font_name),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f0f0f0')),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('LEFTPADDING', (0, 0), (-1, -1), 5),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                    ]))
                    story.append(t)
                    story.append(Spacer(1, 0.3*cm))
                except:
                    pass
    
    # 生成 PDF
    doc.build(story)
    print(f"✅ 已生成: {pdf_file}")


def convert_all_docs(docs_dir, output_dir):
    """转换所有文档"""
    os.makedirs(output_dir, exist_ok=True)
    
    docs = {
        'README.md': '项目说明',
        'DEPLOY.md': '部署说明',
        'DEPLOYMENT.md': '部署指南',
        'ADMIN_GUIDE.md': '管理平台使用说明',
        'MINIAPP_GUIDE.md': '微信小程序使用说明',
        'VERSION_HISTORY.md': '版本更新记录',
        'PROJECT_STATUS.md': '项目状态报告'
    }
    
    for md_file, title in docs.items():
        md_path = os.path.join(docs_dir, md_file)
        if os.path.exists(md_path):
            pdf_file = md_file.replace('.md', '.pdf')
            pdf_path = os.path.join(output_dir, pdf_file)
            try:
                md_to_pdf(md_path, pdf_path, title)
            except Exception as e:
                print(f"❌ 转换失败 {md_file}: {e}")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 2:
        md_file = sys.argv[1]
        pdf_file = sys.argv[2]
        title = sys.argv[3] if len(sys.argv) > 3 else None
        md_to_pdf(md_file, pdf_file, title)
    else:
        # 默认转换所有文档
        docs_dir = '/root/projects/mini-db-query/docs'
        output_dir = '/root/projects/mini-db-query/docs/pdf'
        convert_all_docs(docs_dir, output_dir)
