import streamlit as st
import pandas as pd
import math
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import svgwrite

# -----------------------------
# 核心排版與繪圖函式
# -----------------------------
def compute_positions(cols, rows, cross):
    """
    計算每張桌的中心 (col_idx, row_idx)
    cross=True 時執行交錯排列
    回傳 list of (no, col_idx, row_idx)
    """
    positions = []
    for y in range(1, rows+1):
        for x in range(1, cols+1):
            no = (y-1)*cols + (x-1)
            col_idx = x-1
            if cross:
                row_idx = (2*y-2) if x%2==0 else (2*y-1)
            else:
                row_idx = y-1
            positions.append((no, col_idx, row_idx))
    return positions


def render_svg(df, positions, cols, rows, cross, table_col, title, title_size):
    # SVG 畫布尺寸
    cell = 200
    hs = 20; vs = 20
    width = cols*cell + hs*(cols+1)
    height = (rows*(2 if cross else 1))*cell + vs*((rows*(2 if cross else 1))+1)
    dwg = svgwrite.Drawing(size=(width, height))
    # 顏色列表
    colors = ['#FFD1DC','#FFB347','#B19CD9','#77DD77','#AEC6CF','#FF6961','#CFCFC4']
    color_idx = -1; prev = None
    seats = 10
    for no, col_i, row_i in positions:
        cx = hs + col_i*(cell+hs) + cell/2
        cy = vs + row_i*(cell+vs) + cell/2
        rad = cell*0.4
        # 桌名
        idx0 = no*seats
        name = ''
        if idx0 < len(df):
            name = str(df.iloc[idx0][table_col])
            if name != prev:
                color_idx = (color_idx + 1) % len(colors)
            prev = name
        fill = colors[color_idx] if name else 'white'
        # 畫桌
        dwg.add(dwg.circle(center=(cx, cy), r=rad, stroke='black', fill=fill, stroke_width=2))
        if name:
            dwg.add(dwg.text(name, insert=(cx, cy), text_anchor="middle", alignment_baseline="middle", font_size=title_size))
        # 座位
        for i in range(seats):
            ang = 2*math.pi*i/seats
            x = cx + rad*math.cos(ang)
            y = cy + rad*math.sin(ang)
            dwg.add(dwg.circle(center=(x,y), r=6, stroke='black', fill='lightblue'))
    return dwg.tostring()

# -----------------------------
# Streamlit App
# -----------------------------

st.title("DF 通用桌次/座位圖產生器")

uploaded = st.file_uploader("上傳 Excel/CSV 檔", type=["xlsx","csv"])
cols = st.number_input("列數", min_value=1, max_value=50, value=6)
rows = st.number_input("行數", min_value=1, max_value=50, value=5)
cross = st.checkbox("交錯排列", value=False)
table_col = st.text_input("桌名欄位 (欄位名稱)", value="姓名")

if uploaded:
    if uploaded.name.endswith(('xlsx','xls')):
        df = pd.read_excel(uploaded)
    else:
        df = pd.read_csv(uploaded)
    st.write("預覽資料:", df.head())

    positions = compute_positions(cols, rows, cross)
    svg = render_svg(df, positions, cols, rows, cross, table_col, title=None, title_size=14)
    st.subheader("SVG 預覽")
    st.components.v1.html(svg, height=rows*200+100)   

    st.download_button("下載 SVG", data=svg, file_name="table_layout.svg", mime="image/svg+xml")
