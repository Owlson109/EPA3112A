"""Build the offline HTML deck and reader documents from editable JSON data.
Python 3 standard library only. Run: python3 scripts/build.py
"""
from pathlib import Path
from html import escape as esc
from hashlib import sha256
import json, re, os

ROOT=Path(__file__).resolve().parents[1]
read=lambda name:json.loads((ROOT/'data'/name).read_text(encoding='utf-8'))
slides=read('content.json');sources=read('sources.json');reports=read('report_reviews.json')
timeline=read('timeline.json');changes=read('changelog.json')
byid={s['id']:s for s in sources}
assert len(slides)==15 and sum(s['seconds'] for s in slides)==1020
for s in slides:
    assert all(x in byid for x in s['refs']),s['title']
from bibliography import build_bibliography
reference_slides,bibliography=build_bibliography(ROOT,sources,slides,reports,timeline,read('claim_audit.json'))
deck_slides=slides+reference_slides
total_slides=len(deck_slides)
intros=read('evidence_intros.json')
assert [r['slide'] for r in intros]==list(range(1,total_slides+1))
for row,slide in zip(intros,deck_slides):
    if row.get('enabled') is False:
        assert (row['slide']==1 or slide.get('appendix_number')) and not row['cards']
        continue
    assert len(row['cards'])==2
    for card in row['cards']:
        assert card['source'] in slide['refs'],(row['slide'],card['source'])
        assert card['locator'] and card['kind'] and len(card['lines'])==2
        assert card['context_before'] and card['context_after']

def clock(sec):return f'{sec//60}:{sec%60:02d}'
def plain(s):return re.sub('<[^>]+>','',s)
def refs(s,modal=False):
    out=[]
    for sid in s['refs']:
        source=byid[sid]
        extra=f' data-source="{sid}"' if modal else ' target="_blank" rel="noopener"'
        out.append(f'<a href="appendix.html#{sid}"{extra}><b>{sid}</b> {esc(source.get("short",source["title"]))}</a>')
    return ' '.join(out)
def notes(s):
    if s.get('appendix_number'):
        return '<p class="note-meta">資料來源附頁 · 查閱及答問用途，不計入正文17分鐘。</p>'+''.join('<p>'+p+'</p>' for p in s['notes'])
    return f'<p class="note-meta">講者 {s["speaker"]} · 第 {s["number"]} 頁 · 配時 {clock(s["seconds"])}</p><p class="note-purpose">本頁目的：{esc(s["purpose"])}</p>'+''.join('<p>'+p+'</p>' for p in s['notes'])+f'<p class="transition"><strong>過渡：</strong>{esc(s["transition"])}</p><p class="note-ref">來源：{refs(s)}</p>'

def asset_url(path):
    version = sha256((ROOT / path).read_bytes()).hexdigest()[:12]
    return f'{path}?v={version}'

# The official scaffold supplies the document skeleton and shared engine links.
scaffold=(ROOT/'template/index.html').read_text()
head=scaffold.split('<body',1)[0]
head=re.sub(r'lang="[^"]*"','lang="zh-Hant"',head,count=1)
head=re.sub(r'data-themes="[^"]*"','data-themes="academic-paper"',head,count=1)
head=re.sub(r'<title>.*?</title>','<title>EPA3112｜港專運動及體適能教練的發展</title>',head,flags=re.S)
head=re.sub(r'<link[^>]*fonts\.css[^>]*>\s*','',head)
assets=Path(os.path.relpath(ROOT/'assets',ROOT)).as_posix()
head=re.sub(r'href="[^"]*/assets/([^"]+)"',lambda m:f'href="{assets}/{m[1]}"',head)
head=re.sub(r'href="[^"]*style\.css"',f'href="{Path(os.path.relpath(ROOT/"style.css",ROOT)).as_posix()}"',head)
head=head.replace('themes/tokyo-night.css','themes/academic-paper.css')
# Ship the certificate geometry with its markup, including the clipped lens copies.
# Keep the stylesheet at its original URL for already-open older decks.
cover_css = (ROOT / 'evidence-intro.css').read_text(encoding='utf-8')
extra_styles = ''.join(f'<link rel="stylesheet" href="{name}">\n' for name in ('motion.css','revision.css','heading-font.css'))
head = head.replace('</head>', extra_styles + f'<style id="cover-evidence-style">\n{cover_css}\n</style>\n<link rel="stylesheet" href="course-pages.css">\n</head>')
head = re.sub(r'(<link\b[^>]*\bhref=")([^"]+\.css)(")', lambda m: m[1] + asset_url(m[2]) + m[3], head)

