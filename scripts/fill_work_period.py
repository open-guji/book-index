#!/usr/bin/env python3
"""补全 Work.period（A11，2026-11-02）。只用有据来源，冲突者不改、另出清单。

来源优先序（各来源互证，不一致即列冲突）：
  dyn     authors[0].dynasty 为无歧义朝代名
  ent     authors[0].entity_id 的 Entity.period（Entity 的 period 若自 work 反推则不取，免闭环；dynasty 为歧义名不取）
  note    ai_note 载「國圖著錄：（朝）責任者」
  bracket 题名首方括号纂修年号／民國（方志、家谱）——仅在无其它来源时用
与 period_upper 相斥者（period 晚于上限）列冲突、不改。
用法: python3 scripts/fill_work_period.py [--apply] [--report DIR]
"""
import glob, json, re, sys, os, collections
ORD=['pre-qin','qin-han','three-kingdoms','jin','nanbeichao','sui-tang','five-dynasties','song','liao-jin-yuan','ming','qing','modern']
DYN={'清':'qing','明':'ming','元':'liao-jin-yuan','唐':'sui-tang','民國':'modern','民国':'modern','中華民國':'modern','北宋':'song','南宋':'song','隋':'sui-tang','五代':'five-dynasties','遼':'liao-jin-yuan','金':'liao-jin-yuan','西夏':'liao-jin-yuan','三國':'three-kingdoms','東漢':'qin-han','西漢':'qin-han','漢':'qin-han','汉':'qin-han','戰國':'pre-qin','春秋':'pre-qin','晉':'jin','晋':'jin','西晉':'jin','東晉':'jin','南朝宋':'nanbeichao','劉宋':'nanbeichao','南北朝':'nanbeichao','三國魏':'three-kingdoms','南朝梁':'nanbeichao','南朝齊':'nanbeichao','南朝陳':'nanbeichao','北魏':'nanbeichao','北齊':'nanbeichao','北周':'nanbeichao'}
AMB={'宋','魏','周','梁','吳','蜀','陳','齊','秦'}
RQ='順治 康熙 雍正 乾隆 嘉慶 道光 咸豐 同治 光緒 宣統'.split()
RM='洪武 建文 永樂 洪熙 宣德 正統 景泰 天順 成化 弘治 正德 嘉靖 隆慶 萬曆 萬歷 泰昌 天啟 崇禎'.split()
NOTEDYN={'清':'qing','明':'ming','元':'liao-jin-yuan','唐':'sui-tang'}
TODAY='2026-11-02'
def bracket(t):
    m=re.match(r'^[\[［【(（]([^\]］】)）]{1,6})[\]］】)）]',t)
    if not m: return None
    b=m.group(1)
    if b in ('民國','民国'): return 'modern',b
    if b in RQ or b=='清': return 'qing',b
    if b in RM or b=='明': return 'ming',b
def note(n):
    m=re.search(r'國圖著錄：[（(]([清明元唐])[）)]([^，。；\n）)]{1,10})',n or '')
    if m: return NOTEDYN[m.group(1)],m.group(1)+m.group(2)
