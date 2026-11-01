# 混两部书的 Work 拆分（2026-11-01）

来源：`.claude/qa/dedup-ncltw/README.md` 点名的「混记录」Work，加早稲田盲检（`Work数据疑误`）里同类的几条。旧清单逐条按 main 现状重核：
d59f2pzp4bup（春秋傳）、d59f9uwgehhe（聖賢高士傳讚）已被并成墓碑；d59f2hq4in0g（唐書）、d59f24mhkbnp（古文尚書）、學古編、春秋左傳 现已无混入。下表是仍混着的。

## 做了什么（`plan.json` → `split_mixed.py --apply` → `update_index.py`）
Book 改挂 8 个（Work 与 Book revision 升 major，ai_note 留痕）：
- 金剛般若波羅蜜經 d59fyh6joqo0：總目题羅什譯的 5 本（金川劉氏、明末朱墨套印、淩毓柟朱墨套印、道光淩臯、光緒二十三年）→ 羅什 Work d59f27x7hla8；留真諦譯 4 本及永樂 2 本（總目同记羅什、菩提流支、真諦三譯合订），Work 责任者去羅什、玄奘（玄奘是合刻心經的译者）。
- 水經 d59f208zpssg：「水經四十卷」2 本（桑欽撰酈道元注，叢書子目）→ 水經注 d59f283z9xj8；二／三卷本留原 Work。
- 女科證治準繩 d59f2njfg7pf：文淵閣四庫本《證治准繩》（全書）→ 證治準繩 d59f6eow1l37；四庫總目「《證治準繩》一百二十卷」著录一并移过去。

合刻本 Work 去掉附刻书的责任者（Book 只有 1 部，附刻书不另立 Work）：出使錄去袁彬（北征事蹟）、夷堅志去元好問（續夷堅志）与張元濟、臥游錄去都穆（玉壺水）、唐柳先生集去韓愈（昌黎集）、兩同書去陶弼（邕州小集）、周禮去杜牧（考工記注）。

## 没做（留着）
- 資源（resources／resource_groups）仍留原 Work，没按版次分：金剛經 nlc 趙城金藏 一条、女科證治準繩 的 wikisource／四庫等资源应归證治準繩，待资源线核。
- 夷堅志 d59fxrxuxs76 与 d59f2hrt2oe8 看似重复 Work，另走去重。
- 水經 Work 的 IB（宋史、国史經籍志等）有三卷／四十卷之分，未拆。
- 草稿库（book-index-draft）未跟，需另一 PR（fix_draft.py）；本地未能跑 build_derived --check-only（缺 book-text 索引），交 CI。
