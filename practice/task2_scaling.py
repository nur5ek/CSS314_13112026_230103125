import argparse, json, math, multiprocessing as mp, time
from statistics import median
from harness import emit_verify_tag

def part_kernel(arg):
    start,end=arg; z=0.0
    for i in range(start,end):
        x=(i+1)*0.000001
        v=x
        for k in range(30): v=v*1.0000001+math.sin(v+0.001*k)*0.00001
        z+=v
    return z

def serial_stage(n):
    z=0.0
    for i in range(max(1,n//20)):
        v=(i+1)*0.000001
        for k in range(5):z+=math.sin(v+k)*math.sqrt(v+k+1)
    return z

def timed(pool,p,n,runs):
    regions=[(n*t//p,n*(t+1)//p) for t in range(p)]
    samples=[];serials=[]
    for _ in range(runs):
        st=time.perf_counter_ns(); serial_stage(n);serials.append((time.perf_counter_ns()-st)/1e6)
        pool.map(part_kernel,regions)
        samples.append((time.perf_counter_ns()-st)/1e6)
    return median(samples),median(serials)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--id',type=int,required=True);ap.add_argument('--physical',type=int,required=True);ap.add_argument('--quick',action='store_true');a=ap.parse_args()
    logical=mp.cpu_count();strong_n=16000 if a.quick else 1_200_000;weak_base=2500 if a.quick else 200_000
    strong=[];weak=[]
    for p in range(1,logical+1):
        with mp.Pool(p) as pool:
            s,sa=timed(pool,p,strong_n,1 if a.quick else 3)
            w,wa=timed(pool,p,weak_base*p,1 if a.quick else 3)
        strong.append({'p':p,'N':strong_n,'median_ms':s,'serial_ms':sa});weak.append({'p':p,'N':weak_base*p,'median_ms':w,'serial_ms':wa})
        print(f'p={p} strong={s:.2f} ms weak={w:.2f} ms',flush=True)
    t1=strong[0]['median_ms'];w1=weak[0]['median_ms']
    for r in strong:
        r['speedup']=t1/r['median_ms'];r['efficiency']=r['speedup']/r['p']
    for r in weak:
        r['efficiency']=w1/r['median_ms'];r['alpha']=r['serial_ms']/r['median_ms'];r['gustafson']=r['p']-r['alpha']*(r['p']-1)
    frac=strong[0]['serial_ms']/t1
    result={'student_id':a.id,'quick':a.quick,'strong':strong,'weak':weak,'serial_fraction':frac,'amdahl_infinite':1/frac,'amdahl_at_logical':1/(frac+(1-frac)/logical),'verify':emit_verify_tag('PHASE2',a.id,strong[-1]['speedup'],weak[-1]['gustafson'])}
    open('phase2.json','w').write(json.dumps(result,indent=2));print(result['verify'])
if __name__=='__main__':mp.freeze_support();main()

