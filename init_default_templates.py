import sqlite3
import json
from datetime import datetime

conn = sqlite3.connect(r'E:\Project\Print_tool\temple-management\database\temple.db')
cursor = conn.cursor()

default_templates = [
    {
        '模板名称': '延生大牌模板',
        '模板类型': '延生牌位',
        '牌位类型': '大牌',
        '布局配置': json.dumps({
            'layout': {
                'pageWidth': 210, 'pageHeight': 380,
                'fontFamily': 'STXingkai',
                'nameFontSize': 52, 'nameSpacing': 20,
                'namesTopPct': 25, 'namesLeftPct': 10,
                'namesWidthPct': 80, 'namesHeightPct': 55,
                'yangshangFontSize': 18, 'yangshangSpacing': 5,
                'seatFontSize': 24, 'bottomTopPct': 90, 'bottomLeftPct': 50
            },
            'content': {'namesTitle': '佛光注照'},
            'displayItems': ['names', 'seat', 'fahui_name']
        }),
        '是否启用': 1, '是否默认': 1,
        '备注': '延生大牌位打印模板，姓名竖排，华文行楷'
    },
    {
        '模板名称': '延生中牌模板',
        '模板类型': '延生牌位',
        '牌位类型': '中牌',
        '布局配置': json.dumps({
            'layout': {
                'pageWidth': 148, 'pageHeight': 280,
                'fontFamily': 'STXingkai',
                'nameFontSize': 40, 'nameSpacing': 16,
                'namesTopPct': 25, 'namesLeftPct': 10,
                'namesWidthPct': 80, 'namesHeightPct': 55,
                'yangshangFontSize': 18, 'yangshangSpacing': 5,
                'seatFontSize': 20, 'bottomTopPct': 90, 'bottomLeftPct': 50
            },
            'content': {'namesTitle': '佛光注照'},
            'displayItems': ['names', 'seat', 'fahui_name']
        }),
        '是否启用': 1, '是否默认': 1,
        '备注': '延生中牌位打印模板，姓名竖排，华文行楷'
    },
    {
        '模板名称': '延生小牌模板',
        '模板类型': '延生牌位',
        '牌位类型': '小牌',
        '布局配置': json.dumps({
            'layout': {
                'pageWidth': 130, 'pageHeight': 240,
                'fontFamily': 'STXingkai',
                'nameFontSize': 30, 'nameSpacing': 12,
                'namesTopPct': 25, 'namesLeftPct': 10,
                'namesWidthPct': 80, 'namesHeightPct': 55,
                'yangshangFontSize': 16, 'yangshangSpacing': 4,
                'seatFontSize': 18, 'bottomTopPct': 90, 'bottomLeftPct': 50
            },
            'content': {'namesTitle': '佛光注照'},
            'displayItems': ['names']
        }),
        '是否启用': 1, '是否默认': 1,
        '备注': '延生小牌位打印模板，姓名竖排，华文行楷'
    },
    {
        '模板名称': '往生大牌模板',
        '模板类型': '往生牌位',
        '牌位类型': '大牌',
        '布局配置': json.dumps({
            'layout': {
                'pageWidth': 210, 'pageHeight': 380,
                'fontFamily': 'STXingkai',
                'nameFontSize': 40, 'nameSpacing': 20,
                'namesTopPct': 25, 'namesLeftPct': 10,
                'namesWidthPct': 80, 'namesHeightPct': 55,
                'yangshangFontSize': 18, 'yangshangSpacing': 5,
                'seatFontSize': 24, 'bottomTopPct': 90, 'bottomLeftPct': 50
            },
            'content': {'namesTitle': '佛光接引'},
            'displayItems': ['names', 'yangshang', 'seat', 'fahui_name']
        }),
        '是否启用': 1, '是否默认': 1,
        '备注': '往生大牌位打印模板，接引姓名竖排+阳上竖排，华文行楷'
    },
    {
        '模板名称': '往生中牌模板',
        '模板类型': '往生牌位',
        '牌位类型': '中牌',
        '布局配置': json.dumps({
            'layout': {
                'pageWidth': 148, 'pageHeight': 280,
                'fontFamily': 'STXingkai',
                'nameFontSize': 32, 'nameSpacing': 16,
                'namesTopPct': 25, 'namesLeftPct': 10,
                'namesWidthPct': 80, 'namesHeightPct': 55,
                'yangshangFontSize': 16, 'yangshangSpacing': 4,
                'seatFontSize': 20, 'bottomTopPct': 90, 'bottomLeftPct': 50
            },
            'content': {'namesTitle': '佛光接引'},
            'displayItems': ['names', 'yangshang', 'seat', 'fahui_name']
        }),
        '是否启用': 1, '是否默认': 1,
        '备注': '往生中牌位打印模板，接引姓名竖排+阳上竖排，华文行楷'
    },
    {
        '模板名称': '佛事牌子模板',
        '模板类型': '佛事牌子',
        '牌位类型': '',
        '布局配置': json.dumps({
            'layout': {
                'pageWidth': 100, 'pageHeight': 200,
                'fontFamily': 'STXingkai',
                'nameFontSize': 36, 'nameSpacing': 15,
                'namesTopPct': 25, 'namesLeftPct': 10,
                'namesWidthPct': 80, 'namesHeightPct': 55,
                'yangshangFontSize': 14, 'yangshangSpacing': 3,
                'seatFontSize': 16, 'bottomTopPct': 90, 'bottomLeftPct': 50
            },
            'content': {'namesTitle': '佛力超度'},
            'displayItems': ['names', 'yangshang']
        }),
        '是否启用': 1, '是否默认': 1,
        '备注': '佛事牌子打印模板，姓名竖排，华文行楷'
    }
]

for template in default_templates:
    cursor.execute(
        "SELECT id FROM printer_templates WHERE 模板名称 = ?",
        (template['模板名称'],)
    )
    existing = cursor.fetchone()
    if existing:
        cursor.execute(
            """UPDATE printer_templates SET 布局配置 = ?, 备注 = ? WHERE 模板名称 = ?""",
            (template['布局配置'], template['备注'], template['模板名称'])
        )
    else:
        cursor.execute(
            """INSERT INTO printer_templates (模板名称, 模板类型, 牌位类型, 布局配置, 是否启用, 是否默认, 备注)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (template['模板名称'], template['模板类型'], template['牌位类型'],
             template['布局配置'], template['是否启用'], template['是否默认'], template['备注'])
        )

conn.commit()
conn.close()
print("默认模板初始化完成")