def masthead(slide):
    era=esc(slide['era'])
    if slide.get('layout')!='course-edition':
        return f'<div class="slide-top"><span>EPA3112　／　港專應用學習課程研究</span><span class="section-mark">{era}</span></div>'
    chapters={'A':'課程與起點','B':'資助、評審與改革','C':'校本實施與成效'}
    parts=''.join(f'<span class="chapter-part{" here" if speaker==slide["speaker"] else ""}">{label}</span>' for speaker,label in chapters.items())
    return f'<div class="slide-top"><span class="masthead"><b>EPA3112</b><span>專業及職業教育的政策環境</span></span><span class="chapter-strip">{parts}</span><span class="section-mark">{era}</span></div>'

sections=[]
for s in deck_slides:
    title='' if s['number']==1 else '<h2>'+esc(s['title'])+'</h2>'
    appendix_class=' reference-slide' if s.get('appendix_number') else ''
    footer_refs='<span>資料核讀截至2026.11.18 · HTML點文件名稱查詳情；PDF點文件名稱開啟公開原文。完整網址、核讀狀態及使用位置見研究附錄。</span>' if s.get('appendix_number') else '<span class="source-label">來源</span>'+refs(s,True)
    layout_attr=' data-layout="course-edition"' if s.get('layout')=='course-edition' else ''
    theme_attr=' data-slide-theme="conclusion-dark"' if s.get('theme')=='conclusion-dark' else ''
    sections.append(f'''<section class="slide{appendix_class}"{layout_attr}{theme_attr} data-title="{esc(s['title'],quote=True)}" data-speaker="{s['speaker']}" aria-label="第{s['number']}頁：{esc(s['title'],quote=True)}">
{masthead(s)}
{title}<div class="slide-content">{s['body']}</div>
<footer class="deck-footer"><div class="source-refs">{footer_refs}</div><span class="page-label">{s['number']:02d} / {total_slides}</span></footer>
<aside class="notes">{notes(s)}</aside></section>''')
toc=''.join(f'<li><button data-slide="{s["number"]}">{s["number"]:02d}　{esc(s["title"])}<small>'+('附頁 · 不計入正文配時' if s.get('appendix_number') else f'講者 {s["speaker"]} · {clock(s["seconds"])}')+'</small></button></li>' for s in deck_slides)
controls='''<details class="viewer-dock" open><summary>控制</summary><nav class="viewer-tools" aria-label="簡報控制">
<button data-action="prev" title="上一頁（←）" aria-label="上一頁">←</button><button data-action="next" title="下一頁（→）" aria-label="下一頁">→</button>
<button data-action="toc">目錄</button><button data-action="notes" title="開關本頁講稿（N）">講稿 N</button><button data-action="presenter" title="開啟講者視窗（S）">講者 S</button><button data-action="fullscreen" title="全螢幕（F）">全螢幕 F</button><button data-evidence-toggle aria-pressed="true" title="開關每頁前的文件重點動畫">文件動畫：開</button><button data-slide="16">資料來源</button><a href="appendix.html" target="_blank" rel="noopener">附錄</a><button data-action="print">列印</button></nav></details>'''
dialogs=f'''<dialog id="source-dialog" aria-labelledby="source-title"><div class="dialog-top"><span id="source-id"></span><button data-close aria-label="關閉來源">關閉</button></div><h2 id="source-title"></h2><dl id="source-fields"></dl><p id="source-links"></p></dialog>
<dialog id="course-excerpt" aria-labelledby="excerpt-title" data-no-swipe style="width:min(92vw,1250px);max-width:94vw"><div class="dialog-top"><h2 id="excerpt-title">附錄一 · 科目 674</h2><button type="button" data-close>關閉</button></div><img src="images/edb-69-2020-674.png" style="display:block;width:100%;height:auto" alt="科目674 運動及體適能教練，港專，中文或英文，2020/21學年中四提早開辦模式一及二，課程費用14,200元"><p>教育局通函第 69/2020 號，頁 7。表頭與科目 674 原列合併節錄。 <a href="https://www.edb.gov.hk/attachment/tc/curriculum-development/renewal/CM/EDBCM20069C.pdf#page=7" target="_blank" rel="noopener">查看原頁</a></p></dialog>
<dialog id="certificate-dialog" aria-labelledby="certificate-title" data-no-swipe><div class="dialog-top"><h2 id="certificate-title">港專證書</h2><button type="button" data-close aria-label="關閉證書">關閉</button></div><div class="certificate-enlargement"></div></dialog>
<dialog id="toc-dialog" aria-labelledby="toc-title"><div class="dialog-top"><span>正文15頁 · 配時17分鐘 · 來源附頁{len(reference_slides)}頁</span><button data-close aria-label="關閉目錄">關閉</button></div><h2 id="toc-title">簡報目錄</h2><ol class="toc-list">{toc}</ol></dialog>'''
data=json.dumps(sources,ensure_ascii=False).replace('<','\\u003c')
intro_data=json.dumps(intros,ensure_ascii=False).replace('<','\\u003c')
deck_scripts = ''.join(f'<script src="{asset_url(name)}"></script>' for name in ('evidence-intro.js', f'{assets}/runtime.js', 'notes-controls.js', 'app.js'))
certificate_filters = (ROOT / 'images/certificate-display.svg').read_text(encoding='utf-8')
(ROOT/'index.html').write_text(head+'<body class="tpl-presenter-mode-reveal epa">'+certificate_filters+'<main class="deck" data-w="1920" data-h="1080">'+''.join(sections)+'</main>'+controls+dialogs+'<script id="source-data" type="application/json">'+data+'</script><script id="evidence-intro-data" type="application/json">'+intro_data+'</script>'+deck_scripts+'</body></html>',encoding='utf-8')

