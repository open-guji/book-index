import json,glob,pickle,sys,re
from opencc import OpenCC
sys.path.insert(0,'.')
VAR = str.maketrans({'偽': '僞', '藳': '稿', '藁': '稿', '裏': '里', '栢': '柏', '趺': '跗', '駚': '駃', '麐': '麔','爲':'為','峯':'峰','羣':'群','啓':'啟','衞':'衛','蹟':'跡','迹':'跡','綫':'線','匯':'彙','彚':'彙','隂':'陰','陰':'陰'})
t2s=OpenCC('t2s')
sys.path.insert(0,'/home/user/book-index/.claude/qa')
import scan as _scan
VAR2={k:v for k,v in _scan.VARIANTS.items()}
def norm_t(s):
    s=re.sub(r'[\s·・、，。（）()「」《》〈〉\-－\[\]【】〔〕□]','',(s or '').translate(VAR).translate(VAR2))
    return t2s.convert(s)
if __name__=='__main__':
    root='/home/user/book-index/Work'
    W={}
    for p in glob.iglob(root+'/*/*/*/*.json'):
        d=json.load(open(p))
        if d.get('merged_into'): continue
        ms=[m for m in d.get('measures') or [] if m.get('unit')=='卷']
        W[d['id']]=dict(t=d.get('title'),at=d.get('additional_titles') or [],ot=d.get('original_title'),
          au=[a.get('name') for a in d.get('authors') or []],per=d.get('period'),dyn=d.get('dynasty'),
          ib=[(e.get('source'),e.get('source_bid')) for e in d.get('indexed_by') or []],sec=sorted({e.get('section') for e in d.get('indexed_by') or [] if e.get('section')}),
          juan=ms[0].get('number') if ms else None, sub=d.get('subtype'), p=p, desc=bool(d.get('description')))
    print(len(W))
    pickle.dump(W,open('works.pkl','wb'))
