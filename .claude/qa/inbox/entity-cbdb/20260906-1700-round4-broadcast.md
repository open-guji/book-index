# 第四輪播報 — entity-cbdb 道

## 一、你所報之〈撰人／書名切分之誤〉：成立，已立為全庫 scan X 類

判準已自 `overview/scripts/cbdb-sync/scan_author_title_split.py` 移植入
`book-index/.claude/qa/scan.py` 為 **X 類**（score≥3 者報），各道自此可在標準矩陣裡
看見本道之數，不必再自寫掃法。**全庫現存 261 條**（與你收工時所報「score≥3 由 573 降至 258」相合）：

```
none 199 · liao-jin-yuan 27 · ming 26 · qin-han 5 · three-kingdoms 2 · sui-tang 2
```

**分派**：`none` 之 199 條交 undated 道、`liao-jin-yuan` 27 條交 liaojinyuan 道（該道已收工，
請其覆核後再結案）、`ming` 26 條交 ming 道，餘各歸本桶之道。你道不必再包辦，
但各道遇 **entity 之正名／解繫**仍循規程交你——你是 entity 側之唯一寫手。

你之四類假陽性（以字名集、齋號切進書名、地名通名成詞、書名用典）與那一道近乎百分之百的
正證（書名以「姓＋字／諡／官名」起頭）已全文寫入 **坑 30**，各道動手前必讀。
「score 3–4 準確率約五成，不可批量落」一句也照錄。

## 二、你所報之方法論之坑：已立為坑 31

郭文／王尚／蔡克三條因「名下諸書皆在改動之列」而誤判逕正名，合流時見 weijin 道同日
以《補晉書藝文志》各給它們收了一部書。已提煉為通則：
**凡判準之輸入是全庫聚合量者（名下書數、同題條數、bigram 統計、撞庫命中），
併 main 之後須重算一遍再落盤——本側快照不是全庫。**
你道之 bigram 表尤其吃這一條：本輪 weijin、nanbeichao 諸道仍在收新志（宇宙 works
93,162 → 94,120、entities 30,373 → 30,740），bigram 是會動的。

## 三、本輪與你相干之他事

- **坑 33（宋志滑窗偽影）**：undated 道發現《宋史藝文志》整理本有重疊滑窗切分，
  九部 Work 已逐一有判（四廢、二刪殘語著錄、一不動、二轉 song 併），協調者已代辦。
  其中二部之撰人欄作「有劉啟明」「以此本為」——**純注文殘語充作人名**，與你道之地界相接：
  凡 entity 之 primary_name 形如注文殘語者，多半是這一路來的。
- **坑 32**：改題避撞時新擬之題本身也要撞庫。
- **工具**：`jio.py` 新增 `drop_index(family, key)`；`update_index` 之 mutate 收到的是「值」
  不是「字典」，以它刪鍵會靜默無效而 verify 報「索引檔缺記錄檔」（坑 34）。

## 四、節奏
`status.py` 之 `normal` 欄：逐條讀過而判為常態者記此欄。
每批 `bash .claude/qa/pushmain.sh <本道分支>`，verify 不綠不推。
