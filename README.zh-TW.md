[English](README.md) · **繁體中文**

# picklecut · ttcut

**匹克球與桌球的比賽影片：標記回合、剪掉死球時間、疊上即時計分板，再附一份比分紀錄。** 一條流程，兩套計分引擎。

原始的桌球工具 ttcut 出自 MikaDD（台灣）之手；匹克球改寫和之後的所有版本是 deyugo 做的。兩個工具都以 MIT 授權放在這裡，雙方的著作權聲明都保留。

手機錄一整場比賽，丟進來，每次發球和每個回合結束各按一個鍵。工具會把回合之間撿球、換位、對看一眼的時間剪掉，疊上一個跟著比分和發球方走的計分板。出來的是一支緊湊、看得下去的成片，外加一份逐分的比分紀錄。

| 運動 | 繁體中文版 | 英文版 | 雙擊啟動器 |
|---|---|---|---|
| 匹克球 | `picklecut_v1_1.py` | `picklecut_v1_1_EN.py` | `picklecut.bat` / `.command`、`picklecut_EN.bat` / `.command` |
| 桌球 | `ttcut_v2_4.py` | `ttcut_v2_4_EN.py` | `ttcut.bat` / `.command`、`ttcut_EN.bat` / `.command` |

同一個工具的中文版和英文版邏輯完全相同，標記 JSON 可以互通，差別只在介面文字（`tests/` 裡的測試就是在驗證這件事）。picklecut 和 ttcut 則是同一份程式碼換上不同的計分引擎，兩者的標記 JSON 不能互通。

## 需求