nav='<nav><a href="index.html">開啟簡報</a><a href="index.html#/16">來源附頁</a><a href="storyline.html">逐頁故事線</a><a href="speaker-notes.html">三人講稿</a><a href="official-research.html">官方文件核證</a><a href="report-review.html">四份報告</a><a href="appendix.html">研究附錄</a></nav>'
def reader(filename,title,intro,body):
    doc='<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+esc(title)+'｜EPA3112</title><link rel="stylesheet" href="reader.css"><link rel="stylesheet" href="heading-font.css"></head><body><header>'+nav+'<p class="eyebrow">EPA3112 · 研究及排練資料 · 2026.11.18</p><h1>'+esc(title)+'</h1><p class="intro">'+intro+'</p></header><main>'+body+'<p class="page-footer">公開文件按原頁、段落或網頁欄目定位。O01為組員修讀經驗，O02為導師轉述，O04為組員任教經驗，O09為課程統籌就改動的說明，由Nelson記錄。</p></main><script>function revealHash(){const d=document.getElementById(decodeURIComponent(location.hash.slice(1)));if(d&&d.tagName==="DETAILS")d.open=true;}addEventListener("hashchange",revealHash);revealHash();</script></body></html>'
    if filename=='speaker-notes.html':
        doc=doc.replace('<main>','<div class="reader-notes-controls" data-notes-controls></div><main>')
        doc=doc.replace('</body>','<script src="notes-controls.js"></script></body>')
    (ROOT/filename).write_text(doc,encoding='utf-8')

def report_card(r):
    fields=[('核讀範圍',r['scope']),('定位',r['locator']),('研究對象／性質',r['method']),('可取用的內容',r['findings']),('本次簡報的用法',r['use'])]
    body=''.join('<h3>'+esc(k)+'</h3><p>'+esc(v)+'</p>' for k,v in fields)
    return f'<section class="report" id="report-{r["id"]}"><p class="eyebrow">{r["id"]} · {esc(r["year"])}</p><h2>{esc(r["title"])}</h2><p class="meta">{esc(r["author"])}</p>{body}<div class="limit"><strong>適用範圍</strong><p>{esc(r["limits"])}</p></div><p class="meta"><a href="appendix.html#{r["id"]}">完整來源條目</a> · 使用者提供PDF原件</p></section>'
