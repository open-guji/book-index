from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np, functools
F1=ImageFont.truetype('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',64)
F2=ImageFont.truetype('/usr/share/fonts/opentype/unifont/unifont.otf',64)
@functools.lru_cache(None)
def bm(c):
    for F in (F1,F2):
        if F.getmask(c).getbbox():
            im=Image.new('L',(72,72),0); ImageDraw.Draw(im).text((4,0),c,255,font=F)
            im=im.filter(ImageFilter.GaussianBlur(1.5))
            return np.asarray(im,dtype=float)/255
    return None
def dice(a,b):
    return 2*(a*b).sum()/max(1e-6,(a*a).sum()+(b*b).sum())
def sim(c1,c2):
    a,b=bm(c1),bm(c2)
    if a is None or b is None: return 0.0
    w=dice(a,b)
    L=dice(a[:,:36],b[:,:36]); R=dice(a[:,36:],b[:,36:]); T=dice(a[:36],b[:36]); B=dice(a[36:],b[36:])
    return round(w,3), round(max(L,R,T,B),3)
if __name__=='__main__':
    for p in ['揚楊','曰日','芑苞','孫張','綱綸','軾洵','均鈞','佘畬','柯珂','城珹','允胤','逺遠','僧洪']:
        print(p,sim(p[0],p[1]))
