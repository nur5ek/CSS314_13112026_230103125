import argparse, json, multiprocessing as mp, time
from multiprocessing import shared_memory
from statistics import median
from harness import emit_verify_tag
TILES=[4,8,12,16,24,32,48,64,96,128]

def gemm_worker(names,n,lo,hi,variant,bs):
    blocks=[shared_memory.SharedMemory(name=x) for x in names]
    a,b,c=[sh.buf.cast('d') for sh in blocks]
    try:
        if variant==1:
            for i in range(lo,hi):
                for j in range(n):
                    val=0.0
                    for k in range(n):val+=a[i*n+k]*b[k*n+j]
                    c[i*n+j]=val
        elif variant==2:
            for i in range(lo,hi):
                for k in range(n):
                    aik=a[i*n+k]
                    for j in range(n):c[i*n+j]+=aik*b[k*n+j]
        else:
            for ii in range(lo,hi,bs):
                for jj in range(0,n,bs):
                    for kk in range(0,n,bs):
                        for i in range(ii,min(ii+bs,hi)):
                            for k in range(kk,min(kk+bs,n)):
                                aik=a[i*n+k]
                                for j in range(jj,min(jj+bs,n)):
                                    c[i*n+j]+=aik*b[k*n+j]
    finally:
        del a,b,c
        for sh in blocks:sh.close()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--id',type=int,required=True);ap.add_argument('--physical',type=int,required=True);ap.add_argument('--quick',action='store_true');a=ap.parse_args()
    n=48 if a.quick else 384
    blocks=[shared_memory.SharedMemory(create=True,size=n*n*8) for _ in range(3)]
    try:
        av,bv,cv=[s.buf.cast('d') for s in blocks]
        for i in range(n*n):av[i]=(i%17-8)/17;bv[i]=(i%13-6)/13
        def run(variant,bs):
            for i in range(n*n):cv[i]=0.0
            names=[s.name for s in blocks]
            st=time.perf_counter_ns()
            ps=[mp.Process(target=gemm_worker,args=(names,n,n*t//a.physical,n*(t+1)//a.physical,variant,bs)) for t in range(a.physical)]
            for p in ps:p.start()
            for p in ps:p.join()
            if any(p.exitcode for p in ps):raise RuntimeError('GEMM worker failed')
            elapsed=(time.perf_counter_ns()-st)/1e6
            return elapsed
        rows=[]
        for variant,bs in [(1,0),(2,0)]+[(3,b) for b in TILES]:
            samples=[run(variant,bs) for _ in range(1 if a.quick else 3)]
            med=median(samples)
            row={'variant':variant,'bs':bs,'median_ms':med,'gflops':2*n**3/(med*1e6),'tile_bytes':3*bs*bs*8 if bs else None}
            rows.append(row);print(row,flush=True)
            if variant==2:reference=list(cv)
            if variant==3 and bs==TILES[0]:diff=max(abs(cv[i]-reference[i]) for i in range(n*n))
        best=max(rows[2:],key=lambda r:r['gflops'])
        out={'student_id':a.id,'quick':a.quick,'n':n,'rows':rows,'max_error_vs_variant2':diff,'best_bs':best['bs'],'verify':emit_verify_tag('PHASE3',a.id,rows[0]['gflops'],best['gflops'])}
        open('phase3b.json','w').write(json.dumps(out,indent=2));print(out['verify'])
        del av,bv,cv
    finally:
        for sh in blocks:sh.close();sh.unlink()
if __name__=='__main__':mp.freeze_support();main()
