import re, os
S=os.path.dirname(os.path.abspath(__file__)); R="/Users/michaelweinfeld/Documents/2026/PJ O'Rourke/east-village-178-115"
dos=open(os.path.join(S,'dossier_template.html')).read()
num=open(os.path.join(S,'index.html')).read()   # the built numbers page (scratch copy)

# ---- numbers page: split style / body / script
nstyle=re.search(r'<style>(.*?)</style>',num,re.S).group(1)
nmain=re.search(r'<main>(.*?)</main>',num,re.S).group(1)
ntip='<div class="tip" id="tip"></div>'
nscript=re.search(r'<script>(.*?)</script>\s*$',num,re.S).group(1)

# ---- prefix every numbers CSS selector with #numbers
def prefix_block(css):
    out=[]; i=0; n=len(css)
    while i<n:
        j=css.find('{',i)
        if j<0: out.append(css[i:]); break
        sel=css[i:j].strip()
        if sel.startswith('@media') or sel.startswith('@supports'):
            depth=1; k=j+1
            while k<n and depth: depth+= (css[k]=='{') - (css[k]=='}'); k+=1
            out.append(sel+'{'+prefix_block(css[j+1:k-1])+'}'); i=k; continue
        k=css.find('}',j); body=css[j+1:k]
        if sel.startswith('@') or sel==':root': out.append(sel+'{'+body+'}')
        else:
            parts=[]
            for p in sel.split(','):
                p=p.strip()
                if not p: continue
                if p=='html': continue
                if p=='body': parts.append('#numbers')
                elif p=='*': parts.append('#numbers *')
                else: parts.append('#numbers '+p)
            if parts: out.append(','.join(parts)+'{'+body+'}')
        i=k+1
    return ''.join(out)
pstyle=prefix_block(nstyle)
# the numbers block itself: solid paper, above the stage, its own type defaults
pstyle+='\n#numbers{position:relative;z-index:3;background:var(--paper);color:var(--ink);font-family:var(--body);font-size:17px;line-height:1.5;margin-top:-1px}\n#numbers main{position:static;z-index:auto}\n#numbers section{min-height:0;display:block;padding:0}\n#numbers .scrub{top:0}\n#numbers h2{font-optical-sizing:auto;font-variation-settings:normal}\n#numbers .big,#numbers .doors .v,#numbers .readout .v,#numbers .finding .v,#numbers .buy .cost{font-optical-sizing:auto;font-variation-settings:normal}\n#divider{position:relative;z-index:3;background:var(--paper);padding:120px 24px 40px;text-align:center}\n#divider .k{font-family:var(--mono);font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}\n#divider h2{font-family:var(--disp);font-weight:800;font-size:clamp(56px,9vw,120px);line-height:.9;margin:10px 0 0;letter-spacing:-.02em}\nbody.numbers-on #mast,body.numbers-on #rail,body.numbers-on #cap,body.numbers-on #meter,body.numbers-on #num,body.numbers-on #scrim{opacity:0;pointer-events:none;transition:opacity .4s}\n'

# ---- dossier edits: scope its section/main rules, links to the second act, scroll math over the dossier only
dos=dos.replace('main{position:relative;z-index:2}','main#dossier{position:relative;z-index:2}')
dos=dos.replace('section{min-height:100vh;display:flex;align-items:center;padding:80px 24px}','main#dossier section{min-height:100vh;display:flex;align-items:center;padding:80px 24px}')
dos=dos.replace('<main>\n<section id="s0"','<main id="dossier">\n<section id="s0"',1)
dos=dos.replace('<a href="numbers.html">The numbers →</a>','<a href="#numbers">The numbers ↓</a>')
dos=dos.replace('<a class="cta" href="numbers.html">Hour by hour, the week, the years since 2020 →</a>','<a class="cta" href="#numbers">Hour by hour, the week, the years since 2020 ↓</a>')
dos=dos.replace("const max=document.documentElement.scrollHeight-innerHeight; const t=max>0?Math.min(1,Math.max(0,scrollY/max)):0;",
 "const dm=document.getElementById('dossier'); const max=dm.offsetTop+dm.offsetHeight-innerHeight; const t=max>0?Math.min(1,Math.max(0,scrollY/max)):0; const nb=document.getElementById('numbers').getBoundingClientRect().top; document.body.classList.toggle('numbers-on', nb<innerHeight*0.5); window.__numbersOn = nb<innerHeight*0.5;")
dos=dos.replace("function frame(){ requestAnimationFrame(frame); if(!ready)return;","function frame(){ requestAnimationFrame(frame); if(!ready||window.__numbersOn)return;")
dos=dos.replace('<link rel="canonical" href="https://feldtdesign-ship-it.github.io/east-village-178-115/">','<link rel="canonical" href="https://feldtdesign-ship-it.github.io/east-village-178-115/">\n<meta name="numbers-page" content="merged">')
# insert prefixed numbers style before </style>, and the second act after </main>
dos=dos.replace('</style></head>', pstyle+'</style></head>',1)
second=('\n<div id="divider"><div class="k">Part two</div><h2>The numbers</h2></div>\n<div id="numbers">\n<main>'+nmain+'</main>\n'+ntip+'\n</div>\n')
dos=dos.replace('</main>\n<footer>', '</main>'+second+'<footer>',1)
# numbers script: append before the module script
dos=dos.replace('<script type="importmap">','<script>'+nscript+'</script>\n<script type="importmap">',1)
# the numbers mast inside the block should not link to "./"
dos=dos.replace('<a href="./" style="color:var(--ink-2);text-decoration:none">← Dossier</a> &nbsp;·&nbsp; ','<a href="#s0" style="color:var(--ink-2);text-decoration:none">↑ Dossier</a> &nbsp;·&nbsp; ')
open(os.path.join(R,'index.html'),'w').write(dos)
print('merged index:', len(dos)//1024, 'KB; numbers style rules prefixed:', pstyle.count('#numbers'))
