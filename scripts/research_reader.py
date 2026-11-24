"""Build a searchable evidence reader from the editable local source data."""
from html import escape as esc
import re

def build_research(root,read,sources,reader,table):
    status=read('research_status.json');stats=status['stats'];audit=read('claim_audit.json')
    stats={**stats,'claims':len(audit),'document_entries':sum(s['id'].startswith('D') for s in sources)}
    def links(ids):return ' · '.join('<a href="appendix.html#'+sid+'">'+sid+'</a>' for sid in ids.split())
    body='<section class="research-stats">'+''.join(f'<div><b>{stats[key]}</b><span>{label}</span></div>' for key,label in [('document_entries','公開文件／網頁條目'),('retrieved_document_entries','已保存原文'),('reviewed_document_entries','已核相關頁'),('claims','主張核證項目')])+'</section>'
    body+='<section class="callout"><strong>引用範圍</strong><p>'+esc(status['scope'])+'</p><p>'+esc(status['limit'])+'</p><p><a href="data/sources.csv">來源目錄 CSV</a> · <a href="data/claim_audit.csv">主張核證 CSV</a> · <a href="data/timeline.csv">時間線 CSV</a></p></section>'
    body+='<section><div class="mini-toc"><a href="#findings">文件對讀</a><a href="#cohorts">屆別及模式</a><a href="#numbers">統計口徑</a><a href="#catalog">文件目錄</a><a href="#audit">主張核證</a></div></section>'
    findings=[
      ('科目674的教學與評核','2025年文憑試要求小組為指定對象設計及實施訓練，佔總分30%。2026–28課綱另列20小時伸展及60小時教練、訓練設計及執行，涵蓋安全、教案及試教。','D30 D36'),
      ('本科為何重視實踐','2016–18概覽與2016年評審把運動實踐連到基礎知識、學習興趣及職業相關能力。概覽也列出升學、就業與終身學習的方向。','D12 D41'),
      ('政策如何看課程取捨','2015年職教報告§2.5及註3談學生的興趣和需要，並把本科列入當時新增及修訂的科目。立法會會議紀錄§34、39記錄教育局定期按持份者期望及社會經濟需要檢視整體課程組合。','D09 D100'),
      ('2016–2022年本科評審如何維持質素','2016年要求檢討課程內容與結構，在實踐單元適當加入專項運動技能及教學實習。2019年§2.8.2把維持認可與履行指定條件掛鈎，§2.13要求在實踐單元加入心肺功能訓練。2022年評審延續第3級認可並載有當時的瑜伽單元。','D41 D42 D43'),
      ('從瑜伽到運動伸展','2025–27課綱的瑜伽單元包括動作、呼吸及運動表現。2026–28課綱把同樣20小時編為伸展運動，明列依運動項目選肌肉群和關節、掌握練習及安全守則。新課綱把跨項目選擇練習的要求寫得更具體。','D24 D36'),
      ('調整課程名稱的考慮','任教組員轉述，課程團隊希望回應學校及市場需要，顧及學生對瑜伽名稱的反應及宗教觀感，並讓名稱直接連到運動技能。招生小冊子和兩版教育局課綱分別記錄對外名稱及單元內容。','O09 D25 D24 D36'),
      ('制度與院校供應','2009指引回顧教育改革、職業導向課程試點及高中制度。教院年報交代營運調整，立法會資料逐屆列明提供機構和港專修讀人次。','D64 D35 D04 D05 D06'),
      ('學費與成績匯報','2016預算答覆交代由2016/17學年起全數資助每名高中學生修讀最多兩個應用學習課程。一般應用學習由2018年文憑試起採用三個匯報級別；資歷架構另有獨立級別。','D09 D11 D14 D56'),
      ('課程中英文名稱','2019年評審封面已用Exercise，對名稱的建議涉及中文名。考評局表7f的2021年數據仍用Sports，2022年改用Exercise。','D42 D49'),
      ('2020建議與校內實施','兩份2020年報告分別談職業進階與學校課程規劃。其後通函訂出中四或中五開課安排，港專概覽列明本科接受哪兩級學生入讀。','D17 D57 D20 D69 D70'),
      ('初中導引如何落到港專運動課','政府進度報告第16段交代初中導引已恆常化。教育局活動表第28頁列出港專科目674的兩場安排。2024年5月11日網上示範健身與籃球，5月18日在馬鞍山校園安排體適能測試和健身器材體驗。','D95 D102'),
      ('上課地點與後續選擇','2016–18概覽同列何文田及馬鞍山的場地，2019–21概覽所列模式一場地均在馬鞍山。港專的運動教育文章另說明後期相關學士課程及獎學金的發展理念。','D12 D15 D101'),
      ('新舊班與兩個開課月份','2025年中四和中五模式二新班在9月改教伸展，任教組員亦提及2024入讀的舊班繼續學瑜伽。教育局的模式一開課表把兩個年級的2025年開課日期列為10月4日。','O04 D80 D81'),
    ]
    body+='<section id="findings"><h2>本次補證重點</h2>'+''.join('<article class="finding"><h3>'+esc(title)+'</h3><p>'+esc(txt)+'</p><p class="meta">'+links(ids)+'</p></article>' for title,txt,ids in findings)+'</section>'
    body+='<section id="cohorts"><h2>入讀年級、模式及DSE屆別對照</h2><p>按組員任教經驗，2025年中四及中五模式二新班均在9月開課。下表依通函所列的常規年期對照文憑試屆別。</p>'+table(['入讀時間／年級','模式','課程年度／DSE','可確認內容','依據'],[
      ['2025.09／中四','模式二，本人任教','2026–28／2028 DSE','新班改教伸展；9月授課為本人經驗',links('O04 D69 D80')],
      ['2025.09／中五','模式二，本人任教','2025–27／2027 DSE','新班改教伸展；9月授課為本人經驗',links('O04 D70 D81')],
      ['2025.10.04／中四','模式一，官方TA／TB班','2026–28／2028 DSE','班別表列開課日期及馬鞍山場地',links('D80')],
      ['2025.10.04／中五','模式一，官方SA–SF班','2025–27／2027 DSE','班別表列開課日期及馬鞍山場地',links('D81')],
      ['2024.09.28／中四','模式一，官方SK班','2025–27／2027 DSE','與2025中五入讀同屆DSE；入讀年份不同',links('D82')],
      ['2024年入讀／舊班','本人提及的舊班','依入讀年級對照','組員描述的舊班仍學習瑜伽',links('O04')],
    ])+'<p class="meta">同一2027 DSE屆別可包括2024中四入讀及2025中五入讀。課綱須用入讀年、年級、模式及版本共同識別。模式二由學校與機構議定時間及場地（D69／70，p2§8）。</p></section>'
    body+='<section id="numbers"><h2>2016本科數據：先對齊人群和分母</h2>'+table(['統計項目','數值','原文口徑及定位'],[
      ['2014–16修讀','164人次','D06 印刷2／PDF3；統計單位為修讀人次'],
      ['2016全體考生','報考134；符合出席要求101','D87 表7f；印刷120／PDF19'],
      ['2016全體考生成績','達標或以上85.1%','分母為101名符合出席要求考生'],
      ['2016日校考生','報考129；符合出席要求97','D87 表7e；印刷114／PDF13'],
      ['2016日校考生成績','達標或以上85.6%','分母為97名符合出席要求考生'],
    ])+'<p class="limit">164按修讀人次統計，134及101分別按報考及出席要求計算。全港應用學習統計也分「報考人次」與「報考人數」，比較時應沿用每份文件的分母。</p></section>'
    docs=[s for s in sources if s['id'].startswith('D')]
    def year(s):
        m=re.search(r'(?:19|20)\d{2}',s.get('document_date_or_version','')+' '+s['title'])
        return m.group(0) if m else '9999'
    docs.sort(key=lambda s:(year(s),s['id']))
    options=lambda labels:''.join('<option>'+esc(x)+'</option>' for x in sorted(labels))
    body+='<section id="catalog"><h2>公開文件目錄</h2><p>按文件標示的年份大致排序；精確發布日、課程屆別及認可期見各條目。可用「674」「瑜伽」「2016」等搜尋。</p><div class="research-filters"><label>關鍵字<input id="source-search" type="search" placeholder="名稱、年份、來源ID或內容"></label><label>來源<select id="source-group"><option value="">全部來源</option>'+options({s['source_group'] for s in docs})+'</select></label><label>核讀狀態<select id="source-state"><option value="">全部狀態</option>'+options({s['review_state'] for s in docs})+'</select></label><button id="source-reset" type="button">重設</button></div><p id="source-count" class="meta" aria-live="polite"></p><div id="research-catalog">'
    for s in docs:
        fields=[('日期／適用版本',s.get('document_date_or_version','')),('核讀定位',s.get('locator','')),('可支持的內容',s.get('supports','')),('適用範圍',s.get('limits','')),('原件及核讀記錄',s.get('retrieval_status','本次未另取檔')+'；'+s.get('verification_status',''))]
        detail='<dl>'+''.join('<dt>'+esc(k)+'</dt><dd>'+esc(v)+'</dd>' for k,v in fields)+'</dl>'
        if s.get('url','').startswith('http'):
            label='開啟公開原文'
            detail+='<p><a href="'+esc(s['url'],quote=True)+'" target="_blank" rel="noopener">'+label+'</a> · <a href="appendix.html#'+s['id']+'">完整來源條目</a></p><p class="source-url">'+esc(s['url'])+'</p>'
        if s.get('download_sha256') and s.get('retrieval_status')=='已保存原文':detail+='<p class="hash">SHA-256：'+s['download_sha256']+'</p>'
        body+='<details class="source-record" id="research-'+s['id']+'" data-group="'+esc(s['source_group'],quote=True)+'" data-state="'+esc(s['review_state'],quote=True)+'"><summary><span class="badge">'+s['id']+'</span>'+esc(s['title'])+' <small>｜'+esc(s['review_state'])+'</small></summary>'+detail+'</details>'
    body+='</div></section><section id="audit"><h2>逐項主張核證</h2><p>每項列出投影片位置、證據性質、原文定位及適用範圍。<a href="data/claim_audit.csv">下載CSV</a></p>'
    for a in audit:
        loc='附錄' if a['slide']=='附錄' else '第'+a['slide']+'頁'
        body+='<details class="claim-record"><summary><span class="badge">'+a['id']+'</span>'+loc+'：'+esc(a['claim'])+'</summary><dl><dt>證據性質</dt><dd>'+esc(a['evidence_type'])+'／'+esc(a['status'])+'</dd><dt>來源</dt><dd>'+links(' '.join(a['source_ids']))+'</dd><dt>定位</dt><dd>'+esc(a['locators'])+'</dd><dt>適用範圍</dt><dd>'+esc(a['limits'])+'</dd></dl></details>'
    body+='</section><script src="research-search.js"></script>' 
    reader('official-research.html','公開文件與逐項核證',f'科目674與香港應用學習制度的文件目錄，包括政策原文、評審及課綱的對照。查核截至{status["date"]}。正文維持15頁，詳細證據供答問及修訂。',body)
