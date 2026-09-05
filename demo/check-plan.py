#!/usr/bin/env python3
"""Check static storyboard files. This does not measure a recorded video."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
out={'measurement':'planned caption holds, not recorded playback','recorded':False,'trial_target_cps':17,'event_numeric_limit_verified':False,'variants':{}}
plans={}
for variant in ('baseline','candidate'):
    d=json.loads((ROOT/f'{variant}.json').read_text());plans[variant]=d
    elapsed=0;rows=[]
    for i,s in enumerate(d['steps'],1):
        if s['action'] not in ('wait','click','fill','select','scroll','press','goto'):raise ValueError(f'Unknown action in {variant} step {i}')
        if not 1200<=s['hold_ms']<=15000:raise ValueError(f'Hold outside recorder bounds at step {i}')
        if not s['caption'].strip() or '\u2014' in s['caption']:raise ValueError(f'Empty or disallowed copy at step {i}')
        if s['action']!='wait' and not s.get('selector'):raise ValueError(f'Missing selector at step {i}')
        cps=len(s['caption'])/(s['hold_ms']/1000)
        rows.append({'step':i,'planned_start_ms':elapsed,'hold_ms':s['hold_ms'],'characters':len(s['caption']),'cps':round(cps,2),'exceeds_trial_target':cps>17});elapsed+=s['hold_ms']
    out['variants'][variant]={'step_count':len(rows),'hold_seconds':elapsed/1000,'max_cps':max(r['cps'] for r in rows),'over_target':sum(r['exceeds_trial_target'] for r in rows),'rows':rows}
without_caption=lambda steps:[{k:v for k,v in s.items() if k!='caption'} for s in steps]
if without_caption(plans['baseline']['steps'])!=without_caption(plans['candidate']['steps']):raise ValueError('Comparison changed more than captions')
if out['variants']['candidate']['hold_seconds']>=180:raise ValueError('No room remains in the working time budget for actual action latency')
if out['variants']['candidate']['over_target']:raise ValueError('Candidate has dense planned captions')
out['controls']={'same_actions':True,'same_hold_times':True,'only_captions_change':True,'actual_action_latency_seconds':None,'actual_video_seconds':None,'playback_verified':False}
(ROOT/'planned-metrics.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:{a:b for a,b in v.items() if a!='rows'} for k,v in out['variants'].items()},indent=2))
