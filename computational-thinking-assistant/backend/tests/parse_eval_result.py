# -*- coding: utf-8 -*-
import json
from pathlib import Path

p = Path("tests/tmp_confidence_eval_output_utf8.txt")
text = p.read_text(encoding="utf-8", errors="ignore")
start_tag = "=== EVAL_JSON_BEGIN ==="
end_tag = "=== EVAL_JSON_END ==="

start = text.find(start_tag)
end = text.find(end_tag)
if start < 0 or end < 0 or end <= start:
    raise SystemExit("未找到JSON标记，无法提取")

payload = text[start + len(start_tag):end].strip()
arr = json.loads(payload)
arr.sort(key=lambda x: x.get("idx", 0))

print("idx\tmode\tconfidence\tmax_score\traw\tused")
for r in arr:
    print(f"{r.get('idx')}\t{r.get('mode')}\t{r.get('confidence_mode')}\t{r.get('max_score')}\t{r.get('raw_result_count')}\t{r.get('used_result_count')}")

# 输出分组统计（按题号区间）
for label, lo, hi in [("高",1,10),("中",11,20),("低",21,30)]:
    sub = [x for x in arr if lo <= int(x.get('idx', 0)) <= hi]
    rag_n = sum(1 for x in sub if x.get('mode') == 'rag')
    high_n = sum(1 for x in sub if x.get('confidence_mode') == 'high')
    med_n = sum(1 for x in sub if x.get('confidence_mode') == 'medium')
    low_n = sum(1 for x in sub if x.get('confidence_mode') == 'low')
    print(f"GROUP[{label}] rag={rag_n}/{len(sub)} high={high_n} medium={med_n} low={low_n}")
