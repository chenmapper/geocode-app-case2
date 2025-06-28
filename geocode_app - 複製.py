import streamlit as st
import pandas as pd
import geocoder
import geopandas as gpd
import io
from shapely.geometry import Point

st.title("批次地址 Geocode 與 行政區註記工具")

# 上傳 DataFrame 檔案
uploaded = st.file_uploader("上傳 Excel 或 CSV 檔案", type=["xlsx","xls","csv"])
if uploaded:
    # 讀取 DataFrame
    if uploaded.name.lower().endswith((".xlsx",".xls")):
        df = pd.read_excel(uploaded)
    else:
        df = pd.read_csv(uploaded)

    # 選擇地址欄位，預設為 "地址" 或第一欄
    cols = df.columns.tolist()
    default = cols.index("地址") if "地址" in cols else 0
    addr_col = st.selectbox("選擇地址欄位", options=cols, index=default)

        # 設定最多處理筆數，若上傳量多於1000則上限為1000，否則為資料長度
    limit = min(len(df), 1000)
    max_n = st.number_input("最多處理筆數 (最多上限1000筆)", min_value=1, max_value=limit, value=limit)

    if st.button("開始執行"):  # 執行按鈕("開始執行"):  # 執行按鈕
        df["gx"] = pd.NA
        df["gy"] = pd.NA
        seen = set()
        # 限制次數
        for i, addr in enumerate(df[addr_col].fillna("")[:max_n]):
            if not addr or addr in seen:
                continue
            seen.add(addr)
            # 使用 ArcGIS 進行 geocode 並加上 Taiwan
            g = geocoder.arcgis(f"{addr}, Taiwan")
            if g.ok and g.latlng:
                df.at[i, "gx"] = g.lng
                df.at[i, "gy"] = g.lat
            else:
                df.at[i, "gx"] = pd.NA
                df.at[i, "gy"] = pd.NA

        # 讀取台灣村里 Shapefile
        shp_path = "VILLAGE_NLSC_1140318.shp"
        gdf = gpd.read_file(shp_path).to_crs(epsg=4326)
        # 動態找欄位
        county_field = next(c for c in gdf.columns if "county" in c.lower())
        town_field = next(c for c in gdf.columns if "town" in c.lower())
        vill_field = next((c for c in gdf.columns if "villname" in c.lower()), None)

        # 數值化並過濾台灣範圍
        df[["gx","gy"]] = df[["gx","gy"]].apply(pd.to_numeric, errors="coerce")
        mask = df["gx"].between(119,122) & df["gy"].between(21,26)
        pts = gpd.GeoDataFrame(
            df[mask].copy(),
            geometry=[Point(xy) for xy in zip(df.loc[mask,"gx"], df.loc[mask,"gy"])],
            crs="EPSG:4326"
        )
        # 空間套疊
        join_cols = [county_field, town_field] + ([vill_field] if vill_field else [])
        joined = gpd.sjoin(pts, gdf[join_cols + ["geometry"]], how="left", predicate="within")

        # 回寫行政區
        for fld in join_cols:
            df.loc[mask, fld] = joined[fld].values

        # 顯示前五筆
        st.subheader("前五筆結果預覽")
        st.dataframe(df.head())

        # 提供下載
        towrite = io.BytesIO()
        df.to_excel(towrite, index=False)
        towrite.seek(0)
        st.download_button(
            "下載完整結果(Excel)",
            data=towrite,
            file_name="geocoded_annotated.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
