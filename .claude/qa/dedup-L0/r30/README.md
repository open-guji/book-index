# L0 第三十轮：和刻本串送核的疑似重复

2026-11-15 夜。来源：ai-team `domain/目录与资源/设计/2026-11-和刻本日本馆藏/总览.md`「疑似重复待核」。账本 `merges.json`（Work 2 簇 3 条＋Book 5 组 6 条）。

## 并
- Work《論語徵集覽》d59fxwolqu4i（源賴寛）并入 d59f2pw12xhc（源賴寬），异体同人同书；两条所挂宝历十年前川六左衞門等刊本 Book 993fnqa29t／99jtvg4bnk 同版，一并合并，dating 由误值 834 改 1760。
- Work「論語 日本吉漢宦撰」d59fxx7ehbsx、「論語 日本市野光彥撰」d59fxx7ehbsy 并入何晏《論語集解》d59f27xfwzya：二者是总目以刊者／附撰者为主责任者的误著，版本即吉田篁墩寛政三年箕林山房活字本、市野光彥文化十三年覆刊正平本，本 Work 已各有一条。相应 Book 合并：993g6sdo8w＋99jtmnwxs0；993g6sdo8x＋988fzvo35s＋9979895f7c。
- 尚書正義 弘化四年熊本藩時習館影刻足利學藏宋本：99513cchdt＋988g2qd5vm（同一 NDL 记录 240-16）。
- 御注孝經 文政九年狩谷氏求古樓覆刊宋本：988g36li4g＋994ynwc740。

## 不并
- 詩經世本古義 寬政十年會津藩刊本（99jtrvtqtj）与总目「日本刻本」（99524ke9ds）：后者无年份刊者，无法定版。
- 明朝紀事本末 弘化三年須原屋等刊（99jtmnwxs3）与天保十四年玉岩書堂刊（988g3h7klr）：刊年刊者不同。
- 易簡方 安永七年、文化十四年两新建条与寬延元年刊本、室町钞本：各是一版。
- 傳教大師來臺州錄／將來臺州錄（988g4i1koz／988g7xyscq）：故宫连号两件，疑一为越州錄，登 D 待核（`dedup-judged/L0-第三十轮.tsv`）。

## 顺带改正（和刻本串报的数据疑误）
韻府古篆彙選 993dldm48x dating 1508→1713；朱文公易說 9950a8s2dd「寛正十一年」推定寛政十一年（1799）；沖虛至德真經注 99jihj15hh 版本项延享四年注 1744→1747。逸史 988g1xykgg 疑误挂，需先立中井竹山《逸史》Work，留和刻本串处理。

## 关卡
check_v2、check_schema 0 ERROR；audit-merge-ledger T/L/P/R/D 0；check-classification 0；check_promo_dup 0；check-duplicate-audit PASS。