- Python 3.8 以上
- ffmpeg。本工具不打包，Mac 用 `brew install ffmpeg`；Windows 把 `ffmpeg.exe` 放在腳本旁邊，或用 `--ffmpeg` 指定資料夾（[ffmpeg.org](https://ffmpeg.org/download.html)）
- 顯卡可有可無。啟動時會自動偵測硬體編碼器，見「輸出與顯卡」

## 開始使用

```bash
python3 picklecut_v1_1.py    # 匹克球
python3 ttcut_v2_4.py        # 桌球
```

或者雙擊啟動器。Mac 第一次要先 `chmod +x 檔名.command`，或右鍵選「打開」。主控台視窗要一直開著，關掉工具就停了。啟動後會開一個本機伺服器並打開瀏覽器，只綁定 `127.0.0.1`。

1. 按「載入影片」，或直接把影片拖進視窗。拖入的影片可以馬上開始標記，影格率會在 1 倍速播放時自動估出來；瀏覽器不會透露拖入檔案的路徑，所以按渲染時會跳一次檔案對話框確認。拖入 `.tags.json` 則當成標記讀入。
2. 填名稱和首發。匹克球要選雙打或單打、哪種計分制；桌球選單打或雙打。
3. 播放。每次發球按 `S`，回合結束按 `A` 或 `B`，標的是贏下回合的一方。匹克球由系統判定是得分還是換發，桌球就是得一分。
4. 右側面板即時顯示比分和剪輯統計，匹克球另有正式報分，例如 `5–3–2`。
5. 按「製作成片」。成片旁會多出 `<原名>.cut.mp4`、`<原名>.tags.json`（標記）和 `<原名>.score.txt`（比分紀錄）。

> 重新整理瀏覽器會清掉標記。長比賽中途記得按「匯出 JSON」。

## 鍵盤快捷鍵

| 按鍵 | 動作 |
|---|---|
| `Space` | 播放／暫停 |
| `←` `→` / `Shift` + `←` `→` / `Alt` + `←` `→` | 一秒／五秒／逐格 |
| `S` | 標記發球 |
| `A` / `B` | A / B 贏下回合 |
| `H` | 把當下回合標成 highlight |
| `N` | 換局 |
| `Z` | 復原上一個標記 |
| `1` `2` `3` `4` | 播放速度 0.5× / 1× / 1.5× / 2× |

游標在文字欄位裡時快捷鍵不會動，可以放心打字。拖完進度條、按過速度鈕或勾選框之後，快捷鍵照常有效。

## 修正標記

播放列下方那條時間軸（LosslessCut 風格）顯示成片會留下什麼：亮色是保留、暗色是剪掉、金色是 highlight 回合，細線是發球，白線是播放位置。點一下就跳過去。

標錯了不用從頭來。事件列的 `⟲` 鈕把那個標記移到目前播放位置，`×` 刪掉它。要手動改比分，用計分板下方的「校正」列：它在目前時間插入一筆校正，只填想改的欄位（局、分、發球方，雙打還有第幾位），後面的計分就接著算。漏錄了幾分、標錯了、或中途想設定局數，都是用它。校正會以 `adjust` 事件存進 JSON，比分紀錄裡也看得到。之後想再接著做，載入匯出的 `.tags.json`（按鈕或拖入），事件、字幕、highlight、校正和設定全部回來，照樣能改。

沒有標記的時間一律剪掉，不管那是暫停、鏡頭被擋住一分鐘、休息時相機沒關，還是第一次發球之前和最後一個回合之後。工具做不到的只有一件事：跳過同一個回合裡的某一段。

## Highlight 與字幕

回合進行中或剛結束時按 `H`，就標成 highlight。「輸出範圍」選單有三種：完整比賽；僅 Highlight，只出被標記的回合，計分板照燒，檔名 `<原名>.highlights.mp4`；完整＋Highlight，兩支檔案一起出，共用一條進度。命令列用 `--highlights`。

字幕列輸入文字，按「＋字幕」或 Enter，這行字會從目前位置起燒在成片底部置中，秒數自己填，預設 3 秒。它以 `caption` 事件存進 JSON，跨剪點會自動重新對時；整段落在剪掉區間裡的字幕就直接略過。

## 比分紀錄

每次渲染都會在成片旁多寫一份 `<原名>.score.txt`。裡面有各局結果和局數統計，還有逐分紀錄：原始影片時間、第幾局、由誰發球（雙打會標 `A#2`）、誰贏下回合、當時比分、換發（匹克球）和 highlight 回合的 ★。校正和手動換局也會列出來，所以計分板上每個數字都能在這裡找到出處。「匯出比分」鈕不渲染也能下載同一份文字，`--dry-run` 會在剪接表後面印出來。

## 計分規則

**匹克球（picklecut）**

傳統計分（side-out）是預設：只有發球方能得分。雙打每局由第二發球員開局，也就是 0-0-2；發球方輸掉回合時發球權從 #1 交給 #2，再輸就換發給對方。單打輸掉回合直接換發。一局只能在發球方贏下回合時結束。計分板用一顆圓點標 #1、兩顆標 #2，介面上顯示三碼報分。

每球得分制則是每回合都得分，勝方發下一球。這裡用的是通用規則，MLP 的 freeze 之類沒有實作。

可以切換雙打或單打；接續雙打局中段的影片時，另有起始發球員編號（#1 或 #2）可設。

**桌球（ttcut）**

兩球一換發，雙方都到 10 分後改成一球一換；到目標分且領先兩分，或到封頂，就結束一局。

雙打切開後，計分板會標示一對裡輪到誰發：● 是先填的人，●● 是後填的人。每次該隊接下發球權就換人，每局重新從 #1 開始。決勝局 5 分時的接發對調不會自動處理，用校正列的「#」輸入。校正指定發球方時，兩球一輪從那一點重新起算。

**兩者共通**：每局分數（預設 11，可改 15 或 21）、勝 2 分或封頂制、起始局數、讓分（每局套用或只有第一局）。計分只在 Python 實作一次，介面和渲染呼叫同一個函式，兩邊不會不同調。

## 剪輯規則

剪掉的是回合結束到下一次發球之間那段。

| 設定 | 預設 | 作用 |
|---|---|---|
| 回合後保留 | 1.0 s | 回合結束後多留一下 |
| 發球前保留 | 0.3 s | 下次發球前多留一下 |
| 最短剪點 | 2.0 s | 短於此秒數不剪，避免無意義跳接 |
| 重發也剪 | 關 | 連續兩次發球之間的死球時間也剪 |
| 重發後保留 | 1.5 s | 僅在上一項開啟時適用 |

picklecut 把重複發球叫重發（`--cut-replays` / `--replay-tail`），ttcut 叫擦網重發（`--cut-lets` / `--let-tail`）。

## 一場比賽分成多支影片

1. 第一支照常剪，順手匯出標記 JSON。下一段載入它，隊名、賽制、顏色就直接帶過去。
2. 下一支設起始局數。從一局中間開始的話，把讓分設成當下比分、範圍選「僅第一局」，選首發，匹克球雙打再選發球員編號。或者更省事：在開頭插一筆校正。
3. 每一段用相同畫質設定渲染，最後無損串接（stream copy，不重新編碼）：

```bash
python3 picklecut_v1_1.py --join game1.cut.mp4 game2.cut.mp4 -o match.mp4
```

## 輸出與顯卡

| 畫質 | 倍率 | CRF | preset | 說明 |
|---|---|---|---|---|
| `fast` | 0.70× | 21 | veryfast | 草稿，先確認剪點 |
| `high` | 1.00× | 18 | medium | 預設；維持來源解析度 |
| `max` | 1.40× | 16 | slow | 一律 CPU `libx264`；最慢也最好 |

影格率跟著片源，HDR 會 tone-map 成 SDR。啟動時工具會拿每個可用的硬體編碼器實際試編幾格（Windows 是 NVENC、Quick Sync、AMF，Mac 是 VideoToolbox），第一個真的能跑的就當預設。終端機會印出結果，畫質旁的「編碼器」選單可以改選其他，或改回 CPU 的 `libx264`。獨立的 NVIDIA 或 AMD 顯卡在 1080p60 比 CPU 快好幾倍；Intel 內顯配上強的桌機 CPU 大概打平。硬體解碼（`--hwaccel`）只有 Mac 預設開，Windows 上 4K 反而常變慢，因為每一格都要複製回來疊計分板。

## 命令列

手上有標記 JSON 就能不開介面直接渲染，ttcut 的參數相同：

```bash
python3 picklecut_v1_1.py match.tags.json match.MOV                       # 渲染
python3 picklecut_v1_1.py match.tags.json match.MOV -o final.mp4 --quality max
python3 picklecut_v1_1.py match.tags.json match.MOV --dry-run             # 只印剪接表與比分紀錄
python3 picklecut_v1_1.py match.tags.json match.MOV --highlights          # 精華
```

<details>
<summary>參數</summary>

| 參數 | 說明 |
|---|---|
| `-o, --out` | 輸出路徑；預設 `<來源>.cut.mp4` |
| `--lead` / `--tail` | 發球前／回合後保留秒數（預設讀 JSON） |
| `--min-cut` | 最短剪點，預設 2.0 秒 |
| `--cut-replays` / `--replay-tail` | 連續發球之間也剪／重發後保留秒數（ttcut：`--cut-lets` / `--let-tail`） |
| `--quality` | `fast` / `high` / `max`，預設 `high` |
| `--encoder` | 編碼器；預設是啟動試編通過的第一個硬體編碼器，沒有就 `libx264` |
| `--crf` / `--preset` / `--bitrate` | 覆寫畫質值／libx264 preset／碼率（例如 `40M`） |
| `--fps` / `--size` | `source` 或數字／例如 `1920x1080` |
| `--hdr` | `auto` / `tonemap` / `keep` / `ignore` |
| `--hwaccel` | `auto`（Mac 用 VideoToolbox，其餘不開）/ `none` / `cuda` / `qsv` / `d3d11va` / `dxva2` |
| `--accent` / `--font` | 計分板強調色（優先於 JSON）／字型名稱 |
| `--ffmpeg` | ffmpeg 所在資料夾 |
| `--port` / `--no-browser` / `--listen` | 埠號／不自動開瀏覽器／同時接受區網連線 |
| `--highlights` | 只渲染 `H` 標記的回合；輸出 `<來源>.highlights.mp4` |
| `--join PART...` | 無損串接已渲染的各段；搭配 `-o` |
| `--dry-run` | 只印剪接表與比分紀錄，不渲染 |

</details>

## 標記 JSON

純 JSON，可以 diff、可以手改。Mac 標記、Windows 渲染都行。

```json
{
  "version": 3, "generator": "picklecut V1.1", "source": "IMG_1496.MOV", "fps": 30,
  "sport": "pickleball",
  "players": { "A": "A 隊", "B": "B 隊" }, "firstServer": "A",
  "format": { "pointsPerGame": 11, "deuce": "standard", "cap": 12, "scoring": "sideout", "side": "doubles" },
  "start": { "games": { "A": 0, "B": 0 }, "points": { "A": 0, "B": 0 }, "handicapScope": "every" },
  "pads": { "tail": 1.0, "lead": 0.3 }, "scoreboard": { "accent": "#BFD730" },
  "events": [
    { "t": 12.400, "frame": 372, "type": "serve" },
    { "t": 15.000, "frame": 450, "type": "highlight" },
    { "t": 18.933, "frame": 568, "type": "point", "winner": "A" },
    { "t": 20.000, "frame": 600, "type": "caption", "text": "賽末點", "dur": 3 },
    { "t": 45.100, "frame": 1353, "type": "game" },
    { "t": 46.000, "frame": 1380, "type": "adjust", "games": { "A": 1 }, "server": "B", "serverNum": 2 }
  ]
}
```

事件有六種。`serve`、`point`（帶 `winner`，贏下回合的一方）和 `game` 決定剪接與計分；`highlight`、`caption`（`text`、`dur`）和 `adjust`（`games`、`points`、`server`、`serverNum` 想填哪個填哪個）只是附帶。ttcut 寫的是 `version` 2，沒有 `sport`、`format.scoring`、`start.serverNum`，它的 `format.side` 是 `singles` 或 `doubles`。

## 分享

加 `--listen` 啟動，主控台會印出一個區網網址，同一個 Wi-Fi 上的手機或筆電打開就能用，對方什麼都不用裝；影片、檔案對話框和渲染都留在主機這邊。只在信任的網路上用。架在網際網路上的版本刻意不做，那等於要把好幾 GB 的影片上傳，正是這個工具想避免的事。

要給完全沒裝 Python 的人用，跑 `build_exe.bat` 或 `build_exe.sh`（先 `pip install pyinstaller`），四個工具都會打進 `dist/`。每個執行檔要連同一個放在同資料夾的 ffmpeg 一起給。防毒軟體常在打包過程中直接刪掉剛產生的 PyInstaller 執行檔，先把資料夾加進排除清單。各平台在各自的機器上打包。

## 疑難排解

- 瀏覽器不顯示影片：多半是 HEVC。Chrome 無法預覽，Safari 可以，Mac 上還有 4K 硬體解碼。
- macOS 警告 libass 找不到 PingFang 字型路徑：無害，不用理它。
- Windows 說缺 tkinter：檔案對話框打不開。改用命令列渲染，或裝一個含 tkinter 的 Python。
- 找不到 ffmpeg：仍然可以標記和匯出 JSON。裝好 ffmpeg 或用 `--ffmpeg` 指定，再重新啟動。
- 渲染很慢：看終端機的「硬體編碼」那行，或介面的編碼器選單。`fast` 是最快的 CPU 選項；CPU 夠強的話 Intel 內顯不會比較快；Windows 上 `--hwaccel` 別開。
- 成片畫質比片源差：目標碼率低於片源時渲染前會警告，用 `--bitrate` 或 `--quality max` 蓋過去。

## 版本

小改動 +0.1，架構或輸出格式的重大變更才進位。完整更新紀錄在各腳本開頭的 docstring。

- picklecut V1.1（2026-09-02）：拖放載入、方向鍵 1 秒／5 秒／逐格、字幕、時間軸、校正與逐事件移位、highlight 與輸出範圍、起始發球員編號、`--join`、硬體編碼器偵測與編碼器選單、比分紀錄。V1（2026-08-31）：首個匹克球版本，改寫自 ttcut V2.2。
- ttcut V2.4（2026-09-02）：picklecut V1.1 所有與運動無關的功能移植回來，另加雙打的逐人發球圓點和比分紀錄。桌球計分本身自 V2.2 起沒有動過。

## 其他球拍運動

只有計分引擎和運動項目綁在一起。羽球用 picklecut 現有的選項就能做（每球得分、21 分、封頂 30）。網球和板式網球需要新的計分邏輯和盤數欄位，已經規劃、還沒實作。見 `docs/2026-08-31-pickleball-adaptation-design.md`。

## 授權

MIT，見 [LICENSE](LICENSE)。原始 ttcut 的著作權屬 MikaDD（台灣），匹克球改寫和兩個工具之後的版本屬 deyugo。工具透過外部指令呼叫 ffmpeg，本身不含也不散布 ffmpeg，ffmpeg 有自己的授權。開發過程用了 Anthropic Claude 協助寫程式。

---

Copyright (c) 2026 MikaDD (Taiwan)，原始 ttcut  
Copyright (c) 2026 deyugo，匹克球改寫與之後的版本
