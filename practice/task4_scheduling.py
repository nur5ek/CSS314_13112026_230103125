import argparse, json, math, multiprocessing as mp, time
from statistics import median
from harness import emit_verify_tag
CHUNKS=[1,8,64,512]

def do_item(i,quick):
    repeats=1+(i*i)//1600
    if quick:repeats=max(1,repeats//1000)
    v=0.0
    for k in range(repeats):v+=math.sin(k*0.0001)*math.cos(k*0.0002)+math.sqrt(k+1)*0.00000001
    return v

def worker(t,p,n,strategy,chunk,queue_index,lock,active,quick):
    start=time.perf_counter_ns();total=0.0
    if strategy=='block':
        for i in range(t*n//p,(t+1)*n//p):total+=do_item(i,quick)
    elif strategy=='cyclic':
        for i in range(t,n,p):total+=do_item(i,quick)
    else:
        while True:
            with lock:
                start_idx=queue_index.value;queue_index.value+=chunk
            if start_idx>=n:break
            for i in range(start_idx,min(n,start_idx+chunk)):total+=do_item(i,quick)
    active[t]=(time.perf_counter_ns()-start)/1e6

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--id',type=int,required=True);ap.add_argument('--physical',type=int,required=True);ap.add_argument('--quick',action='store_true');a=ap.parse_args()
    n=800 if a.quick else 8000;rows=[]
    for strategy,chunk in [('block',0),('cyclic',0)]+[('dynamic',c) for c in CHUNKS]:
        counter=mp.Value('i',0);lock=mp.Lock();times=mp.Array('d',a.physical)
        st=time.perf_counter_ns()
        ps=[mp.Process(target=worker,args=(t,a.physical,n,strategy,chunk,counter,lock,times,a.quick)) for t in range(a.physical)]
        for p in ps:p.start()
        for p in ps:p.join()
        if any(p.exitcode for p in ps):raise RuntimeError('worker failure')
        elapsed=(time.perf_counter_ns()-st)/1e6
        vals=list(times);lam=max(vals)/(sum(vals)/len(vals)) if sum(vals)>0 else float('nan')
        row={'strategy':strategy,'chunk':chunk,'wall_ms':elapsed,'lambda':lam,'worker_ms':vals}
        rows.append(row);print(row,flush=True)
    best=min(rows[2:],key=lambda x:x['wall_ms'])
    out={'student_id':a.id,'quick':a.quick,'n':n,'rows':rows,'best_chunk':best['chunk'],'verify':emit_verify_tag('PHASE4',a.id,rows[0]['wall_ms'],best['wall_ms'])}
    open('phase4.json','w').write(json.dumps(out,indent=2));print(out['verify'])
if __name__=='__main__':mp.freeze_support();main()

