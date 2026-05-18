# -*- coding: utf-8 -*-
import json
import traceback

f = open('data/typical_cases.json', 'r', encoding='utf-8')
raw = f.read()
print('文件大小:', len(raw), '字节')
print('前300字符:', raw[:300])
print('---')
try:
    d = json.loads(raw)
    print('JSON解析成功')
    print('数据结构:', type(d))
    if isinstance(d, list):
        print('案例数量:', len(d))
        for i, c in enumerate(d[:3]):
            print(f'  案例{i+1}: title={c.get("title","无")} | category={c.get("category","无")}')
    elif isinstance(d, dict):
        cases = d.get('cases', d.get('typical_cases', d.get('data', [])))
        print('案例数量:', len(cases))
        for i, c in enumerate(cases[:3]):
            print(f'  案例{i+1}: title={c.get("title","无")} | category={c.get("category","无")}')
    else:
        print('未知结构')
except Exception as e:
    print('JSON解析失败:', e)
    traceback.print_exc()