reviewintro='四份報告均已作相關段落核讀。1999、2015、2017三份與交接包原件相同，沿用U14–U16；2021報告新增為U18。它們提供歷史及研究背景，本科的具體變化仍優先引用政策原文、評審及課綱。'
reader('report-review.html','四份延伸報告：閱讀與引用筆記',reviewintro,'<section class="callout">讀報告時分開三件事：<strong>研究發現、研究者建議、已實行制度</strong>。例如U18提出提高ApL評級，是研究建議；不能直接當成政府已實施的政策。</section>'+''.join(report_card(r) for r in reports))

allocation='<table><thead><tr><th>講者</th><th>頁數</th><th>內容</th><th>配時</th></tr></thead><tbody>'
for person,label in [('A','教育目的、制度與課程供應'),('B','資助、評審與2020政策'),('C','班別、伸展調整與本科教學')]:
    ss=[s for s in slides if s['speaker']==person]
    allocation+=f'<tr><td>{person}</td><td>{ss[0]["number"]}–{ss[-1]["number"]}</td><td>{label}</td><td>{clock(sum(s["seconds"] for s in ss))}</td></tr>'
allocation+='</tbody></table>'
mini='<div class="mini-toc">'+''.join(f'<a href="#slide-{s["number"]}">{s["number"]:02d}</a>' for s in slides)+'</div>'
body='<section>'+allocation+'<p class="meta">17分鐘為講述配時，未經真人排練計時。首頁及兩頁來源附頁直接顯示；第2–15頁文件過渡約5.8秒。正文14段全播約增加1分21秒，合計約18分21秒。可按空白鍵／Esc略過，或以「文件動畫」按鈕關閉。<a href="index.html#/16">資料來源附頁</a>供查閱，不計入正文配時。</p>'+mini+'</section>'
txt=['EPA3112｜港專「運動及體適能教練」的發展','15頁｜三人｜講述配時17:00｜2026-11-18','A 1–5頁 5:30；B 6–10頁 5:50；C 11–15頁 5:40','首頁及兩頁來源附頁無文件動畫；第2–15頁共14段全播約增加1:21，合計約18:21；空白鍵／Esc可略過。可按實際排練調整語速。','']
for s in slides:
    body+=f'<section class="notes-section" id="slide-{s["number"]}"><h2>{s["number"]:02d}　{esc(s["title"])}</h2>{notes(s)}</section>'
    txt += [f'{s["number"]:02d} {s["title"]}｜講者{s["speaker"]}｜{clock(s["seconds"])}','目的：'+s['purpose'],'',*map(plain,s['notes']),'過渡：'+s['transition'],'來源：'+', '.join(s['refs']),'']
reader('speaker-notes.html','三人逐字稿與排練配時','每頁標出要帶出的重點。「過渡」是講者離開本頁時說的最後一句，第5、10頁由此交給下一位組員。用 A−／A+ 調整字級；設定會記憶。講者視窗按 S 開啟；快速查看本頁講稿按 N。',body)
(ROOT/'speaker-notes.txt').write_text('\n'.join(txt),encoding='utf-8')

def table(headers,rows,cls=''):
    return '<div class="table-wrap"><table class="'+cls+'"><thead><tr>'+''.join('<th>'+esc(h)+'</th>' for h in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+str(c)+'</td>' for c in row)+'</tr>' for row in rows)+'</tbody></table></div>'
