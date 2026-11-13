"""Compile the current Minimal Lab experimental JSON files into one Markdown report."""
import argparse
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
SCRIPTS = ['harness.py','task0_cal.py','task1_falsesharing.py','task2_scaling.py','task3a_roofline.py','task3b_gemm.py','task4_scheduling.py','build_report.py']

def fmt(x,n=4):
    return f'{x:.{n}f}' if isinstance(x,(int,float)) else str(x)

def table(headers,rows):
    def cell(x):return str(x).replace('|','\\|')
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(map(cell,row))+' |' for row in rows])+'\n'

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--id',type=int,required=True)
    ap.add_argument('--physical',type=int,default=10)
    ap.add_argument('--cpu',default='Intel Core i7-12650H')
    ap.add_argument('--l1',default='P-core: 48 KiB; E-core: 32 KiB (architectural reference)')
    ap.add_argument('--l2',default='9728 KiB (Windows reported)')
    ap.add_argument('--l3',default='24576 KiB (Windows reported)')
    ap.add_argument('--cache-line',default='64 bytes (architectural reference, not measured)')
    a=ap.parse_args()
    datasets={}
    for name in ['phase0','phase1','phase2','phase3a','phase3b','phase4']:
        f=BASE/(name+'.json')
        if not f.exists():raise SystemExit(f'Missing {f.name}. Run its task script first.')
        datasets[name]=json.loads(f.read_text(encoding='utf-8'))
        if datasets[name].get('student_id')!=a.id:raise SystemExit(f'Student ID mismatch in {f.name}')
        if datasets[name].get('quick'):raise SystemExit(f'{f.name} contains --quick output; full run required.')
    d0,d1,d2,d3a,d3b,d4=[datasets[n] for n in ['phase0','phase1','phase2','phase3a','phase3b','phase4']]
    hashes=[d0['verify'],d1['verify'],d2['verify'],d3b['verify'],d4['verify']]
    lines=[]
    def put(t=''):lines.append(t)
    put(f'# Minimal Python Parallel Systems Lab — Student ID {a.id}')
    put('**Performance Evaluation and Optimization in Parallel Computing — Ungraded Practice**')
    put('')
    put('## Phase 0 — Hardware topology and timer calibration')
    put(table(['Parameter','Measured or reference value'],[
      ('CPU',a.cpu),('Physical cores',a.physical),('Logical processors',d0['cpu_count']),('L1 data cache',a.l1),('L2 cache',a.l2),('L3 cache',a.l3),('Cache-line size',a.cache_line),('Python',d0['python']),('OS',d0['os']),('Clock reads',d0['clock_reads']),('Timer-call latency (ns)',fmt(d0['clock_latency_ns'],5))]))
    put('Cache L1 and cache-line values are architectural references until independently measured; they are not inferred from performance sweeps. The processor has 6 P-cores and 4 E-cores (16 logical threads).')
    put('')
    put('## Phase 1 — False sharing and Karp–Flatt')
    put(f'**Run configuration:** {d1["steps"]:,} RMW operations; 10 physical worker processes for the stride sweep.')
    put('')
    put('### Table 1A — Stride sensitivity')
    put(table(['p','Stride (words)','Offset (bytes)','Median (ms)','IQR (ms)','Throughput (Mops/s)'],[(r['p'],r['stride'],r['offset_bytes'],fmt(r['median_ms'],3),fmt(r['iqr_ms'],3),fmt(r['mops'],3)) for r in d1['stride_sweep']]))
    put('### Table 1B — Process scaling and effective serial fraction')
    put('S(p) = T(1)/T(p); E(p) = S(p)/p; e(p) = (1/S(p) - 1/p)/(1 - 1/p), for p >= 2.')
    put(table(['Stride','p','Median (ms)','Speedup','Efficiency','Karp–Flatt e(p)'],[(r['stride'],r['p'],fmt(r['median_ms'],3),fmt(r['speedup']),fmt(r['efficiency']),fmt(r['karp_flatt']) if r['karp_flatt'] is not None else 'N/A') for r in d1['scaling']]))
    times=d1['stride_sweep'];fastest=min(times,key=lambda r:r['median_ms'])
    put(f'**Interpretation:** The lowest observed median occurred at stride {fastest["stride"]}, {fastest["median_ms"]:.2f} ms. The x86-64 architectural cache-line distance is expected near stride 8 (64 bytes); the data should be used to determine whether a distinct drop was actually observed, rather than assuming it occurred. Process startup, OS scheduling, and interpreter overhead may obscure the effect. Compare e(p) across stride 1 and 16 in Table 1B.')
    put('')
    put('## Phase 2 — Strong scaling, weak scaling, and architectural inflection')
    put('### Strong scaling (fixed N = 1,200,000)')
    put(table(['p','N','Median (ms)','Serial stage (ms)','Speedup','Efficiency'],[(r['p'],r['N'],fmt(r['median_ms'],3),fmt(r['serial_ms'],3),fmt(r['speedup']),fmt(r['efficiency'])) for r in d2['strong']]))
    put('### Weak scaling (N = 200,000 × p)')
    put(table(['p','N','Median (ms)','Serial (ms)','Weak efficiency','alpha','Gustafson S'],[(r['p'],r['N'],fmt(r['median_ms'],3),fmt(r['serial_ms'],3),fmt(r['efficiency']),fmt(r['alpha']),fmt(r['gustafson'])) for r in d2['weak']]))
    put(f'**Amdahl:** s = Tserial(1)/Tstrong(1) = {d2["serial_fraction"]:.6f}; S(infinity) = {d2["amdahl_infinite"]:.4f}; S({d0["cpu_count"]}) theoretical = {d2["amdahl_at_logical"]:.4f}; observed = {d2["strong"][-1]["speedup"]:.4f}.')
    p=a.physical
    if len(d2['strong'])>p:
        x,y=d2['strong'][p-1]['speedup'],d2['strong'][p]['speedup']
        put(f'**Physical-to-logical boundary:** S({p})={x:.4f}, S({p+1})={y:.4f}; marginal change (S({p+1})-S({p}))/S({p})×100={(y-x)/x*100:.3f}%. This relative change is not a homogeneous SMT penalty; the CPU is hybrid.')
    put('**Interpretation:** Compare the measured p=1..Plog speedup/efficiency against ideal linear scaling and the Amdahl model. In weak scaling the Gustafson estimate describes a scaled workload, not measured speedup at fixed workload.')
    put('')
    put('## Phase 3 — Empirical Roofline and GEMM')
    put(table(['Roofline measurement','Value'],[('Memory copy size per buffer',f'{d3a["size_bytes_per_buffer"]:,} bytes'),('Copy time',f'{d3a["copy_seconds"]:.6f} s'),('Streaming bandwidth',f'{d3a["bandwidth_gbs"]:.6f} GB/s'),('Compute time',f'{d3a["compute_seconds"]:.6f} s'),('Python compute ceiling',f'{d3a["compute_gflops"]:.6f} GFLOP/s'),('Ridge I*',f'{d3a["ridge_flops_per_byte"]:.6f} FLOP/byte')]))
    put('### GEMM 256 × 256; tile sweep')
    put(table(['Variant','BS','Median (ms)','GFLOP/s','Tile footprint (bytes)'],[(r['variant'],r['bs'] or '—',fmt(r['median_ms'],3),fmt(r['gflops'],6),r['tile_bytes'] if r['tile_bytes'] is not None else '—') for r in d3b['rows']]))
    best=max(d3b['rows'][2:],key=lambda x:x['gflops']);naive=d3b['rows'][0];reordered=d3b['rows'][1]
    bw,peak=d3a['bandwidth_gbs'],d3a['compute_gflops']
    naive_bound=min(peak,bw*0.125); tiled_i=best['bs']/12; tiled_bound=min(peak,bw*tiled_i)
    put(f'**Best tile:** BS*={best["bs"]}, working set W=3×BS²×8={best["tile_bytes"]:,} bytes ({best["tile_bytes"]/1024:.2f} KiB), I_tiled≈BS/12={tiled_i:.4f} FLOP/byte.')
    put('**Indicative roofline:** R(I)=min(P_sustained, BW_sustained × I). Operational intensity 0.125 FLOP/byte is the assignment’s naive approximation; reordered intensity is not separately measured.')
    put(table(['Variant','Assumed intensity','Roofline bound (GFLOP/s)','Measured (GFLOP/s)','Attainment (%)'],[
      ('Naive','0.125',fmt(naive_bound,6),fmt(naive['gflops'],6),fmt(100*naive['gflops']/naive_bound,2)),
      ('Reordered','0.125 (proxy)',fmt(naive_bound,6),fmt(reordered['gflops'],6),fmt(100*reordered['gflops']/naive_bound,2)),
      (f'Tiled BS={best["bs"]}',fmt(tiled_i,4),fmt(tiled_bound,6),fmt(best['gflops'],6),fmt(100*best['gflops']/tiled_bound,2))]))
    put(f'**Correctness:** Maximum absolute difference against reordered GEMM across checked tiles = {d3b["max_error_vs_variant2"]:.3g}; requirement < 1e-9. Per-tile errors: {d3b.get("error_by_tile",{})}.')
    put('**Limitation:** Python-level spawn, indexing and interpreter overhead are included in these measurements; this roofline should not be interpreted as the native SIMD hardware ceiling.')
    put('')
    put('## Phase 4 — Irregular workloads and dynamic scheduling')
    put('N=8,000; K(i)=1+floor((i/40)^2); p=10 physical workers.')
    put(table(['Strategy','Chunk','Wall (ms)','Lambda','Worker times (ms)'],[(r['strategy'],r['chunk'] if r['chunk'] else '—',fmt(r['wall_ms'],3),fmt(r['lambda'],4),', '.join(fmt(x,1) for x in r['worker_ms'])) for r in d4['rows']]))
    block=d4['rows'][0];winner=min(d4['rows'][2:],key=lambda x:x['wall_ms'])
    put(f'**Best chunk C*:** {winner["chunk"]}. Compared with contiguous block scheduling, speedup = {block["wall_ms"]/winner["wall_ms"]:.4f}× and wall-time reduction = {100*(1-winner["wall_ms"]/block["wall_ms"]):.2f}%.')
    put('**Interpretation:** Lambda = max(worker_time)/mean(worker_time). Fine-grained dynamic chunks improve tail balance but require more synchronized counter claims; coarse chunks reduce lock operations yet may assign heavy tail work unevenly. Use the observed wall times and lambda to justify C*.')
    put('')
    put('## Verification hash summary (verbatim outputs)')
    put('```text\n'+'\n'.join(hashes)+'\n```')
    put('')
    put('## Raw terminal telemetry (unaltered JSON from scripts)')
    for name,dat in datasets.items():
        put(f'### {name}.json\n```json\n'+json.dumps(dat,indent=2)+'\n```\n')
    put('## Complete Python 3 source appendix')
    for name in SCRIPTS:
        put(f'### {name}\n```python\n'+(BASE/name).read_text(encoding='utf-8').rstrip()+'\n```\n')
    dest=BASE/f'lab_report_{a.id}.md'; dest.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(f'Created {dest.name} ({dest.stat().st_size} bytes)')

if __name__=='__main__':main()
