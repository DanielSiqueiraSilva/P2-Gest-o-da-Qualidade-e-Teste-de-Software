"""Carga e estresse limitados e autorizados somente na aplicação local; sem terceiros."""
import os,sys,json,datetime,tempfile,shutil,subprocess,time,socket,threading,statistics,csv,math
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import urlopen
root=Path(__file__).resolve().parent.parent;code=root/'codigo'; ev=root/'evidencias';out=root/'relatorios'; out.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix='aurora-p2-load-') as td:
 db=Path(td)/'db.json';shutil.copy2(code/'data/db.json',db)
 s=socket.socket();s.bind(('127.0.0.1',0));port=s.getsockname()[1];s.close()
 proc=subprocess.Popen(['node','server.js'],cwd=code,env={**os.environ,'PORT':str(port),'DB_PATH':str(db)},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 target=f'http://127.0.0.1:{port}/api/products/produto-teste'
 for i in range(60):
  try:
   if urlopen(target,timeout=1).status==200:break
  except Exception:time.sleep(.1)
 stages=[('carga-baixa',2,3),('carga-media',6,3),('carga_referencia',12,3),('estresse',24,3),('recuperacao',2,3)]
 rows=[];results=[]
 try:
  for stage,concurrency,duration in stages:
   stop=threading.Event();samples=[];lock=threading.Lock()
   def worker():
    local=[]
    while not stop.is_set():
     begin=time.perf_counter();status='erro'
     try:
      with urlopen(target,timeout=3) as r:
       data=r.read();status=str(r.status)
       if not data:status='corpo-vazio'
     except Exception as e:status=type(e).__name__
     local.append((1000*(time.perf_counter()-begin),status))
    with lock:samples.extend(local)
   with ThreadPoolExecutor(max_workers=concurrency) as pool:
    start=time.perf_counter();futures=[pool.submit(worker) for _ in range(concurrency)];time.sleep(duration);stop.set()
    for f in futures:f.result()
    elapsed=time.perf_counter()-start
   latency=sorted(ms for ms,s in samples)
   ok=sum(s=='200' for ms,s in samples);total=len(samples); errors=total-ok
   p95=latency[min(len(latency)-1,math.ceil(.95*len(latency))-1)] if latency else None
   row={'cenario':stage,'concorrencia':concurrency,'duracao_segundos':round(elapsed,2),'requisicoes':total,'aprovadas':ok,'erros':errors,'taxa_erro_pct':round(errors/total*100,2) if total else None,'latencia_media_ms':round(statistics.mean(latency),2) if latency else None,'p95_ms':round(p95,2) if p95 else None,'latencia_max_ms':round(max(latency),2) if latency else None,'vazao_req_s':round(ok/elapsed,2)}
   results.append(row);print(stage,json.dumps(row,ensure_ascii=False),flush=True)
   for ms,status in samples: rows.append({'cenario':stage,'tempo_ms':round(ms,4),'status':status})
 finally:
  proc.terminate()
  try:proc.wait(timeout=7)
  except subprocess.TimeoutExpired:proc.kill()
 doc={'executado_em_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'ambiente':'localhost 127.0.0.1; cópia temporária da base didática; sem serviços de terceiros','endpoint':'GET /api/products/produto-teste','carga_limitada':True,'node':subprocess.check_output(['node','-v'],text=True).strip(),'stages':results}
 (out/'desempenho.json').write_text(json.dumps(doc,ensure_ascii=False,indent=2))
 with open(ev/'CT-CARGA-STRESS-amostras.csv','w',newline='') as f:
  wr=csv.DictWriter(f,fieldnames=['cenario','tempo_ms','status']);wr.writeheader();wr.writerows(rows)
 (ev/'CT-CARGA-STRESS-relatorio.txt').write_text('\n'.join(str(x) for x in results))
 print('SALVO',out/'desempenho.json')