story_rows=[[str(s['number']),'<a href="index.html#/'+str(s['number'])+'">'+esc(s['title'])+'</a>',esc(s['purpose'])] for s in deck_slides]
story='<section class="callout"><strong>主線</strong><p>兩張港專證書提出認可與教學的疑問。追查開辦、資助及評審後，用瑜伽改伸展比對課綱和班別，最後以本科的訓練計劃評核及試教回應開場。</p></section><section>'+table(['頁碼','這一頁的標題','一句話重點'],story_rows)+'</section><section><h2>三人交接</h2>'+allocation+'<p class="meta">第16–17頁為來源查閱，不計入正文17分鐘。</p></section>'
reader('storyline.html','逐頁故事線','每頁用一句話交代作用，供Nelson及組員掌握整體次序；詳細內容及證據見逐字稿與來源附錄。',story)
(ROOT/'storyline.txt').write_text('EPA3112｜逐頁故事線｜2026-11-18\n主線：從兩張港專證書追查資歷、課程和班別的變化，最後用本科的訓練計劃評核及試教回應開場。\n\n'+'\n\n'.join(f'{s["number"]:02d}　{s["title"]}\n{s["purpose"]}' for s in deck_slides)+'\n\nA 1–5頁：教育目的、制度與課程供應\nB 6–10頁：資助、評審與2020政策\nC 11–15頁：班別、伸展調整與本科教學\n第16–17頁為來源查閱，不計入正文17分鐘。\n',encoding='utf-8')
body='<section><div class="mini-toc"><a href="#timing">分工</a><a href="#readings">四份報告</a><a href="#accreditation">評審期</a><a href="#versions">課綱版本</a><a href="#timeline">完整時間線</a><a href="#limits">文件對讀</a><a href="#changes">修訂記錄</a><a href="#sources">全部來源</a></div></section>'
body+='<section id="timing"><h2>正文分工</h2>'+allocation+'</section>'
body+='<section id="readings"><h2>四份延伸報告</h2><p>'+reviewintro+'</p>'+table(['ID／年份','報告','用法'],[[r['id']+'<br>'+esc(r['year']),'<a href="report-review.html#report-'+r['id']+'">'+esc(r['title'])+'</a>',esc(r['use'])] for r in reports])+'</section>'
body+='<section id="accreditation"><h2>四份評審摘要的日期與有效期</h2>'+table(['來源','報告日期','評審有效期','定位'],[
['D41','2016.11','2017.01.01–2021.12.31','印刷1–4／PDF2–5'],['D42','2019.11','2020.01.01–2024.12.31','印刷6–7／PDF7–8'],['D43','2022.07','2025.01.01–2027.08.31','印刷5–6／PDF6–7'],['D44','2025.06','2027.09.01–2030.08.31（未來安排）','印刷3–4／PDF4–5']])+ '<p class="meta">前兩段有效期重疊照原文保留。評審期、QR登記及個別證書的頒發日不同；QF第3級不等同DSE第3級或專業教練牌照。27資歷學分＝270名義學習時數，其中180為接觸課時。</p></section>'
body+='<section id="versions"><h2>瑜伽／伸展版本對照</h2>'+table(['編印／擬稿時間','適用版本','名稱及結構','來源'],[
['2024.05','港專小冊子','瑜伽；八部分','D51 PDF7'],['2024.06','教育局2024–26','瑜伽；八部分，180小時','D23 PDF2'],['2025.02','港專小冊子','運動伸展；七部分','D25 PDF4'],['2025.04','教育局2025–27','瑜伽；八部分，180小時','D24 PDF2'],['2025.06','評審摘要（2027–30認可期）','Stretching Exercises；七部分','D44 印刷16–17'],['2025.09（經驗所述）','模式二任教經驗：中四及中五新班','兩級新班改伸展；2024入讀仍瑜伽','O04，2026-11-16本人補充'],['2025.11','教育局2026–28課綱','伸展運動；七部分，180小時','D36 PDF2'],['2026.11.16 查閱','教育局2026–28概覽','運動伸展；七部分，180小時','D90 印刷99／PDF101'],['2026.11.16 查閱','教育局2027–29概覽','伸展運動；七部分，180小時','D73 印刷93／PDF95']])+'</section>'
timeline_rows=[]
for t in timeline:
    timeline_rows.append([esc(t.get('事件日期','')),esc(t.get('事件與可確認事項','')),esc(t.get('來源ID','')),esc(t.get('關聯及限制',''))])
# Header names are preserved from the handoff CSV; fall back to its actual keys.
if timeline and not any(r[2] for r in timeline_rows):
    for row,t in zip(timeline_rows,timeline):row[2]=esc(t.get('來源','') or t.get('來源IDs','') or list(t.values())[6])
