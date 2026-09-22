# ComfyUI-Bleachery

[English](README.md) | 繁體中文

去除圖片黃色偏色（白平衡校正）的 ComfyUI 自訂節點。

透過將圖片轉換到 LAB 色彩空間，分析 B（藍-黃）通道的平均偏移量，
自動將偏黃的圖片拉回中性色調 —— 適合用來修正老照片、螢光燈拍攝、
或是 AI 生圖常見的暖色偏黃問題。

## ✨ 特色

- 🎨 基於 LAB 色彩空間的白平衡校正，只調整色調不影響亮度
- 🎚️ 可調整校正強度（`strength`），從輕微微調到強力去黃
- 📦 支援 batch 輸入，一次處理多張圖片
- 🧠 自動判斷：只有圖片真的偏黃時才會做校正，不會誤傷本來就中性的圖片
- ⚡ 純 OpenCV 運算，速度快、不佔用額外 GPU 資源

## 📸 效果示意

```
原圖（偏黃） ──▶ Bleachery ──▶ 校正後（中性色調）
```

## 🔧 安裝方式

### 方法一：手動安裝

1. 進入 ComfyUI 的自訂節點資料夾：
   ```bash
   cd ComfyUI/custom_nodes
   ```
2. Clone 本專案：
   ```bash
   git clone https://github.com/K0KU20/ComfyUI-Bleachery.git
   ```
3. 安裝相依套件：
   ```bash
   cd ComfyUI-Bleachery
   pip install -r requirements.txt
   ```
4. 重新啟動 ComfyUI。

### 方法二：ComfyUI Manager

若已安裝 [ComfyUI-Manager](https://github.com/ltdrdata/ComfyUI-Manager)，
可透過 Manager 搜尋 `ComfyUI-Bleachery` 並直接安裝。

## 🚀 使用方式

1. 在畫布上按右鍵 → **Add Node** → **image** → **postprocessing** → **Bleachery**
   （或直接在搜尋框輸入 `Bleachery`）
2. 將 `Load Image` 節點的輸出接到 `Bleachery` 的 `image` 輸入
3. 調整 `strength` 參數（預設 `0.8`）
4. 將輸出接到 `Save Image` 或 `Preview Image`

### 範例工作流程

```
Load Image → Bleachery → Save Image
```

### 節點參數

| 參數名稱   | 類型    | 必填 | 預設值 | 說明                                                         |
|------------|---------|------|--------|--------------------------------------------------------------|
| `image`    | IMAGE   | 是   | -      | 要處理的輸入圖片，支援 batch，也支援帶 alpha 的 RGBA 圖片      |
| `strength` | FLOAT   | 是   | 0.8    | 去黃強度，範圍 0.0–2.0，數值越大效果越強                      |
| `mask`     | MASK    | 否   | -      | 透明度遮罩（例如去背節點輸出的 mask）。接上之後，校正只會套用在不透明區域，透明背景不受影響 |

**輸出**：`image`（處理後圖片）、`mask`（原樣輸出，方便接續接到需要 mask 的節點，例如合成或存成透明 PNG）

### 🖼️ 去背 / 透明背景圖片

如果來源圖片已經去背（帶透明背景），請把去背節點輸出的 `mask` 一併接到 `Bleachery` 的 `mask` 輸入：

```
Load Image / 去背節點 ──(image)──▶ Bleachery ──(image)──▶ Save Image
              └──────(mask)───────▶      │
                                          └──(mask)──▶ （視需要接到其他節點）
```

這樣可以避免兩個常見問題：
- 透明背景被誤判成需要校正的顏色，導致背景變成怪異的紫紅色
- alpha（透明）資訊在處理過程中遺失，輸出圖片變成沒有透明背景

## 🧪 運作原理

節點內部流程：

1. 將圖片從 RGB 轉換到 **LAB 色彩空間**（L = 亮度，A = 綠-紅，B = 藍-黃）
2. 計算整張圖 B 通道的平均值，與中性值 `128` 比較，得出「偏黃程度」
3. 若偏黃（平均值 > 128），依 `strength` 比例將 B 通道往 `128` 拉近
4. 轉換回 RGB 並輸出

```python
yellow_strength = mean(B) - 128
if yellow_strength > 0:
    B_corrected = clip(B - yellow_strength * strength, 0, 255)
```

## 📁 專案結構

```
ComfyUI-Bleachery/
├── __init__.py        # 節點註冊入口
├── nodes.py            # 節點主邏輯
├── requirements.txt    # 相依套件
└── README.md
```

## 🛠️ 需求環境

- ComfyUI（任何近期版本）
- Python 套件：`opencv-python`、`numpy`

## 🤝 貢獻

歡迎提出 Issue 或 Pull Request！無論是回報 bug、建議新功能，
或是想加入更多色彩校正演算法，都非常歡迎。

## 📄 授權

本專案採用 [MIT License](LICENSE) 授權。

## 🙏 致謝

核心白平衡演算法基於 LAB 色彩空間的 B 通道偏移校正概念實作。

## 📝 更新紀錄

- **v1.1**：新增透明背景 / 去背圖片支援。節點現在能處理帶 alpha 通道的 RGBA 圖片，並新增選填的 `mask` 輸入，讓校正只作用在不透明區域，修正透明背景被誤染成紫紅色、以及輸出遺失透明圖層的問題。
- **v1.0**：初版釋出。
