# 批次地址 Geocode 與 行政區註記工具

這是一個基於 **Streamlit** 的 Web 應用，能針對上傳的 DataFrame（Excel/CSV）：

* **A: Geocode**（地址 → 經緯度）
* **B: 註記行政區**（經緯度 → 縣市／鄉鎮／村里）
* **D: 下載結果**（含原始資料筆數，支援前五筆預覽）

應用可自由勾選組合（A、B、D），並一次處理最大 1000 筆 Geocode 任務，支持斷點續跑（自動跳過已有經緯度或標記為 `-` 的列）。

---

## 功能特色

1. **上傳資料**：支援 `.xlsx`、`.xls`、`.csv` 格式。
2. **地址欄位自選**：自動預設包含「地址」關鍵字的欄位，或自行下拉選擇。
3. **Geocode**：使用 ArcGIS API（添加 `, Taiwan`）批次轉換，最多 1000 筆。
4. **註記行政區**：讀取同目錄下 `VILLAGE_NLSC_1140318.shp`（台灣村里），並做空間套疊。
5. **續跑機制**：已轉換的 `gx`/`gy` 列或標記失敗 (`-`) 列會自動跳過。
6. **彈性組合**：可僅執行 Geocode、僅執行註記、或全流程一次完成。
7. **預覽與下載**：前五筆預覽；下載包含所有筆數的 Excel 結果。

---

## 檔案結構

```
table_app/
├── case2/
│   ├── geocode_app.py      # 主程式
│   ├── VILLAGE_NLSC_1140318.shp  # 台灣村里 Shapefile
│   ├── requirements.txt
│   ├── README.md           # 本說明檔
│   └── LICENSE             # MIT 授權
└── ...                     # 其他內容
```

---

## 安裝與執行

```bash
# 進入目錄
cd Downloads/table_app/case2

# 建議使用虛擬環境
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.\.venv\Scripts\activate   # Windows

# 安裝依賴
pip install -r requirements.txt

# 啟動應用
streamlit run geocode_app.py
```

1. 瀏覽器自動開啟 `http://localhost:8501`。
2. 若要網路內部他機訪問，可加參數：

   ```bash
   streamlit run geocode_app.py \
     --server.address 0.0.0.0 \
     --server.port 8501 \
     --server.enableCORS false
   ```

---

## 使用說明

1. **上傳資料**：點擊「Browse files」上傳 Excel/CSV。
2. **選擇地址欄位**：若預設不正確，可下拉選擇。
3. **勾選流程**：

   * 「執行 Geocode」 → 地址轉經緯度。
   * 「執行行政區註記」 → 經緯度轉行政區。
   * 「顯示下載按鈕」 → 顯示並提供下載功能。
4. **設定上限**：Geocode 最多處理 1000 筆，可自行調整。
5. **執行按鈕**：分別點「開始 Geocode」「開始註記行政區」。
6. **結果預覽**：下方顯示前五筆結果。
7. **下載結果**：下載完整 Excel，包含新欄位 `gx`, `gy`, `縣市`, `鄉鎮`, `村里` 等。
8. **作者簡介**：可以叫我阿瑟 警大刑事系55期畢業 我在警界服務30年 退休5年多囉 
                這是我一生中第2支上傳的app 很有趣 有興趣的可以加我的line:im144339
                我都是自學 非科班 希望用中庸之道 幫助更多需要幫助的人。  
---

## 注意事項

* **Shapefile**：請確保 `VILLAGE_NLSC_1140318.shp` 及相關配套檔案（`.dbf`, `.shx`）與程式同目錄。
* **API 時效**：ArcGIS geocode 速率有限，每次最多 1000 筆，請務必於線上環境耐心等待。
* **續跑策略**：重複或空地址、已有座標、標記為 `-` 的列都會自動跳過，方便分批處理。

---

## 授權聲明

本程式採用 **MIT License**。詳見 `LICENSE` 檔。

---

## 後續優化

* 整合 Google Maps Geocoding API（提高命中率）
* 加入使用紀錄及分析（Google Sheets/Apps Script）
* 多語系支援、UI 美化
* Docker 化、自動化 CI/CD 部署

歡迎提 issue 或 pull request，一起讓工具更好用！
