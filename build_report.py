import argparse, json, pathlib
p=argparse.ArgumentParser();p.add_argument('--id',type=int,required=True);p.add_argument('--physical',type=int,required=True);p.add_argument('--cpu',default='[MEASURE WITH WINDOWS POWERSHELL]');p.add_argument('--l1',default='[MEASURE]');p.add_argument('--l2',default='[MEASURE]');p.add_argument('--l3',default='[MEASURE]');p.add_argument('--cache-line',default='[MEASURE]');args=p.parse_args()

def load(n):
    try:return json.loads(pathlib.Path(f'phase{n}.json').read_text())
    except FileNotFoundError:return {}
results={n:load(n) for n in ['0','1','2','3a','3b','4']}
lines=[f'# Parallel Computing Lab — {args.id}','', '## Phase 0 — Hardware baseline','',f'- CPU model: {args.cpu}',f'- Physical cores: {args.physical}',f'- Logical cores: {results["0"].get("cpu_count","[MEASURE]")}',f'- L1d: {args.l1}',f'- L2: {args.l2}',f'- L3: {args.l3}',f'- Cache line: {args.cache_line}',f'- Python and OS: {results["0"].get("python","[MEASURE]")} / {results["0"].get("os","[MEASURE]")}', '']
for key,title in [('0','Phase 0 — Clock calibration'),('1','Phase 1 — False sharing and Karp-Flatt'),('2','Phase 2 — Strong and weak scaling'),('3a','Phase 3A — Roofline ceilings'),('3b','Phase 3B — GEMM'),('4','Phase 4 — Scheduling')]:
    r=results[key];lines.extend([f'## {title}',''])
    if not r:lines.append('**NOT MEASURED: run the corresponding Python script on your laptop.**')
    else:
        if r.get('quick'):lines.append('**QUICK TEST DATA ONLY — NOT VALID FOR FINAL SUBMISSION.**')
        lines.extend(['```json',json.dumps(r,indent=2),'```'])
    if r.get('verify'):lines.extend(['',f'`{r["verify"]}`'])
    lines.append('')
lines+=['## Hardware-grounded analysis — fill after real runs','', '### Phase 1 — Observed cache-line boundary and e(p) trend','[Interpret tables using your actual measured values.]','','### Phase 2 — Amdahl vs Gustafson and SMT transition','[Calculate marginal speedup drop across physical-to-logical boundary.]','','### Phase 3 — Measured roofline and optimal tile','[Compare optimum tile footprint with L1d/L2 and calculate roofline efficiency.]','','### Phase 4 — Dynamic scheduling trade-off','[Compare lock contention and load imbalance for all C values.]','','## Python source appendix','']
for name in ['harness.py','task0_cal.py','task1_falsesharing.py','task2_scaling.py','task3a_roofline.py','task3b_gemm.py','task4_scheduling.py']:
    f=pathlib.Path(name)
    if f.exists():lines.extend([f'### {name}','```python',f.read_text(),'```',''])
path=pathlib.Path(f'lab_report_{args.id}.md');path.write_text('\n'.join(lines),encoding='utf-8');print(f'Created {path}')
