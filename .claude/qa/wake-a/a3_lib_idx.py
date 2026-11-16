# -*- coding: utf-8 -*-
import json,re,sys
sys.path.insert(0,'/tmp/wa3')
from a3norm import nz,era_year
rows=json.load(open('/tmp/wa3_jprows.json'))
for r in rows:
    y=r['year']
    if not y or y<1500 or y>1912: y=era_year(r['edition'] or '')
    r['y']=y
    r['nt']=nz(r['title'] or '')
def libmatch(year,theme_re):
    return [r for r in rows if r['y']==year and re.search(theme_re,r['nt'])]