body+='<section id="timeline"><h2>完整時間線</h2><p class="meta">時間線分列事件日期、報告日期、適用屆別及有效期，可按來源編號查閱相應文件。<a href="data/timeline.csv">下載CSV</a></p>'+table(['事件日期','事件／可確認事項','來源ID','關聯與限制'],timeline_rows,'timeline')+'</section>'
body+='<section id="limits"><h2>不同文件各可回答甚麼？</h2><ul><li>教院年報D02–D04交代營運和委託課程的變化。立法會資料D05、D06按屆列出各院校的課程，以及港專2014–16屆的修讀人次。</li><li>2016年本科評審D41記錄職業相關能力及課程檢討要求。2019年D42把認可與履行指定條件相連，其中一項是修訂心肺功能訓練。2022年D43列出續評認可期及當時的瑜伽單元。</li><li>教育局D24、D36課綱第2頁交代兩版單元的內容。O04記錄中四和中五模式二新班在9月改教伸展的任教經驗，O09說明團隊考慮的學校及市場需要、學生對名稱的反應與跨運動教學用途。</li></ul></section>' 
body+='<section id="changes"><h2>本次重要修訂</h2>'+table(['項目','修訂','依據'],[[esc(c['item']),esc(c['change']),esc(c['source'])] for c in changes])+'</section>'
body+='<section><h2>如需縮成9頁正文</h2><p>保留順序並合併：①1–2；②3–4；③5；④6–7；⑤8–9；⑥10–11；⑦12；⑧13–14；⑨15。此為編排建議，現交付正文仍是15頁，資料來源附頁另計。</p></section>'
body+='<section id="sources"><h2>來源目錄</h2><p class="meta">公開原文連結需網絡；簡報、講稿、圖像及本附錄可離線閱讀。各條目列明用於本報告的頁面或段落，以及適用的屆別和資料範圍。<a href="data/sources.csv">CSV</a> · <a href="data/sources.json">JSON</a></p>'
for s in sources:
    fields=[('日期／版本',s.get('document_date_or_version')),('頁碼／段落',s.get('locator')),('可支持的內容',s.get('supports')),('適用範圍',s.get('limits')),('本次核讀狀態',s.get('verification_status'))]
    
    detail='<dl>'+''.join('<dt>'+esc(k)+'</dt><dd>'+esc(str(v))+'</dd>' for k,v in fields if v)+'</dl>'
    url=s.get('url','')
    if url.startswith(('http://','https://')):detail+=f'<a class="source-url" href="{esc(url,quote=True)}" target="_blank" rel="noopener noreferrer">{esc(url)}</a>'
    else:detail+='<p class="meta">這項資料由組員提供。來源性質、範圍與引用位置見上。</p>'
    if s.get('alternate_url'):detail+=f'<p><a href="{esc(s["alternate_url"],quote=True)}" target="_blank" rel="noopener noreferrer">同一段落的官方網頁版</a></p>'
    if s['id'] in ('C01','C02'):detail+=f'<p><a href="images/{s["id"]}_redacted.png">查看匿名化證書</a></p>'
    body+=f'<details id="{s["id"]}"><summary><span class="badge">{s["id"]}</span>{esc(s["title"])}</summary>{detail}</details>'
body+='</section>'
body=f'<section class="callout"><a href="index.html#/16">簡報末尾資料來源附頁　{bibliography["source_count"]}項引用及延伸資料</a> · <a href="data/bibliography.csv">引用清單CSV</a><br><a href="official-research.html">本次深入檢索：官方文件目錄、{len(read("claim_audit.json"))}項主張核證及屆別對照</a></section>'+body
reader('appendix.html','來源、完整時間線與研究附錄','主簡報聚焦674本科；本頁收錄研究背景、版本差異與證據界限，供答問及後續修訂。',body)
from research_reader import build_research
build_research(ROOT,read,sources,reader,table)
lengths=[dict(slide=s['number'],characters=len(plain(''.join(s['notes'])+s['transition'])),seconds=s['seconds']) for s in slides]
(ROOT/'data/speaker_timing.json').write_text(json.dumps(lengths,ensure_ascii=False,indent=2))
print('Built index, appendix, report-review, storyline, speaker-notes HTML/TXT; sources:',len(sources))
print('Notes characters:',[(x['slide'],x['characters']) for x in lengths])
