import os,json,datetime,tempfile,shutil,subprocess,time,socket,re
from pathlib import Path
from playwright.sync_api import sync_playwright
from urllib.request import urlopen
root=Path(__file__).resolve().parent.parent
code=root/'codigo'; ev=root/'evidencias'; results=[]
with tempfile.TemporaryDirectory(prefix='aurora-p2-ui-') as td:
 db=Path(td)/'db.json';shutil.copy2(code/'data/db.json',db)
 s=socket.socket();s.bind(('127.0.0.1',0));port=s.getsockname()[1];s.close()
 proc=subprocess.Popen(['node','server.js'],cwd=code,env={**os.environ,'PORT':str(port),'DB_PATH':str(db)},stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
 base=f'http://127.0.0.1:{port}'
 for attempt in range(80):
  try:
   if urlopen(base,timeout=1).status==200:break
  except Exception:time.sleep(.1)
 def check(id,description,fn):
  try:
   value=fn() or ''
   results.append(dict(id=id,description=description,status='aprovado',detail=str(value)))
   print('PASS',id,description,flush=True)
  except Exception as ex:
   results.append(dict(id=id,description=description,status='reprovado',detail=str(ex)[:700]))
   print('FAIL',id,str(ex)[:160],flush=True)
 try:
  with sync_playwright() as p:
   browser_options={'headless':True, 'args':['--no-sandbox','--disable-dev-shm-usage']}
   browser_path=os.environ.get('CHROMIUM_PATH') or ('/usr/bin/chromium' if Path('/usr/bin/chromium').exists() else None)
   if browser_path: browser_options['executable_path']=browser_path
   browser=p.chromium.launch(**browser_options)
   version=browser.version
   for width in [1280,390]:
    context=browser.new_context(viewport={'width':width,'height':850},device_scale_factor=1)
    page=context.new_page();page.set_default_timeout(25000)
    id='CT-COMP01' if width==1280 else 'CT-COMP02'
    def check_catalog():
     page.goto(base,wait_until='domcontentloaded');page.locator('[data-testid="product-card"]').first.wait_for(state='visible')
     count=page.locator('[data-testid="product-card"]').count();assert count>100,count
     page.screenshot(path=str(ev/(id+'.png')))
     return f'{count} produtos renderizados'
    check(id,f'Chromium {width}x850, catálogo',check_catalog)
    if results[-1]['status'] != 'aprovado':
     context.close()
     continue
    def check_search():
     page.locator('#search').fill('produto-teste')
     count=page.locator('[data-testid="product-card"]:visible').count();assert count==1,count
     assert page.locator('[data-testid="product-card"][data-product-id="produto-teste"]').is_visible()
     page.screenshot(path=str(ev/(id+'-busca.png')));return 'um produto correspondente'
    check('CT-E02' if width==1280 else 'CT-COMP03',f'Busca por texto ({width}px)',check_search)
    def check_category():
     page.locator('#search').fill('');select=page.locator('#category-filter')
     cat=select.locator('option').nth(1).get_attribute('value');select.select_option(cat)
     visible=page.locator('[data-testid="product-card"]:visible');count=visible.count();assert count>0
     values=visible.locator('.category').all_text_contents();assert all(v==cat for v in values),values[:3]
     page.screenshot(path=str(ev/(id+'-categoria.png')));return f'{cat}, {count} produtos'
    check('CT-E03' if width==1280 else 'CT-COMP04',f'Filtro de categoria ({width}px)',check_category)
    if width==1280:
     def name_label():
      page.goto(base+'/#cadastro');assert page.get_by_label('Nome',exact=True).count()==1
      page.screenshot(path=str(ev/'CT-AC01.png'));return 'label for correto'
     check('CT-AC01','Rótulo acessível Nome',name_label)
     def keyboard():
      page.goto(base+'/#catalogo');page.locator('#search').fill('produto-teste')
      add=page.locator('[data-testid="product-card"][data-product-id="produto-teste"] button')
      add.focus();assert add.evaluate('(e)=>document.activeElement===e')
      page.keyboard.press('Enter');page.wait_for_function("document.getElementById('cart-count').textContent==='1'")
      page.screenshot(path=str(ev/'CT-AC02.png'));return 'Enter no botão adiciona item'
     check('CT-AC02','Ação acessível ao teclado',keyboard)
     def cart():
      page.goto(base+'/#carrinho');page.locator('[data-testid="cart-subtotal"]').wait_for()
      text=page.locator('[data-testid="cart-subtotal"]').text_content();assert '150,00' in text,text
      page.screenshot(path=str(ev/'CT-E04.png'));return 'subtotal R$ 150,00'
     check('CT-E04','Carrinho com item e total',cart)
     def focus():
      page.goto(base+'/#cadastro');el=page.get_by_label('Nome',exact=True);el.focus()
      outline=el.evaluate('(e)=>getComputedStyle(e).outlineWidth');assert float(outline.replace('px',''))>0,outline
      return outline
     check('CT-AC03','Foco visual identificado',focus)
     def register_error():
      page.goto(base+'/#cadastro');page.get_by_label('Nome',exact=True).fill('A');page.get_by_label('E-mail',exact=True).fill('aluno@teste.com');page.get_by_label('Senha',exact=True).fill('Senha123!')
      page.locator('#register-form button[type="submit"]').click()
      page.wait_for_function("document.querySelector('#register-error').textContent.length>0")
      text=page.locator('#register-error').text_content();assert 'Nome' in text,text
      page.screenshot(path=str(ev/'CT-AC04.png'));return text
     check('CT-AC04','Erro de cadastro específico',register_error)
     def cart_empty():
      page.goto(base+'/#catalogo');page.evaluate("localStorage.removeItem('aurora-cart');localStorage.removeItem('aurora-coupon')");page.reload();page.goto(base+'/#carrinho')
      page.wait_for_function("document.getElementById('cart-content').textContent.includes('vazio')")
      assert page.locator('#cart-content a[href="#catalogo"]').count()==1
      page.screenshot(path=str(ev/'CT-AC05.png'));return 'mensagem de vazio e retorno ao catálogo'
     check('CT-AC05','Carrinho vazio com orientação',cart_empty)
    context.close()
   browser.close()
 finally:
  proc.terminate()
  try:proc.wait(timeout=10)
  except subprocess.TimeoutExpired:proc.kill()
 (ev/'CT-INTERFACE.json').write_text(json.dumps({'date':datetime.datetime.now(datetime.timezone.utc).isoformat(),'browser':'Chromium headless','browser_version':locals().get('version','indisponível'),'results':results},ensure_ascii=False,indent=2))
 (ev/'CT-INTERFACE.log').write_text('\n'.join(f"{c['id']} {c['status']} {c['detail']}" for c in results)+'\n')
 print('RESUMO',sum(x['status']=='aprovado' for x in results),'aprovados',sum(x['status']!='aprovado' for x in results),'reprovados')
