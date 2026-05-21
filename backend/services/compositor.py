"""
compositor.py — 10 structurally distinct thumbnail templates.

Each template has a completely different LAYOUT LOGIC:
 0  Power Split       — diagonal hard split, person right, text left
 1  Full Bleed        — person fills entire canvas, heavy text overlay bottom-left
 2  Top Banner        — person bottom-center, large title banner top, bright bg
 3  Centered Stack    — person center, title above + subtitle below (vertical stack)
 4  Side Card         — left white/light card panel, photo bleeds right edge, no diagonal
 5  Neon Cyber        — dark grid, person left, neon-outlined text right
 6  Oversized Type    — massive single word behind person (text as background)
 7  Split Solid       — hard 50/50 solid color blocks, no gradient, flat editorial
 8  Corner Accent     — person bottom-right corner, giant title top-left, geometric shapes
 9  Magazine Cover    — portrait crop center, text wraps both sides, magazine grid
"""

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps
import io, re, random, math, os

CANVAS_W = 1280
CANVAS_H = 720

# ── FONT LOADER ──────────────────────────────────────────────────────────────
_FDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")

_DISPLAY = [os.path.join(_FDIR,"BebasNeue-Regular.ttf"),
            "C:/Windows/Fonts/Impact.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
_BLACK   = [os.path.join(_FDIR,"Montserrat-Black.ttf"),
            os.path.join(_FDIR,"Montserrat-Bold.ttf"),
            "C:/Windows/Fonts/arialbd.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
_BOLD    = [os.path.join(_FDIR,"Montserrat-Bold.ttf"),
            "C:/Windows/Fonts/arialbd.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]

_font_cache = {}
def _font(size, style="display"):
    key = (size, style)
    if key in _font_cache: return _font_cache[key]
    paths = {"display":_DISPLAY,"black":_BLACK,"bold":_BOLD}.get(style,_BOLD)
    for p in paths:
        try:
            f = ImageFont.truetype(p, size)
            _font_cache[key] = f
            return f
        except: pass
    f = ImageFont.load_default()
    _font_cache[key] = f
    return f

# ── COLOR UTILS ──────────────────────────────────────────────────────────────
def _hex(h):
    h = h.strip().lstrip("#")
    if len(h) != 6: return (20,20,35)
    return tuple(int(h[i:i+2],16) for i in (0,2,4))

def _blend(a,b,t): return tuple(int(a[i]+(b[i]-a[i])*t) for i in range(3))
def _darken(c,t):  return _blend(c,(0,0,0),t)
def _lighten(c,t): return _blend(c,(255,255,255),t)
def _lum(c):       return 0.299*c[0]+0.587*c[1]+0.114*c[2]
def _fg(c):        return (10,10,10) if _lum(c)>145 else (245,245,245)
def _rgba(c,a=255):return c+(a,)

# ── LAYER HELPERS ─────────────────────────────────────────────────────────────
def _layer(): return Image.new("RGBA",(CANVAS_W,CANVAS_H),(0,0,0,0))

def _glow(cx,cy,r,color,alpha=160,blur=80):
    L=_layer(); ImageDraw.Draw(L).ellipse([cx-r,cy-r,cx+r,cy+r],fill=color+(alpha,))
    return L.filter(ImageFilter.GaussianBlur(blur))

def _scrim_left(end,alpha=210):
    L=_layer()
    for x in range(end):
        a=int(alpha*(1-x/end)**0.55)
        ImageDraw.Draw(L).line([(x,0),(x,CANVAS_H)],fill=(0,0,0,a))
    return L

def _scrim_right(start,alpha=210):
    span=CANVAS_W-start
    L=_layer()
    for i in range(span):
        a=int(alpha*(i/span)**0.55)
        ImageDraw.Draw(L).line([(start+i,0),(start+i,CANVAS_H)],fill=(0,0,0,a))
    return L

def _scrim_bottom(start_y,alpha=220):
    span=CANVAS_H-start_y
    L=_layer()
    for i in range(span):
        a=int(alpha*(i/span)**0.6)
        ImageDraw.Draw(L).line([(0,start_y+i),(CANVAS_W,start_y+i)],fill=(0,0,0,a))
    return L

def _scrim_top(end_y,alpha=200):
    L=_layer()
    for i in range(end_y):
        a=int(alpha*(1-i/end_y)**0.6)
        ImageDraw.Draw(L).line([(0,i),(CANVAS_W,i)],fill=(0,0,0,a))
    return L

def _dot_grid(spacing=48,alpha=14):
    L=_layer()
    for x in range(0,CANVAS_W,spacing):
        for y in range(0,CANVAS_H,spacing):
            ImageDraw.Draw(L).ellipse([x-1,y-1,x+1,y+1],fill=(255,255,255,alpha))
    return L

def _scanlines(alpha=28):
    L=_layer()
    for y in range(0,CANVAS_H,4):
        ImageDraw.Draw(L).line([(0,y),(CANVAS_W,y)],fill=(0,0,0,alpha))
    return L

def _text_glow(canvas,text,pos,font,color,blur=26,alpha=110):
    L=_layer(); ImageDraw.Draw(L).text(pos,text,font=font,fill=color+(alpha,))
    canvas.alpha_composite(L.filter(ImageFilter.GaussianBlur(blur)))
    return ImageDraw.Draw(canvas)

def _shadow_text(draw,pos,text,font,fill,sh=(5,7),sh_a=190,sw=2):
    draw.text((pos[0]+sh[0],pos[1]+sh[1]),text,font=font,
              fill=(0,0,0,sh_a),stroke_width=sw,stroke_fill=(0,0,0,sh_a))
    draw.text(pos,text,font=font,fill=fill,
              stroke_width=sw,stroke_fill=(0,0,0,200))

def _fit(draw,text,max_w,max_h,max_s,min_s,style="display",sw=0):
    words=text.split()
    for s in range(max_s,min_s-1,-4):
        fn=_font(s,style); lh=int(s*1.10)
        lines,cur=[],""
        for w in words:
            t=(cur+" "+w).strip()
            if draw.textbbox((0,0),t,font=fn,stroke_width=sw)[2]<=max_w: cur=t
            else:
                if cur: lines.append(cur)
                cur=w
        if cur: lines.append(cur)
        wmax=max((draw.textbbox((0,0),l,font=fn,stroke_width=sw)[2] for l in lines),default=0)
        if wmax<=max_w and len(lines)*lh<=max_h: return lines,s,lh
    fn=_font(min_s,style); lh=int(min_s*1.10)
    lines,cur=[],""
    for w in words:
        t=(cur+" "+w).strip()
        if draw.textbbox((0,0),t,font=fn)[2]<=max_w: cur=t
        else:
            if cur: lines.append(cur)
            cur=w
    if cur: lines.append(cur)
    return lines,min_s,lh

def _chip(draw,x,y,text,font,bg,fg,r=8,px=18,h=38):
    tw=draw.textbbox((0,0),text,font=font)[2]; w=tw+px*2
    draw.rounded_rectangle([x,y,x+w,y+h],radius=r,fill=bg)
    th=draw.textbbox((0,0),text,font=font)[3]
    draw.text((x+px,y+(h-th)//2),text,font=font,fill=fg)
    return x+w

def _topic(p):
    t=(p or "").lower()
    for k,v in [("fastapi","FASTAPI"),("react","REACT"),("next.js","NEXT.JS"),
                ("nextjs","NEXT.JS"),("node","NODE.JS"),("python","PYTHON"),
                ("django","DJANGO"),("flask","FLASK"),("javascript","JS"),
                ("typescript","TS"),("golang","GO"),("rust","RUST"),
                ("docker","DOCKER"),("kubernetes","K8S"),("devops","DEVOPS"),
                ("aws","AWS"),("cloud","CLOUD"),("ai","AI"),("llm","LLM"),
                ("ml","ML"),("dsa","DSA"),("sql","SQL"),("mongo","MONGODB"),
                ("html","HTML"),("css","CSS"),("tailwind","TAILWIND")]:
        if k in t: return v
    ws=re.findall(r"[A-Za-z]+",p or "")
    return ws[0].upper()[:10] if ws else "TUTORIAL"

def _dur(p):
    if not p: return None
    m=re.search(r"(\d+)\s*(hours?|hrs?)\b",p,re.I)
    if m: return f"{m.group(1)}HR COURSE"
    m=re.search(r"(\d+)\s*(minutes?|mins?)\b",p,re.I)
    if m: return f"{m.group(1)} MIN"
    return None

# ── PERSON PASTE ──────────────────────────────────────────────────────────────
def _has_alpha(img):
    return img.mode=="RGBA" and img.split()[-1].getextrema()[0]<250

def _paste(canvas,hbytes,x,y,th,accent,flip=False,brightness=1.0):
    try:
        src=Image.open(io.BytesIO(hbytes)).convert("RGBA")
        src=ImageOps.exif_transpose(src)
        src=ImageEnhance.Contrast(src).enhance(1.18)
        src=ImageEnhance.Sharpness(src).enhance(1.35)
        src=ImageEnhance.Color(src).enhance(1.12)
        if brightness!=1.0: src=ImageEnhance.Brightness(src).enhance(brightness)
        cutout=_has_alpha(src)

        if cutout:
            bb=src.getbbox()
            if bb: src=src.crop(bb)
            sc=th/src.height; tw=int(src.width*sc)
            src=src.resize((tw,th),Image.LANCZOS)
            if flip: src=ImageOps.mirror(src)
            alpha=src.split()[-1]
            # Three shadow passes
            for off,blur,opa in [(30,48,170),(16,24,115),(6,10,75)]:
                sh=_layer(); ss=Image.new("RGBA",src.size,(0,0,0,opa)); ss.putalpha(alpha)
                sh.paste(ss,(x+off,y+off),ss)
                canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)))
            # Rim glow — two passes
            for gb,ga in [(32,125),(14,85)]:
                g=_layer(); gs=Image.new("RGBA",src.size,accent+(ga,)); gs.putalpha(alpha)
                g.paste(gs,(x-3,y-3),gs)
                canvas.alpha_composite(g.filter(ImageFilter.GaussianBlur(gb)))
            canvas.alpha_composite(src,dest=(x,y))
        else:
            asp=src.width/src.height; tw=int(th*asp)
            src=src.resize((tw,th),Image.LANCZOS)
            cw=int(th*0.74); left=max(0,(tw-cw)//2)
            src=src.crop((left,0,left+cw,th)); tw=src.width
            if flip: src=ImageOps.mirror(src)
            g=_glow(x+tw//2,y+th//2,int(th*0.6),accent,90,50)
            canvas.alpha_composite(g)
            mask=Image.new("L",(tw,th),0)
            ImageDraw.Draw(mask).rounded_rectangle([0,0,tw-1,th-1],radius=28,fill=255)
            canvas.paste(src,(x,y),mask)
            b=_layer()
            ImageDraw.Draw(b).rounded_rectangle([x-4,y-4,x+tw+4,y+th+4],
                                                 radius=32,outline=accent+(255,),width=5)
            canvas.alpha_composite(b)
    except Exception as e:
        print(f"[paste] {e}")
    return canvas

# ─────────────────────────────────────────────────────────────────────────────
# TEMPLATE 0 — POWER SPLIT
# Layout: diagonal split 55/45, person right, text left, vertical accent rule
# ─────────────────────────────────────────────────────────────────────────────
def _t0_power_split(hbytes,design,prompt):
    bg=_hex(design.get("bg_color","#080810")); ac=_hex(design.get("accent_color","#00d4ff"))
    title=design.get("title","TUTORIAL").upper(); sub=design.get("subtitle","LEARN NOW").upper()
    c=Image.new("RGBA",(CANVAS_W,CANVAS_H),_rgba(bg))
    c.alpha_composite(_glow(int(CANVAS_W*.72),int(CANVAS_H*.45),int(CANVAS_H*.85),ac,50,120))
    c.alpha_composite(_dot_grid())
    SP=580
    shadow=_layer(); ImageDraw.Draw(shadow).polygon([(SP-80,0),(CANVAS_W,0),(CANVAS_W,CANVAS_H),(SP+100,CANVAS_H)],fill=_darken(ac,.72)+(255,)); c.alpha_composite(shadow)
    diag=_layer(); ImageDraw.Draw(diag).polygon([(SP-20,0),(SP+55,0),(SP-45,CANVAS_H),(SP-120,CANVAS_H)],fill=ac+(255,)); c.alpha_composite(diag)
    edge=_layer()
    for xi in range(60):
        ImageDraw.Draw(edge).line([(SP-20+xi,0),(SP-120+xi,CANVAS_H)],fill=(255,255,255,int(100*(1-xi/60)**2)))
    c.alpha_composite(edge.filter(ImageFilter.GaussianBlur(8)))
    bar=_layer(); ImageDraw.Draw(bar).rectangle([44,60,49,CANVAS_H-60],fill=ac+(210,)); c.alpha_composite(bar)
    if hbytes: _paste(c,hbytes,SP-15,CANVAS_H-718,718,ac)
    c.alpha_composite(_scrim_left(SP-20,155))
    d=ImageDraw.Draw(c)
    lines,sz,lh=_fit(d,title,490,400,175,60,"display",2)
    fn=_font(sz,"display"); y=88
    for line in lines:
        d=_text_glow(c,line,(66,y),fn,ac,28,100); _shadow_text(d,(66,y),line,fn,(255,255,255)); y+=lh
    sf=_font(36,"bold"); sw=d.textbbox((0,0),sub,font=sf)[2]
    d.rounded_rectangle([66,y+18,66+min(520,sw+36),y+62],radius=8,fill=ac+(255,))
    d.text((82,y+24),sub,font=sf,fill=_fg(ac))
    cf=_font(26,"bold"); tag=_topic(prompt); dur=_dur(prompt); cy=CANVAS_H-70
    rx=_chip(d,66,cy,tag,cf,(255,255,255,230),(10,10,10),h=40)
    if dur: _chip(d,rx+14,cy,dur,cf,ac+(255,),_fg(ac),h=40)
    d.rectangle([0,CANVAS_H-6,CANVAS_W,CANVAS_H],fill=ac+(255,))
    return c

# ─────────────────────────────────────────────────────────────────────────────
# TEMPLATE 1 — FULL BLEED
# Layout: person fills 80% of frame edge-to-edge, heavy gradient from bottom,
#         large title bottom-left over scrim, no panel, no diagonal
# ─────────────────────────────────────────────────────────────────────────────
def _t1_full_bleed(hbytes,design,prompt):
    ac=_hex(design.get("accent_color","#ff6b35"))
    title=design.get("title","TUTORIAL").upper(); sub=design.get("subtitle","LEARN NOW").upper()
    c=Image.new("RGBA",(CANVAS_W,CANVAS_H),(5,5,5,255))
    # Person centered, fills frame
    if hbytes:
        try:
            src=Image.open(io.BytesIO(hbytes)).convert("RGBA")
            src=ImageOps.exif_transpose(src)
            src=ImageEnhance.Contrast(src).enhance(1.1); src=ImageEnhance.Color(src).enhance(1.15)
            cutout=_has_alpha(src)
            if cutout:
                bb=src.getbbox()
                if bb: src=src.crop(bb)
                th=CANVAS_H+60; sc=th/src.height; tw=int(src.width*sc)
                src=src.resize((tw,th),Image.LANCZOS)
                px=max(0,(CANVAS_W-tw)//2+160); py=-30
                # rim glow
                alpha=src.split()[-1]
                for gb,ga in [(50,130),(20,90)]:
                    g=_layer(); gs=Image.new("RGBA",src.size,ac+(ga,)); gs.putalpha(alpha)
                    g.paste(gs,(px-4,py-4),gs); c.alpha_composite(g.filter(ImageFilter.GaussianBlur(gb)))
                c.alpha_composite(src,dest=(px,py))
            else:
                th=int(CANVAS_H*1.05); sc=th/src.height; tw=int(src.width*sc)
                src=src.resize((tw,th),Image.LANCZOS)
                px=max(0,(CANVAS_W-tw)//2+100); py=-20
                mask=Image.new("L",(tw,th),255)
                c.paste(src.convert("RGB"),(px,py),mask)
        except Exception as e: print(f"[t1] {e}")
    # Heavy bottom gradient scrim
    c.alpha_composite(_scrim_bottom(int(CANVAS_H*0.3),240))
    # Left side scrim so text area stays readable
    c.alpha_composite(_scrim_left(700,120))
    # Accent glow bottom-left
    c.alpha_composite(_glow(200,CANVAS_H+100,500,ac,70,120))
    d=ImageDraw.Draw(c)
    lines,sz,lh=_fit(d,title,750,320,200,70,"display",3)
    fn=_font(sz,"display"); y=CANVAS_H-lh*len(lines)-110
    for line in lines:
        d=_text_glow(c,line,(56,y),fn,ac,34,120); _shadow_text(d,(56,y),line,fn,(255,255,255),sh=(5,8),sh_a=200,sw=3); y+=lh
    sf=_font(36,"bold"); sw2=d.textbbox((0,0),sub,font=sf)[2]
    d.rounded_rectangle([56,y+10,56+min(700,sw2+40),y+56],radius=7,fill=ac+(245,))
    d.text((72,y+16),sub,font=sf,fill=_fg(ac))
    cf=_font(26,"bold"); tag=_topic(prompt); dur=_dur(prompt); cy=CANVAS_H-54
    rx=_chip(d,56,cy,tag,cf,(255,255,255,220),(10,10,10),h=38)
    if dur: _chip(d,rx+12,cy,dur,cf,ac+(255,),_fg(ac),h=38)
    d.rectangle([0,CANVAS_H-5,CANVAS_W,CANVAS_H],fill=ac+(255,))
    return c

# ─────────────────────────────────────────────────────────────────────────────
# TEMPLATE 2 — TOP BANNER
# Layout: bright solid top half with giant title, person emerges from bottom,
#         no dark background — colorful and energetic
# ─────────────────────────────────────────────────────────────────────────────
def _t2_top_banner(hbytes,design,prompt):
    ac=_hex(design.get("accent_color","#FFD600"))
    title=design.get("title","TUTORIAL").upper(); sub=design.get("subtitle","LEARN NOW").upper()
    dark=_darken(ac,.78); mid=_darken(ac,.40)
    c=Image.new("RGBA",(CANVAS_W,CANVAS_H),(6,6,10,255))
    # Top banner — dark bg, accent stripe top edge
    banner=_layer(); ImageDraw.Draw(banner).rectangle([0,0,CANVAS_W,CANVAS_H//2+40],fill=dark+(255,)); c.alpha_composite(banner)
    # Accent top bar
    ImageDraw.Draw(c).rectangle([0,0,CANVAS_W,14],fill=ac+(255,))
    # Diagonal accent element top-right
    tri=_layer(); ImageDraw.Draw(tri).polygon([(CANVAS_W-300,0),(CANVAS_W,0),(CANVAS_W,260)],fill=ac+(40,)); c.alpha_composite(tri)
    # Bottom half bg
    bot=_layer(); ImageDraw.Draw(bot).rectangle([0,CANVAS_H//2+40,CANVAS_W,CANVAS_H],fill=(6,6,10,255)); c.alpha_composite(bot)
    # Glow at bottom
    c.alpha_composite(_glow(CANVAS_W//2,CANVAS_H,int(CANVAS_H*.7),ac,55,130))
    # Person bottom center, tall
    if hbytes: _paste(c,hbytes,int(CANVAS_W*0.58),CANVAS_H-690,690,ac,flip=True)
    # Scrim left half of bottom so person stands out
    c.alpha_composite(_scrim_right(int(CANVAS_W*0.5),60))
    d=ImageDraw.Draw(c)
    lines,sz,lh=_fit(d,title,820,280,185,65,"display",2)
    fn=_font(sz,"display"); y=28
    for line in lines:
        d=_text_glow(c,line,(60,y),fn,ac,24,90); _shadow_text(d,(60,y),line,fn,(255,255,255),sw=2); y+=lh
    sf=_font(34,"bold"); sw2=d.textbbox((0,0),sub,font=sf)[2]
    d.rounded_rectangle([60,y+10,60+min(700,sw2+36),y+54],radius=7,fill=ac+(255,))
    d.text((76,y+16),sub,font=sf,fill=_fg(ac))
    cf=_font(24,"bold"); tag=_topic(prompt); dur=_dur(prompt)
    rx=_chip(d,60,CANVAS_H-60,tag,cf,(255,255,255,220),(10,10,10),h=38)
    if dur: _chip(d,rx+12,CANVAS_H-60,dur,cf,ac+(255,),_fg(ac),h=38)
    d.rectangle([0,CANVAS_H-6,CANVAS_W,CANVAS_H],fill=ac+(255,))
    return c

# ─────────────────────────────────────────────────────────────────────────────
# TEMPLATE 3 — CENTERED HERO
# Layout: person dead center, title arcs above, subtitle below,
#         left+right text flanking — no left/right panel split
# ─────────────────────────────────────────────────────────────────────────────
def _t3_centered_hero(hbytes,design,prompt):
    bg=_hex(design.get("bg_color","#06060e")); ac=_hex(design.get("accent_color","#a855f7"))
    title=design.get("title","TUTORIAL").upper(); sub=design.get("subtitle","LEARN NOW").upper()
    c=Image.new("RGBA",(CANVAS_W,CANVAS_H),_rgba(bg))
    # Central atmosphere glow
    c.alpha_composite(_glow(CANVAS_W//2,CANVAS_H//2,int(CANVAS_H*.75),ac,65,150))
    # Secondary glow top
    c.alpha_composite(_glow(CANVAS_W//2,0,int(CANVAS_H*.4),_lighten(ac,.3),40,100))
    c.alpha_composite(_dot_grid(52,12))
    # Person center
    if hbytes: _paste(c,hbytes,int(CANVAS_W*0.34),CANVAS_H-710,710,ac)
    # Top scrim to keep title readable
    c.alpha_composite(_scrim_top(220,160))
    # Bottom scrim for subtitle
    c.alpha_composite(_scrim_bottom(480,180))
    d=ImageDraw.Draw(c)
    # Title — centered across full width top
    lines,sz,lh=_fit(d,title,CANVAS_W-120,200,190,70,"display",2)
    fn=_font(sz,"display")
    y=18
    for line in lines:
        tw=d.textbbox((0,0),line,font=fn)[2]
        x=(CANVAS_W-tw)//2
        d=_text_glow(c,line,(x,y),fn,ac,30,110); _shadow_text(d,(x,y),line,fn,(255,255,255),sw=2); y+=lh
    # Centered accent rule
    d.rectangle([CANVAS_W//2-200,y+8,CANVAS_W//2+200,y+12],fill=ac+(200,))
    # Subtitle — centered bottom
    sf=_font(36,"bold"); sw2=d.textbbox((0,0),sub,font=sf)[2]
    sx=(CANVAS_W-sw2)//2
    d.rounded_rectangle([sx-18,CANVAS_H-130,sx+sw2+18,CANVAS_H-82],radius=8,fill=ac+(245,))
    d.text((sx,CANVAS_H-126),sub,font=sf,fill=_fg(ac))
    # Bottom chips centered
    cf=_font(24,"bold"); tag=_topic(prompt); dur=_dur(prompt)
    tw2=d.textbbox((0,0),tag,font=cf)[2]+40
    dw=d.textbbox((0,0),dur,font=cf)[2]+40 if dur else 0
    total=tw2+(dw+14 if dur else 0)
    cx=(CANVAS_W-total)//2
    rx=_chip(d,cx,CANVAS_H-58,tag,cf,(255,255,255,220),(10,10,10),h=38)
    if dur: _chip(d,rx+14,CANVAS_H-58,dur,cf,ac+(255,),_fg(ac),h=38)
    d.rectangle([0,CANVAS_H-5,CANVAS_W,CANVAS_H],fill=ac+(255,))
    return c

# ─────────────────────────────────────────────────────────────────────────────
# TEMPLATE 4 — SIDE CARD
# Layout: clean light card left (no diagonal), photo bleeds into right 55%
#         editorial / clean / no gradients on the card side
# ─────────────────────────────────────────────────────────────────────────────
def _t4_side_card(hbytes,design,prompt):
    ac=_hex(design.get("accent_color","#2563eb"))
    title=design.get("title","TUTORIAL").upper(); sub=design.get("subtitle","LEARN NOW").upper()
    # Dark overall bg
    c=Image.new("RGBA",(CANVAS_W,CANVAS_H),(8,8,14,255))
    # Right side glow
    c.alpha_composite(_glow(CANVAS_W,CANVAS_H//2,int(CANVAS_H*.8),ac,55,130))
    if hbytes: _paste(c,hbytes,int(CANVAS_W*0.42),CANVAS_H-718,718,ac,flip=True)
    # CARD — clean flat rectangle, no diagonal, straight vertical edge
    CARD_W=560
    card=_layer()
    card_bg=_darken(_hex("0f1120"),.1)
    ImageDraw.Draw(card).rectangle([0,0,CARD_W,CANVAS_H],fill=(14,16,30,255))
    c.alpha_composite(card)
    # Accent left border
    ImageDraw.Draw(c).rectangle([0,0,7,CANVAS_H],fill=ac+(255,))
    # Accent right border of card — creates clean separation
    sep=_layer(); ImageDraw.Draw(sep).rectangle([CARD_W,0,CARD_W+3,CANVAS_H],fill=ac+(180,))
    c.alpha_composite(sep)
    # Top accent line inside card
    ImageDraw.Draw(c).rectangle([0,0,CARD_W,10],fill=ac+(255,))
    d=ImageDraw.Draw(c)
    M=48
    lines,sz,lh=_fit(d,title,CARD_W-M*2,380,170,60,"display",2)
    fn=_font(sz,"display"); y=70
    for line in lines:
        d=_text_glow(c,line,(M,y),fn,ac,24,90); _shadow_text(d,(M,y),line,fn,(255,255,255),sw=2); y+=lh
    # Thick rule
    d.rectangle([M,y+14,M+320,y+20],fill=ac+(220,))
    sf=_font(34,"bold"); sw2=d.textbbox((0,0),sub,font=sf)[2]
    d.rounded_rectangle([M,y+28,M+min(CARD_W-M*2,sw2+36),y+72],radius=8,fill=ac+(245,))
    d.text((M+16,y+34),sub,font=sf,fill=_fg(ac))
    cf=_font(24,"bold"); tag=_topic(prompt); dur=_dur(prompt); cy=CANVAS_H-64
    rx=_chip(d,M,cy,tag,cf,(255,255,255,220),(10,10,10),h=40)
    if dur: _chip(d,rx+12,cy,dur,cf,ac+(255,),_fg(ac),h=40)
    d.rectangle([0,CANVAS_H-6,CANVAS_W,CANVAS_H],fill=ac+(255,))
    return c

# ─────────────────────────────────────────────────────────────────────────────
# TEMPLATE 5 — NEON CYBER
# Layout: dark grid bg, person left, neon outlined text right, chromatic aberration
# ─────────────────────────────────────────────────────────────────────────────
def _t5_neon_cyber(hbytes,design,prompt):
    ac=_hex(design.get("accent_color","#00ffcc"))
    title=design.get("title","TUTORIAL").upper(); sub=design.get("subtitle","LEARN NOW").upper()
    sec=_blend(ac,(255,0,200),.5); bg=(2,2,12)
    c=Image.new("RGBA",(CANVAS_W,CANVAS_H),_rgba(bg))
    grid=_layer()
    for xi in range(0,CANVAS_W,52): ImageDraw.Draw(grid).line([(xi,0),(xi,CANVAS_H)],fill=ac+(16,))
    for yi in range(0,CANVAS_H,52): ImageDraw.Draw(grid).line([(0,yi),(CANVAS_W,yi)],fill=ac+(16,))
    c.alpha_composite(grid)
    c.alpha_composite(_glow(CANVAS_W//2,CANVAS_H+60,int(CANVAS_H*.9),ac,60,90))
    c.alpha_composite(_scanlines())
    if hbytes: _paste(c,hbytes,28,CANVAS_H-718,718,ac)
    c.alpha_composite(_scrim_right(560,190))
    TX=630; d=ImageDraw.Draw(c)
    lines,sz,lh=_fit(d,title,610,400,175,60,"display",2)
    fn=_font(sz,"display"); y=88
    for line in lines:
        gl1=_layer(); ImageDraw.Draw(gl1).text((TX+6,y+4),line,font=fn,fill=sec+(110,))
        gl2=_layer(); ImageDraw.Draw(gl2).text((TX-4,y-2),line,font=fn,fill=ac+(100,))
        c.alpha_composite(gl1.filter(ImageFilter.GaussianBlur(14)))
        c.alpha_composite(gl2.filter(ImageFilter.GaussianBlur(24)))
        d=ImageDraw.Draw(c); _shadow_text(d,(TX,y),line,fn,(255,255,255),sw=2); y+=lh
    sf=_font(32,"bold"); sw2=d.textbbox((0,0),sub,font=sf)[2]; bw=min(610,sw2+40)
    nb=_layer(); ImageDraw.Draw(nb).rounded_rectangle([TX,y+18,TX+bw,y+62],radius=5,outline=ac+(255,),width=2)
    c.alpha_composite(nb.filter(ImageFilter.GaussianBlur(5))); d=ImageDraw.Draw(c)
    d.rounded_rectangle([TX,y+18,TX+bw,y+62],radius=5,outline=ac+(255,),width=2)
    d.text((TX+16,y+25),sub,font=sf,fill=ac)
    cf=_font(22,"bold"); tag=_topic(prompt); dur=_dur(prompt); cy=CANVAS_H-68
    tw2=d.textbbox((0,0),tag,font=cf)[2]+40
    d.rounded_rectangle([TX,cy,TX+tw2,cy+38],radius=6,fill=ac+(22,),outline=ac+(200,),width=2)
    d.text((TX+20,cy+8),tag,font=cf,fill=ac)
    if dur:
        dx=TX+tw2+14; dw2=d.textbbox((0,0),dur,font=cf)[2]+40
        d.rounded_rectangle([dx,cy,dx+dw2,cy+38],radius=6,fill=sec+(22,),outline=sec+(180,),width=2)
        d.text((dx+20,cy+8),dur,font=cf,fill=sec)
    nb2=_layer(); ImageDraw.Draw(nb2).rectangle([0,CANVAS_H-6,CANVAS_W,CANVAS_H],fill=ac+(255,))
    c.alpha_composite(nb2.filter(ImageFilter.GaussianBlur(4)))
    ImageDraw.Draw(c).rectangle([0,CANVAS_H-5,CANVAS_W,CANVAS_H],fill=ac+(255,))
    return c

# ─────────────────────────────────────────────────────────────────────────────
# TEMPLATE 6 — OVERSIZED TYPE
# Layout: massive title text fills background at 40% opacity,
#         person overlaid center-right, small clean text bottom-left
#         text IS the design, not just a label
# ─────────────────────────────────────────────────────────────────────────────
def _t6_oversized_type(hbytes,design,prompt):
    bg=_hex(design.get("bg_color","#060612")); ac=_hex(design.get("accent_color","#e63946"))
    title=design.get("title","TUTORIAL").upper(); sub=design.get("subtitle","LEARN NOW").upper()
    c=Image.new("RGBA",(CANVAS_W,CANVAS_H),_rgba(bg))
    c.alpha_composite(_glow(CANVAS_W*.6,CANVAS_H*.4,int(CANVAS_H*.8),ac,45,160))
    # GIANT background text — fills entire canvas
    bg_fn=_font(310,"display")
    bg_layer=_layer()
    bd=ImageDraw.Draw(bg_layer)
    words=title.split()
    by=-30
    for word in words:
        ww=bd.textbbox((0,0),word,font=bg_fn)[2]
        bx=random.choice([-60,-30,0,30])
        bd.text((bx,by),word,font=bg_fn,fill=ac+(38,))
        by+=265
        if by>CANVAS_H+100: break
    # Second pass — offset for depth
    by2=100
    for word in (words+words)[:3]:
        ww=bd.textbbox((0,0),word,font=bg_fn)[2]
        bd.text((CANVAS_W-ww-40,by2),word,font=bg_fn,fill=_lighten(ac,.15)+(18,))
        by2+=260
    c.alpha_composite(bg_layer)
    c.alpha_composite(_dot_grid(44,10))
    if hbytes: _paste(c,hbytes,int(CANVAS_W*.36),CANVAS_H-718,718,ac)
    # Strong bottom scrim for readability
    c.alpha_composite(_scrim_bottom(int(CANVAS_H*.52),220))
    c.alpha_composite(_scrim_left(560,130))
    d=ImageDraw.Draw(c)
    # Small tight title in corner
    fn2=_font(88,"display"); y=CANVAS_H-200
    lines2,sz2,lh2=_fit(d,title,700,190,88,50,"display",2)
    fn2=_font(sz2,"display")
    for line in lines2:
        d=_text_glow(c,line,(52,y),fn2,ac,22,100); _shadow_text(d,(52,y),line,fn2,(255,255,255),sw=2); y+=lh2
    sf=_font(30,"bold"); sw2=d.textbbox((0,0),sub,font=sf)[2]
    d.rounded_rectangle([52,y+10,52+min(650,sw2+36),y+52],radius=6,fill=ac+(240,))
    d.text((68,y+14),sub,font=sf,fill=_fg(ac))
    cf=_font(22,"bold"); tag=_topic(prompt); dur=_dur(prompt)
    rx=_chip(d,52,CANVAS_H-50,tag,cf,(255,255,255,215),(10,10,10),h=36)
    if dur: _chip(d,rx+12,CANVAS_H-50,dur,cf,ac+(255,),_fg(ac),h=36)
    d.rectangle([0,CANVAS_H-5,CANVAS_W,CANVAS_H],fill=ac+(255,))
    return c

# ─────────────────────────────────────────────────────────────────────────────
# TEMPLATE 7 — HARD SPLIT FLAT
# Layout: perfectly flat 50/50 blocks — NO gradients, NO diagonal, NO glow
#         left = solid accent color, right = near-black
#         clean Swiss/Bauhaus editorial feel
# ─────────────────────────────────────────────────────────────────────────────
def _t7_hard_split_flat(hbytes,design,prompt):
    ac=_hex(design.get("accent_color","#22c55e"))
    title=design.get("title","TUTORIAL").upper(); sub=design.get("subtitle","LEARN NOW").upper()
    dark=(8,10,12); MID=CANVAS_W//2
    c=Image.new("RGBA",(CANVAS_W,CANVAS_H),(8,10,12,255))
    # Left side — solid accent
    left=_layer(); ImageDraw.Draw(left).rectangle([0,0,MID,CANVAS_H],fill=ac+(255,)); c.alpha_composite(left)
    # Hard divider
    ImageDraw.Draw(c).rectangle([MID-3,0,MID+3,CANVAS_H],fill=(255,255,255,255))
    # Person — straddles the midpoint
    if hbytes: _paste(c,hbytes,MID-200,CANVAS_H-700,700,dark)
    # Left side text — dark on accent
    d=ImageDraw.Draw(c)
    M=44
    lines,sz,lh=_fit(d,title,MID-M*2-60,380,180,60,"display",2)
    fn=_font(sz,"display"); y=80
    for line in lines:
        d.text((M,y),line,font=fn,fill=(10,10,10)); y+=lh
    # Rule
    d.rectangle([M,y+12,M+280,y+17],fill=(10,10,10,200))
    sf=_font(32,"bold"); sw2=d.textbbox((0,0),sub,font=sf)[2]
    d.rounded_rectangle([M,y+26,M+min(MID-M*2,sw2+32),y+68],radius=6,fill=(10,10,10,220))
    d.text((M+14,y+32),sub,font=sf,fill=ac)
    cf=_font(22,"bold"); tag=_topic(prompt); dur=_dur(prompt); cy=CANVAS_H-64
    rx=_chip(d,M,cy,tag,cf,(10,10,10,220),ac,h=38)
    if dur: _chip(d,rx+10,cy,dur,cf,(255,255,255,200),(10,10,10),h=38)
    # Right side — white label
    ri_x=MID+20
    d.text((ri_x,CANVAS_H-60),_topic(prompt),font=_font(28,"bold"),fill=(255,255,255,160))
    d.rectangle([0,CANVAS_H-6,CANVAS_W,CANVAS_H],fill=(255,255,255,255))
    return c

# ─────────────────────────────────────────────────────────────────────────────
# TEMPLATE 8 — CORNER ACCENT
# Layout: person bottom-right corner (partial crop), massive title top-left,
#         geometric accent shapes (circles/triangles) as pure design elements
# ─────────────────────────────────────────────────────────────────────────────
def _t8_corner_accent(hbytes,design,prompt):
    bg=_hex(design.get("bg_color","#08080e")); ac=_hex(design.get("accent_color","#f59e0b"))
    title=design.get("title","TUTORIAL").upper(); sub=design.get("subtitle","LEARN NOW").upper()
    c=Image.new("RGBA",(CANVAS_W,CANVAS_H),_rgba(bg))
    # Large accent circle — decorative, bottom-right
    circ=_layer()
    r=460
    ImageDraw.Draw(circ).ellipse([CANVAS_W-r-80,CANVAS_H-r-80,CANVAS_W+r-80,CANVAS_H+r-80],
                                  fill=_darken(ac,.55)+(255,))
    ImageDraw.Draw(circ).ellipse([CANVAS_W-r-40,CANVAS_H-r-40,CANVAS_W+r-40,CANVAS_H+r-40],
                                  fill=_darken(ac,.35)+(180,))
    c.alpha_composite(circ.filter(ImageFilter.GaussianBlur(3)))
    # Small accent circle — top decorative
    sc2=_layer()
    ImageDraw.Draw(sc2).ellipse([CANVAS_W-180,-80,CANVAS_W+80,180],fill=ac+(60,))
    c.alpha_composite(sc2.filter(ImageFilter.GaussianBlur(2)))
    # Diagonal accent bar
    bar=_layer()
    ImageDraw.Draw(bar).polygon([(CANVAS_W-500,0),(CANVAS_W-380,0),(CANVAS_W,400),(CANVAS_W,260)],
                                 fill=ac+(50,))
    c.alpha_composite(bar)
    c.alpha_composite(_dot_grid(50,11))
    # Person bottom-right — partial, emerging from circle
    if hbytes: _paste(c,hbytes,CANVAS_W-590,CANVAS_H-700,700,ac,flip=True)
    # Scrim bottom-right over person for text contrast on left
    c.alpha_composite(_scrim_right(CANVAS_W-400,100))
    d=ImageDraw.Draw(c)
    M=56
    lines,sz,lh=_fit(d,title,780,400,190,65,"display",2)
    fn=_font(sz,"display"); y=52
    for line in lines:
        d=_text_glow(c,line,(M,y),fn,ac,26,100); _shadow_text(d,(M,y),line,fn,(255,255,255),sw=2); y+=lh
    # Double rule
    d.rectangle([M,y+16,M+400,y+20],fill=ac+(220,))
    d.rectangle([M,y+26,M+200,y+29],fill=ac+(120,))
    sf=_font(34,"bold"); sw2=d.textbbox((0,0),sub,font=sf)[2]
    d.rounded_rectangle([M,y+38,M+min(780,sw2+36),y+82],radius=8,fill=ac+(245,))
    d.text((M+16,y+44),sub,font=sf,fill=_fg(ac))
    cf=_font(24,"bold"); tag=_topic(prompt); dur=_dur(prompt); cy=CANVAS_H-64
    rx=_chip(d,M,cy,tag,cf,(255,255,255,220),(10,10,10),h=40)
    if dur: _chip(d,rx+12,cy,dur,cf,ac+(255,),_fg(ac),h=40)
    d.rectangle([0,CANVAS_H-6,CANVAS_W,CANVAS_H],fill=ac+(255,))
    return c

# ─────────────────────────────────────────────────────────────────────────────
# TEMPLATE 9 — MAGAZINE COVER
# Layout: portrait crop center-left, large text fills right,
#         top category tag, fine horizontal rules — magazine grid aesthetic
# ─────────────────────────────────────────────────────────────────────────────
def _t9_magazine(hbytes,design,prompt):
    ac=_hex(design.get("accent_color","#dc2626"))
    title=design.get("title","TUTORIAL").upper(); sub=design.get("subtitle","LEARN NOW").upper()
    is_dark=True; bg=(9,9,14)
    c=Image.new("RGBA",(CANVAS_W,CANVAS_H),_rgba(bg))
    # Subtle texture gradient
    c.alpha_composite(_glow(0,0,int(CANVAS_H*.7),_darken(ac,.6),45,180))
    c.alpha_composite(_glow(CANVAS_W,CANVAS_H,int(CANVAS_H*.6),_darken(ac,.6),35,160))
    # Person left — tall portrait
    if hbytes: _paste(c,hbytes,30,CANVAS_H-710,710,ac)
    # Scrim over person — left center, so person edges are visible
    overlay=_layer()
    for x in range(380,640):
        a=int(180*((x-380)/260)**1.5)
        ImageDraw.Draw(overlay).line([(x,0),(x,CANVAS_H)],fill=(9,9,14,a))
    c.alpha_composite(overlay)
    d=ImageDraw.Draw(c)
    # Magazine-style top strip
    d.rectangle([0,0,CANVAS_W,56],fill=ac+(255,))
    cat=_topic(prompt)
    cf2=_font(28,"bold")
    d.text((24,14),cat,font=cf2,fill=_fg(ac))
    d.text((CANVAS_W-d.textbbox((0,0),"youtube.com",font=cf2)[2]-24,14),"AI SERIES",font=cf2,fill=_fg(ac))
    # Right side text area
    TX=660; d=ImageDraw.Draw(c)
    # Issue-style number
    nf=_font(22,"bold")
    d.text((TX,76),"EPISODE 01  ·  2025",font=nf,fill=(180,180,180))
    # Fine rule
    d.rectangle([TX,106,CANVAS_W-40,109],fill=(180,180,180,120))
    lines,sz,lh=_fit(d,title,CANVAS_W-TX-50,340,170,55,"display",1)
    fn=_font(sz,"display"); y=118
    for i,line in enumerate(lines):
        if i==0: d=_text_glow(c,line,(TX,y),fn,ac,22,100)
        else: d=ImageDraw.Draw(c)
        _shadow_text(d,(TX,y),line,fn,(255,255,255),sw=1); y+=lh
    # Rule under title
    d.rectangle([TX,y+10,CANVAS_W-40,y+13],fill=ac+(200,))
    # Subtitle — magazine deck style
    sf=_font(30,"bold")
    sub_lines,_,slh=_fit(d,sub,CANVAS_W-TX-50,120,30,22,"bold")
    y2=y+26
    for sl in sub_lines:
        d.text((TX,y2),sl,font=sf,fill=(210,210,210)); y2+=slh
    # Fine bottom rule
    d.rectangle([TX,y2+12,CANVAS_W-40,y2+14],fill=(130,130,130,100))
    # Tags
    cf=_font(22,"bold"); tag=_topic(prompt); dur=_dur(prompt); cy=CANVAS_H-60
    rx=_chip(d,TX,cy,tag,cf,ac+(255,),_fg(ac),h=38)
    if dur: _chip(d,rx+10,cy,dur,cf,(200,200,200,200),(20,20,20),h=38)
    # Bottom accent line
    d.rectangle([0,CANVAS_H-6,CANVAS_W,CANVAS_H],fill=ac+(255,))
    return c

# ─────────────────────────────────────────────────────────────────────────────
# ILLUSTRATION OVERLAY
# ─────────────────────────────────────────────────────────────────────────────
def _paste_illustration(canvas,ibytes,layout,ac,opacity=50):
    try:
        icon=Image.open(io.BytesIO(ibytes)).convert("RGBA")
        ts=int(CANVAS_H*.52); sc=ts/max(icon.width,icon.height,1)
        icon=icon.resize((int(icon.width*sc),int(icon.height*sc)),Image.LANCZOS)
        x=(CANVAS_W-icon.width-120) if layout=="headshot_left" else 80
        y=(CANVAS_H-icon.height)//2
        wm=_layer(); a=icon.split()[-1].point(lambda p:min(p,opacity)); icon.putalpha(a)
        wm.paste(icon,(x,y),icon); canvas.alpha_composite(wm)
    except Exception as e: print(f"[illus] {e}")
    return canvas

# ─────────────────────────────────────────────────────────────────────────────
# DISPATCHER
# ─────────────────────────────────────────────────────────────────────────────
TEMPLATES=[
    _t0_power_split,    # 0
    _t1_full_bleed,     # 1
    _t2_top_banner,     # 2
    _t3_centered_hero,  # 3
    _t4_side_card,      # 4
    _t5_neon_cyber,     # 5
    _t6_oversized_type, # 6
    _t7_hard_split_flat,# 7
    _t8_corner_accent,  # 8
    _t9_magazine,       # 9
]

def compose_thumbnail(headshot_bytes,bg_image_bytes,design,prompt_text="",
                      headshot_is_cutout=False,illustration_bytes=None,
                      template_index=None):
    if template_index is not None and 0<=template_index<len(TEMPLATES):
        renderer=TEMPLATES[template_index]
    else:
        renderer=random.choice(TEMPLATES)
    canvas=renderer(headshot_bytes,design,prompt_text)
    if illustration_bytes:
        canvas=_paste_illustration(canvas,illustration_bytes,
                                   design.get("layout","headshot_right"),
                                   _hex(design.get("accent_color","#ffffff")))
    if bg_image_bytes:
        try:
            bg=Image.open(io.BytesIO(bg_image_bytes)).convert("RGBA")
            bg=bg.resize((CANVAS_W,CANVAS_H),Image.LANCZOS)
            bg=ImageEnhance.Color(bg.convert("RGB")).enhance(0.22)
            bg=ImageEnhance.Brightness(bg).enhance(0.28)
            bg=bg.convert("RGBA")
            r,g,b,a=canvas.convert("RGBA").split()
            a=a.point(lambda p:int(p*.93))
            canvas=Image.alpha_composite(bg,Image.merge("RGBA",(r,g,b,a))).convert("RGB")
        except Exception as e:
            print(f"[bg blend] {e}"); canvas=canvas.convert("RGB")
    else:
        canvas=canvas.convert("RGB")
    out=io.BytesIO()
    canvas.save(out,format="JPEG",quality=94,optimize=True)
    out.seek(0)
    return out.read()

def get_template_count(): return len(TEMPLATES)