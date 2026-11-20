"""Build source appendix slides from actual citations, not the search catalog."""
from collections import defaultdict
from html import escape as esc
import csv
import json
import math
import re

ID_PATTERN = re.compile(r'\b(?:D\d{2,3}E?|[CUO]\d{2})\b')


def build_bibliography(root, sources, main_slides, reports, timeline, claims):
    byid = {s['id']: s for s in sources}
    uses = defaultdict(lambda: defaultdict(list))
    for slide in main_slides:
        for sid in slide['refs'] + slide.get('extra_notes_refs', []):
            uses[sid]['正文／逐字稿'].append(str(slide['number']))
    for claim in claims:
        for sid in claim['source_ids']:
            uses[sid]['主張核證'].append(claim['id'])
    for row in timeline:
        for sid in ID_PATTERN.findall(row.get('來源', '')):
            uses[sid]['延伸時間線'].append(row['事件ID'])
    for report in reports:
        uses[report['id']]['研究報告筆記'].append(report['id'])
    assert set(uses) <= set(byid), sorted(set(uses) - set(byid))
    authors = {r['id']: r['author'] for r in reports}
    main_ids = {sid for slide in main_slides for sid in slide['refs'] + slide.get('extra_notes_refs', [])}
    claim_ids = {sid for claim in claims for sid in claim['source_ids']} - main_ids
    report_ids = {r['id'] for r in reports} - main_ids - claim_ids
    time_ids = set(uses) - main_ids - claim_ids - report_ids
    groups = [
        ('正文及逐字稿引用', main_ids, '對應正文第1–15頁；來源編號與頁底引註一致。'),
        ('補充核證文件', claim_ids, '用於核證筆記及版本比對；未重複列出正文已引用的文件。'),
        ('四份延伸研究報告', report_ids, '使用者提供的研究報告；核讀相關段落，非逐頁通讀。'),
        ('延伸時間線參考', time_ids, '各項對應研究附錄的事件、屆別或認可期。'),
    ]
    records = []
    for label, ids, description in groups:
        ordered = sorted(ids, key=lambda sid: ('DCUO'.index(sid[0]), int(re.search(r'\d+', sid).group()), sid))
        entries = []
        for sid in ordered:
            source = byid[sid]
            record = dict(
                id=sid, group=label, title=source['title'],
                date_or_version=source['document_date_or_version'],
                author=authors.get(sid, ''), locator=source['locator'],
                url=source.get('url', ''), review_state=source['review_state'],
                used_in=dict(uses[sid]),
            )
            entries.append(record)
            records.append(record)
    def entry_html(entry):
        sid = entry['id']
        labels = {'正文及逐字稿引用': '', '補充核證文件': '核證', '四份延伸研究報告': '研究', '延伸時間線參考': '時間線'}
        kind = f'<span class="bib-kind">{labels[entry["group"]]}</span>' if labels[entry['group']] else ''
        title = entry['title']
        author = esc(entry['author']) + '。' if entry['author'] else ''
        flag = {'O01':'〔組員修讀經驗〕', 'O02':'〔導師轉述〕',
                'O04':'〔組員任教經驗〕', 'O09':'〔課程統籌說明〕'}.get(sid, '')
        return (
            f'<article class="bib-entry" data-bibliography-id="{sid}">'
            f'<span class="bib-id">{sid}</span><div class="bib-copy">'
            f'<h3>{kind}<a href="appendix.html#{sid}" data-source="{sid}">{esc(title)}</a></h3>'
            f'<p class="bib-meta">{author}{esc(entry["date_or_version"])}；{esc(entry["locator"])}'
            f'<span class="bib-flag">{flag}</span></p></div></article>'
        )

    def columns(entries):
        # Keep source order while distributing text length across three columns.
        def visual_length(text):
            return sum(1 if ord(c) > 255 else .55 for c in text)
        weights = [max(1, math.ceil(visual_length(e['title']) / 31)) * 19.5
                   + max(1, math.ceil(visual_length(e['date_or_version'] + e['locator'] + e['author']) / 39)) * 16
                   + 9 for e in entries]
        prefix = [0]
        for weight in weights:
            prefix.append(prefix[-1] + weight)
        cuts = min(((a, b) for a in range(1, len(entries)-1) for b in range(a+1, len(entries))),
                   key=lambda ab: max(prefix[ab[0]], prefix[ab[1]]-prefix[ab[0]], prefix[-1]-prefix[ab[1]]))
        bounds = [0, *cuts, len(entries)]
        return '<div class="bibliography-columns">' + ''.join(
            '<div class="bibliography-list">' + ''.join(entry_html(e) for e in entries[a:b]) + '</div>'
            for a, b in zip(bounds, bounds[1:])) + '</div>'

    main_public = {sid for sid in main_ids if sid.startswith('D')}
    pages = [
        ('正文及逐字稿的公開文件', [r for r in records if r['id'] in main_public],
         f'正文及逐字稿引用 {len(main_public)} 項公開文件。證書、修讀及任教經驗列於下一頁。'),
        ('證書、經驗與延伸資料', [r for r in records if r['id'] not in main_public],
         f'正文個案資料 {len(main_ids-main_public)} 項（C 證書、O 經驗及轉述）、補充核證 {len(claim_ids)} 項、研究報告 {len(report_ids)} 項、時間線參考 {len(time_ids)} 項。'),
    ]
    appendix = []
    for i, (label, entries, description) in enumerate(pages, 1):
        appendix.append(dict(
            number=len(main_slides) + i, appendix_number=i, speaker='R', seconds=0,
            title=f'資料來源（{i}/2）｜{label}', era=f'參考資料 A{i:02d} · 全部{len(records)}項',
            body=f'<p class="bib-intro">{description}</p>' + columns(entries),
            refs=[e['id'] for e in entries],
            purpose='資料來源附頁，供查閱及答問，不計入正文17分鐘。',
            notes=[f'本頁列出{label}。點文件名稱可查看完整網址及引用限制。PDF中的文件名稱連至公開原文；私人資料沒有公開連結。'],
            transition='按需查閱下一頁來源，或返回正文。',
        ))
    metadata = dict(updated_on='2026-11-18', evidence_checked_through='2026-11-18',
                    main_slides=len(main_slides), appendix_slides=len(appendix),
                    total_slides=len(main_slides) + len(appendix), source_count=len(records),
                    groups=[dict(title=label, count=len(ids)) for label, ids, _ in groups], sources=records)
    (root / 'data/bibliography.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    with (root / 'data/bibliography.csv').open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0]))
        writer.writeheader()
        for record in records:
            writer.writerow({**record, 'used_in': json.dumps(record['used_in'], ensure_ascii=False)})
    return appendix, metadata
