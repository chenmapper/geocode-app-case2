
import streamlit as st
import pandas as pd
import geocoder
import geopandas as gpd
import io
from shapely.geometry import Point

st.title("地址轉經緯度工具（下載前補齊 gx/gy＋行政區）")

# 初始化狀態
if "df" not in st.session_state:
    st.session_state["df"] = None

def reset_state_on_upload():
    for key in ["df", "geocode_done"]:
        if key in st.session_state:
            del st.session_state[key]

uploaded = st.file_uploader("上傳 Excel 或 CSV 檔案", type=["xlsx", "xls", "csv"])
if uploaded:
    reset_state_on_upload()
    if uploaded.name.lower().endswith((".xlsx", ".xls")):
        df = pd.read_excel(uploaded)
    else:
        df = pd.read_csv(uploaded)

    # 移除已有的行政區欄位（為了後續重註記）
    for col in ["COUNTYNAME", "TOWNNAME", "VILLNAME"]:
        if col in df.columns:
            df.drop(columns=col, inplace=True)

    st.session_state["df"] = df.copy()

df = st.session_state.get("df", None)

if df is not None:
    st.write(f"目前資料共 {len(df)} 筆")
    st.dataframe(df.head())

    cols = df.columns.tolist()
    default = next((i for i, c in enumerate(cols) if "地址" in c), 0)
    addr_col = st.selectbox("選擇地址欄位", options=cols, index=default)

    max_n = st.number_input("Geocode 筆數上限", min_value=1, max_value=1000, value=1000)

    if st.button("執行 Geocode"):
        if "gx" not in df.columns:
            df["gx"] = pd.NA
        if "gy" not in df.columns:
            df["gy"] = pd.NA

        empty = df[df["gx"].isna() | df["gy"].isna()].copy()
        nonempty_addr = empty[addr_col].fillna("")
        to_process = nonempty_addr[nonempty_addr != ""].drop_duplicates().index.tolist()
        count = 0
        for idx in to_process[:max_n]:
            addr = df.at[idx, addr_col]
            g = geocoder.arcgis(f"{addr}, Taiwan")
            if g.ok and g.latlng:
                df.at[idx, "gx"] = g.lng
                df.at[idx, "gy"] = g.lat
            else:
                df.at[idx, "gx"] = "-"
                df.at[idx, "gy"] = "-"
            count += 1

        st.session_state["df"] = df.copy()
        st.success(f"已完成 {count} 筆 Geocode")

    st.subheader("目前結果預覽（未註記）")
    st.dataframe(st.session_state["df"].head())

    def prepare_download_df():
        df = st.session_state["df"].copy()
        if "gx" not in df.columns or "gy" not in df.columns:
            st.warning("⚠️ 尚未執行 Geocode，將下載原始資料")
            return df

        df["gx"] = pd.to_numeric(df["gx"], errors="coerce")
        df["gy"] = pd.to_numeric(df["gy"], errors="coerce")

        # 補齊重複地址的 gx/gy
        addr_to_coords = df[df["gx"].notna() & df["gy"].notna()]             .drop_duplicates(subset=[addr_col])             .set_index(addr_col)[["gx", "gy"]].to_dict(orient="index")

        for idx, row in df[(df["gx"].isna() | df["gy"].isna())].iterrows():
            addr = row[addr_col]
            if addr in addr_to_coords:
                df.at[idx, "gx"] = addr_to_coords[addr]["gx"]
                df.at[idx, "gy"] = addr_to_coords[addr]["gy"]

        mask = df["gx"].between(119, 122) & df["gy"].between(21, 26)
        if mask.sum() == 0:
            return df

        pts = gpd.GeoDataFrame(
            df[mask].copy(),
            geometry=[Point(xy) for xy in zip(df.loc[mask, "gx"], df.loc[mask, "gy"])],
            crs="EPSG:4326"
        )

        shp_path = "VILLAGE_NLSC_1140318.shp"
        gdf = gpd.read_file(shp_path).to_crs(epsg=4326)
        county_field = next(c for c in gdf.columns if "county" in c.lower())
        town_field = next(c for c in gdf.columns if "town" in c.lower())
        vill_field = next((c for c in gdf.columns if "villname" in c.lower()), None)
        join_cols = [county_field, town_field] + ([vill_field] if vill_field else [])
        joined = gpd.sjoin(pts, gdf[join_cols + ["geometry"]], how="left", predicate="within")

        for fld in join_cols:
            df[fld] = pd.NA  # 明確建立欄位
            mask_empty = mask
            df.loc[mask_empty, fld] = joined[fld].values

        return df

    towrite = io.BytesIO()
    df_to_download = prepare_download_df()
    df_to_download.to_excel(towrite, index=False)
    towrite.seek(0)

    st.download_button(
        "📥 下載最終結果（補齊經緯度＋行政區）",
        data=towrite,
        file_name="result_geocoded_annotated.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    with st.expander("🔍 除錯資訊"):
        st.write("df shape:", df.shape)
        st.write("欄位:", list(df.columns))
        st.write("已有 gx/gy 值筆數:", df["gx"].notna().sum() if "gx" in df.columns else 0)
