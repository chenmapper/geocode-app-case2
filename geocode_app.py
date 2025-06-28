import streamlit as st
import pandas as pd
import geocoder
import geopandas as gpd
import io
from shapely.geometry import Point

st.title("批次地址 Geocode 與 行政區註記工具")

# 上傳 DataFrame 檔案
uploaded = st.file_uploader("上傳 Excel 或 CSV 檔案", type=["xlsx","xls","csv"])
if not uploaded:
    st.info("請先上傳檔案")
else:
    # 讀取 DataFrame
    if uploaded.name.lower().endswith((".xlsx",".xls")):
        df = pd.read_excel(uploaded)
    else:
        df = pd.read_csv(uploaded)

    st.write(f"資料共 {len(df)} 筆，欄位：{', '.join(df.columns)}")

    # 選擇地址欄位
    cols = df.columns.tolist()
    default = next((i for i, c in enumerate(cols) if '地址' in c), 0)
    addr_col = st.selectbox("選擇地址欄位", options=cols, index=default)

    # 步驟選擇
    run_geocode = st.checkbox("執行 Geocode (地址→經緯度)", value=True)
    run_annotate = st.checkbox("執行行政區註記 (經緯度→行政區)", value=True)
    run_download = st.checkbox("顯示下載按鈕", value=True)

    # 如果要 Geocode，確保欄位存在
    if run_geocode and "gx" not in df.columns:
        df["gx"] = pd.NA
        df["gy"] = pd.NA

    # A: Geocode
    if run_geocode:
        st.subheader("步驟 A: Geocode 地址")
        max_n = st.number_input("最多 Geocode 筆數 (上限1000)", min_value=1, max_value=1000, value=1000)
        if st.button("開始 Geocode"):
            # 找出需 geocode 的 index：gx/gy 缺值且地址非空，並去重地址
            empty = df[ df["gx"].isna() | df["gy"].isna() ].copy()
            nonempty_addr = empty[ addr_col ].fillna("")
            # 去除空地址並取唯一 index
            to_process = nonempty_addr[ nonempty_addr != "" ].drop_duplicates().index.tolist()
            count = 0
            for idx in to_process[:max_n]:
                addr = df.at[idx, addr_col]
                g = geocoder.arcgis(f"{addr}, Taiwan")
                if g.ok and g.latlng:
                    df.at[idx, "gx"] = g.lng
                    df.at[idx, "gy"] = g.lat
                else:
                    # 無法取得經緯度時標記為 '-'，避免下次重複查詢
                    df.at[idx, "gx"] = '-'  
                    df.at[idx, "gy"] = '-'  
                count += 1 
            st.success(f"已完成 {count} 筆 Geocode")

    # B: Annotate
    if run_annotate:
        st.subheader("步驟 B: 行政區註記")
        if st.button("開始註記行政區"):
            shp_path = "VILLAGE_NLSC_1140318.shp"
            gdf = gpd.read_file(shp_path).to_crs(epsg=4326)
            county_field = next(c for c in gdf.columns if "county" in c.lower())
            town_field = next(c for c in gdf.columns if "town" in c.lower())
            vill_field = next((c for c in gdf.columns if "villname" in c.lower()), None)
            df[["gx","gy"]] = df[["gx","gy"]].apply(pd.to_numeric, errors="coerce")
            mask = df["gx"].between(119,122) & df["gy"].between(21,26)
            pts = gpd.GeoDataFrame(
                df[mask].copy(),
                geometry=[Point(xy) for xy in zip(df.loc[mask,"gx"], df.loc[mask,"gy"])],
                crs="EPSG:4326"
            )
            join_cols = [county_field, town_field] + ([vill_field] if vill_field else [])
            joined = gpd.sjoin(pts, gdf[join_cols + ["geometry"]], how="left", predicate="within")
            for fld in join_cols:
                df.loc[mask, fld] = joined[fld].values
            st.success("行政區註記完成")

    # D: Preview & Download
    st.subheader("結果預覽")
    st.dataframe(df.head(5))
    if run_download:
        towrite = io.BytesIO()
        df.to_excel(towrite, index=False)
        towrite.seek(0)
        st.download_button(
            "下載完整結果(Excel)",
            data=towrite,
            file_name="geocoded_annotated.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
