import csv, math
from pathlib import Path
from statistics import mean, stdev
import numpy as np
from scipy.stats import wilcoxon

ROOT = Path(__file__).parent
OUT = ROOT / 'results_v050_final_campaign'
POLICIES = ['periodic','event_driven','send_on_delta','teen_like','distributed_edge','voi_baseline','dstep','dstep_payoff']
EVENTS = ['deterministic','physical_pulse','absent']
NODES = [20,50,100]


def read_csv(path):
    with path.open(newline='', encoding='utf-8') as f: return list(csv.DictReader(f))

def write_csv(path, rows):
    if not rows: return
    keys, seen = [], set()
    for r in rows:
        for k in r:
            if k not in seen: seen.add(k); keys.append(k)
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)

def fnum(row,key):
    v=row.get(key)
    if v in (None,'','None'): return None
    try: return float(v)
    except Exception: return None

def boot_ci(vals, B=5000, seed=1):
    a=np.asarray(vals,dtype=float)
    if len(a)==1:return float(a[0]),float(a[0])
    rng=np.random.default_rng(seed)
    means=np.empty(B)
    for i in range(B):means[i]=a[rng.integers(0,len(a),len(a))].mean()
    return tuple(map(float,np.percentile(means,[2.5,97.5])))

def holm(ps):
    m=len(ps); idx=sorted(range(m), key=lambda i:ps[i]); out=[1.0]*m; prev=0.0
    for rank,i in enumerate(idx):
        adj=min(1.0,(m-rank)*ps[i]); prev=max(prev,adj); out[i]=prev
    return out

def paired_stats(ref,base,key):
    rmap={(x['run']):x for x in ref}; bmap={(x['run']):x for x in base}
    common=sorted(set(rmap)&set(bmap),key=lambda x:int(x))
    dif=[]
    for k in common:
        a=fnum(rmap[k],key);b=fnum(bmap[k],key)
        if a is not None and b is not None:dif.append(a-b)
    if not dif:return None
    d=np.asarray(dif,float); sd=float(d.std(ddof=1)) if len(d)>1 else 0.0
    if np.allclose(d,0):p=1.0
    else:
        try:p=float(wilcoxon(d,zero_method='wilcox',alternative='two-sided').pvalue)
        except Exception:p=1.0
    lo,hi=boot_ci(d,B=5000,seed=990+len(dif))
    return {'paired_runs':len(dif),'delta_mean':float(d.mean()),'delta_sd':sd,'delta_ci_lo':lo,'delta_ci_hi':hi,'cohen_dz':float(d.mean()/sd) if sd>0 else 0.0,'p':p}

parts=sorted(OUT.glob('final_raw_*.csv'))
raw=[]
for p in parts:raw.extend(read_csv(p))
# Deduplicate defensively.
unique={}
for r in raw:unique[(r['event_model'],r['nodes'],r['policy'],r['run'])]=r
raw=list(unique.values())
write_csv(OUT/'final_raw.csv',raw)

metrics=['confirmation_f1','awareness_recall','dcr','network_false_alarm','false_confirmation_rate','false_awareness_rate','tx_packets','energy_mj','collisions','suppressed_tx','link_pdr','channel_loss_rate','collision_loss_rate','mean_alert_delay_s','mean_lead_time_s']
summary=[]
for e in EVENTS:
  for n in NODES:
    for p in POLICIES:
      rows=[r for r in raw if r['event_model']==e and int(float(r['nodes']))==n and r['policy']==p]
      rec={'event_model':e,'nodes':n,'policy':p,'runs':len(rows)}
      for mi,m in enumerate(metrics):
        vals=[fnum(r,m) for r in rows]; vals=[v for v in vals if v is not None and math.isfinite(v)]
        if vals:
          rec[m+'_mean']=mean(vals); rec[m+'_sd']=stdev(vals) if len(vals)>1 else 0.0
          lo,hi=boot_ci(vals,5000,seed=1000+mi+n+EVENTS.index(e)*100);rec[m+'_ci_lo']=lo;rec[m+'_ci_hi']=hi
      if e!='absent':
        rec['operational_success_rate']=mean([1.0 if (fnum(r,'confirmation_f1') or 0)>=0.95 and (fnum(r,'dcr') or 0)>=0.95 else 0.0 for r in rows])
      else:
        rec['false_alarm_free_rate']=mean([1.0 if (fnum(r,'network_false_alarm') or 0)==0 else 0.0 for r in rows])
      summary.append(rec)
write_csv(OUT/'final_summary.csv',summary)