def main():
    apply='--apply' in sys.argv
    rep=sys.argv[sys.argv.index('--report')+1] if '--report' in sys.argv else None
    E={}
    for p in glob.glob('Entity/*/*/*/*.json'):
        d=json.load(open(p)); E[d['id']]=d
    plan=[];conf=[];stat=collections.Counter()
    for p in sorted(glob.glob('Work/*/*/*/*.json')):
        d=json.load(open(p))
        if d.get('period') or d.get('merged_into'): continue
        a=d.get('authors') or []
        c=[]
        if '不一致' in (d.get('ai_note') or '') and '未寫' in (d.get('ai_note') or ''): stat['skip_inconsistent_note']+=1; continue  # 录入时有意未写朝代
        if a:
            a0=a[0]
            if re.search('舊題|旧题|偽|僞|托',(a0.get('role') or '')+str(a0.get('role_basis',''))): stat['skip_attrib']+=1; continue
            dy=a0.get('dynasty')
            if False and dy in DYN and dy not in AMB:  # dyn 路线 2026-11-02 抽检错 6.7%（多为叢書子目承叢書撰者朝代），已停用
                c.append(('dyn',DYN[dy],f'據 authors[0].dynasty「{dy}」（A11 {TODAY} 補）'))
            e=E.get(a0.get('entity_id') or '')
            if e and e.get('period') and not e.get('merged_into') and not dy:  # 撰人朝代闕才据 Entity；authors 已写朝代者属 dyn 路线（已停用）
                eb=e.get('period_basis') or ''
                if re.search('所繫|從所繫',eb): stat['skip_circular']+=1
                elif e.get('dynasty') in AMB: stat['skip_amb']+=1
                else: c.append(('ent',e['period'],f'撰人朝代闕，據其 Entity {e["id"]}「{e.get("primary_name")}」dynasty「{e.get("dynasty")}」period {e["period"]}（其 dynasty 出處：{(e.get("dynasty_basis") or "未記")[:40]}）（A11 {TODAY} 補）'))
        if not c:
            r=note(d.get('ai_note'))
            if r and not a: c.append(('note',r[0],f'據國圖著錄責任者朝代「{r[1]}」（ai_note 載，A11 {TODAY} 補）'))
        r=bracket(d['title'])
        if r:
            if not c and a and a[0].get('dynasty'): stat['skip_bracket_dyn']+=1; continue  # 已写朝代而 period 未补者另有缘故（dyn 路线已回滚）
            if not c: c.append(('bracket',r[0],f'據題名首纂修年號「{r[1]}」（A11 {TODAY} 補）'))
            elif r[0] not in {x[1] for x in c}: conf.append((d['id'],d['title'],'bracket_vs_author',sorted({x[1] for x in c}|{r[0]}))); continue
        if not c: stat['nocand']+=1; continue
        ps={x[1] for x in c}
        if len(ps)>1: conf.append((d['id'],d['title'],'sources_disagree',sorted(ps))); continue
        per=c[0][1]; up=d.get('period_upper')
        if up and ORD.index(per)>ORD.index(up): conf.append((d['id'],d['title'],'exceeds_upper',[per,'upper='+up])); continue
        plan.append((p,d,per,c[0][2],c[0][0]))
    cnt=collections.Counter(x[4] for x in plan)
    print('可补',len(plan),dict(cnt),'冲突',len(conf),collections.Counter(x[2] for x in conf),dict(stat))
    if rep:
        os.makedirs(rep,exist_ok=True)
        with open(rep+'/conflicts.tsv','w') as f:
            f.write('id\ttitle\treason\tvalues\n')
            for x in conf: f.write('\t'.join([x[0],x[1],x[2],','.join(x[3])])+'\n')
        with open(rep+'/plan.tsv','w') as f:
            f.write('id\ttitle\tperiod\tsource\n')
            for p,d,per,b,s in plan: f.write(f'{d["id"]}\t{d["title"]}\t{per}\t{s}\n')
    if apply:
        for p,d,per,b,s in plan:
            new={}
            for k,v in d.items():
                new[k]=v
                if k=='dynasty_basis' or (k=='authors' and 'dynasty_basis' not in d and 'dynasty' not in d): pass
            new['period']=per; new['period_basis']=b
            # 键序：period 紧随 authors/dynasty 之后无硬规定，附于 revision 前
            ordered={}
            for k,v in new.items():
                if k in ('period','period_basis'): continue
                if k=='revision': ordered['period']=per; ordered['period_basis']=b
                ordered[k]=v
            if 'period' not in ordered: ordered['period']=per; ordered['period_basis']=b
            rv=d.get('revision','1.0.0').split('.')
            ordered['revision']=f'{rv[0]}.{int(rv[1])+1}.0'; ordered['revised_at']=TODAY
            open(p,'w',encoding='utf-8').write(json.dumps(ordered,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__': main()