# Paired dstep_payoff vs every comparator, fresh 6M seeds.
compare_metrics=['confirmation_f1','awareness_recall','dcr','network_false_alarm','tx_packets','energy_mj','collisions']
comp=[]
for e in EVENTS:
  for n in NODES:
    ref=[r for r in raw if r['event_model']==e and int(float(r['nodes']))==n and r['policy']=='dstep_payoff']
    for b in POLICIES:
      if b=='dstep_payoff':continue
      base=[r for r in raw if r['event_model']==e and int(float(r['nodes']))==n and r['policy']==b]
      rec={'event_model':e,'nodes':n,'comparison':f'dstep_payoff - {b}','baseline':b}
      for m in compare_metrics:
        st=paired_stats(ref,base,m)
        if st:
          for k,v in st.items():rec[f'{k}_{m}']=v
      comp.append(rec)
# Holm separately within each event/N/metric family across the 7 baselines.
for e in EVENTS:
  for n in NODES:
    group=[r for r in comp if r['event_model']==e and r['nodes']==n]
    for m in compare_metrics:
      good=[r for r in group if f'p_{m}' in r]
      if good:
        adj=holm([r[f'p_{m}'] for r in good])
        for r,a in zip(good,adj):r[f'p_holm_{m}']=a
write_csv(OUT/'final_paired_comparisons.csv',comp)

# Compact manuscript-facing report.
L=['# V0.50 FINAL FROZEN-POLICY CAMPAIGN','',
   'Fresh final-evaluation seeds: 6,000,000-series (not used for development or the 5,000,000-series hold-out).',
   'Design: 3 event models × 3 node counts × 8 policies × 30 paired runs = 2,160 simulations.',
   'Policies: Periodic, Event-driven, Send-on-Delta, TEEN-like, Distributed-edge, VoI baseline, original D-STEP, D-STEP Payoff-Aware.','',
   'All energy quantities below are modeled energy, not direct hardware energy measurements.','']
for e in EVENTS:
  L += [f'## {e}','']
  if e!='absent':
    L += ['| N | Policy | Conf. F1 | Awareness | DCR | TX | Energy mJ | Collisions | Op. success |','|---:|---|---:|---:|---:|---:|---:|---:|---:|']
    for r in summary:
      if r['event_model']==e:
        L.append(f"| {r['nodes']} | {r['policy']} | {r.get('confirmation_f1_mean',0):.4f} | {r.get('awareness_recall_mean',0):.4f} | {r.get('dcr_mean',0):.4f} | {r.get('tx_packets_mean',0):.1f} | {r.get('energy_mj_mean',0):.1f} | {r.get('collisions_mean',0):.1f} | {r.get('operational_success_rate',0):.3f} |")
  else:
    L += ['| N | Policy | Network false-alarm incidence | False-alarm-free runs | TX | Energy mJ |','|---:|---|---:|---:|---:|---:|']
    for r in summary:
      if r['event_model']==e:
        L.append(f"| {r['nodes']} | {r['policy']} | {r.get('network_false_alarm_mean',0):.4f} | {r.get('false_alarm_free_rate',0):.3f} | {r.get('tx_packets_mean',0):.1f} | {r.get('energy_mj_mean',0):.1f} |")
  L += ['']
L += ['## Payoff-Aware versus original D-STEP (paired)','', '| Event | N | ΔConf.F1 | ΔAwareness | ΔDCR | ΔTX | ΔEnergy mJ | Holm p(E) |','|---|---:|---:|---:|---:|---:|---:|---:|']
for r in comp:
  if r['baseline']=='dstep':
    L.append(f"| {r['event_model']} | {r['nodes']} | {r.get('delta_mean_confirmation_f1',0):+.4f} | {r.get('delta_mean_awareness_recall',0):+.4f} | {r.get('delta_mean_dcr',0):+.4f} | {r.get('delta_mean_tx_packets',0):+.2f} | {r.get('delta_mean_energy_mj',0):+.2f} | {r.get('p_holm_energy_mj',1):.4g} |")
L += ['', '## Integrity notes','',
      '- v0.50 policy parameters remained frozen; no tuning was performed using these 6,000,000-series results.',
      '- Event-absent runs are interpreted through false-alarm metrics, not F1/DCR.',
      '- Confirmation F1 and network awareness/DCR remain separate because the 5M hold-out exposed a real confirmation-versus-awareness trade-off.',
      '- Hardware TEST002 calibrates/validates the measured ESP32 link profile; the final large-scale campaign remains simulation-based.',
      '- Modeled energy must not be described as hardware-measured energy until direct current/time measurements are performed.']
(OUT/'V050_FINAL_CAMPAIGN_REPORT.md').write_text('\n'.join(L),encoding='utf-8')
print(f'raw rows={len(raw)} expected=2160')
print(OUT/'V050_FINAL_CAMPAIGN_REPORT.md')
