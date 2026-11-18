'use strict';
const test=require('node:test');const assert=require('node:assert/strict');const fs=require('fs');const os=require('os');const path=require('path');
const {createServer}=require('../server');const {openDatabase}=require('../src/persistence/database');
const tmp=fs.mkdtempSync(path.join(os.tmpdir(),'aurora-p2-'));const dbPath=path.join(tmp,'db.json');
fs.copyFileSync(path.join(__dirname,'../data/db.json'),dbPath);
const db=openDatabase(dbPath);const server=createServer(db);let base,clientToken,clientBToken,adminToken,createdOrder;
const address={street:'Rua Exemplo',number:'12',district:'Centro',city:'Saquarema',state:'RJ',zip:'28990-000'};
async function req(method,url,data,token){const response=await fetch(base+url,{method,headers:{...(data?{'Content-Type':'application/json'}:{}),...(token?{Authorization:`Bearer ${token}`}:{})},body:data?JSON.stringify(data):undefined});let value;try{value=await response.json()}catch{value=null}return {status:response.status,body:value}}
async function login(email){const r=await req('POST','/api/auth/login',{email,password:'SenhaDidatica123!'});assert.equal(r.status,200);return r.body.token;}
test.before(async()=>{await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));base=`http://127.0.0.1:${server.address().port}`;clientToken=await login('cliente-a@loja.test');clientBToken=await login('cliente-b@loja.test');adminToken=await login('admin@loja.test')});
test.after(async()=>{await new Promise(resolve=>server.close(resolve));fs.rmSync(tmp,{recursive:true,force:true})});
test('CT-F01 / RF-01 cadastro com dados fictícios',async()=>{const r=await req('POST','/api/auth/register',{name:'Aluno Teste',email:`aluno-p2-${process.pid}@teste.com`,password:'Senha123!'});assert.equal(r.status,201);assert.ok(r.body.token)});
test('CT-F02 / RF-02 autenticação e sessão',async()=>{const r=await req('GET','/api/auth/me',null,clientToken);assert.equal(r.status,200);assert.equal(r.body.user.email,'cliente-a@loja.test')});
test('CT-F03 / RF-03 catálogo contém atributos',async()=>{const r=await req('GET','/api/products');assert.equal(r.status,200);assert.ok(r.body.length>0);const p=r.body.find(p=>p.id==='produto-teste');assert.ok(p);for(const k of ['name','description','category','price','stock'])assert.ok(Object.hasOwn(p,k))});
test('CT-APISUP01 / RF-03 catálogo possui categorias para o filtro',async()=>{const r=await req('GET','/api/products');assert.equal(r.status,200);assert.ok(r.body.some(p=>p.category));});
test('CT-F05 / RF-05 cotação com duas unidades',async()=>{const r=await req('POST','/api/cart/quote',{items:[{productId:'produto-teste',quantity:2}]});assert.equal(r.status,200);assert.deepEqual([r.body.subtotal,r.body.discount,r.body.shipping,r.body.total],[300,30,0,270]);});
test('CT-F06 / RF-06 estoque consultável',async()=>{const r=await req('GET','/api/products/produto-teste');assert.equal(r.status,200);assert.equal(r.body.stock,5)});
test('CT-F07 / RF-07 cupom VINTE prevalece sobre automático',async()=>{const r=await req('POST','/api/cart/quote',{items:[{productId:'produto-teste',quantity:2}],couponCode:'VINTE'});assert.equal(r.status,200);assert.equal(r.body.discount,60);assert.equal(r.body.total,240)});
test('CT-F08 / RF-08 endereço obrigatório (negativo)',async()=>{const r=await req('POST','/api/checkout',{items:[{productId:'produto-teste',quantity:1}],address:{street:'Rua ABC'}},clientToken);assert.equal(r.status,400);assert.match(r.body.error,/endere[cç]o/i)});
test('CT-F09 / RF-09 finalizar pedido com endereço e persistência',async()=>{const r=await req('POST','/api/checkout',{items:[{productId:'produto-teste',quantity:2,unitPrice:0.01}],address},clientToken);assert.equal(r.status,201);createdOrder=r.body.order;assert.equal(createdOrder.subtotal,300);assert.equal(createdOrder.discount,30);assert.equal(createdOrder.total,270);assert.equal(createdOrder.address.city,'Saquarema');assert.equal(db.findProduct('produto-teste').stock,3);const reopened=openDatabase(dbPath);assert.equal(reopened.findOrder(createdOrder.id).id,createdOrder.id);assert.equal(reopened.findProduct('produto-teste').stock,3)});
test('CT-I01 / RF-06,RF-09 estoque alterado após compra e persistido',async()=>{assert.equal(db.findProduct('produto-teste').stock,3);assert.ok(openDatabase(dbPath).findOrder(createdOrder.id));});
test('CT-I02 / RF-09,RF-10 pedido criado recuperável pela API',async()=>{const r=await req('GET',`/api/orders/${createdOrder.id}`,null,clientToken);assert.equal(r.status,200);assert.equal(r.body.id,createdOrder.id)});
test('CT-F10 / RF-10 histórico de pedidos próprios',async()=>{const r=await req('GET','/api/orders',null,clientToken);assert.equal(r.status,200);assert.ok(r.body.some(o=>o.id===createdOrder.id));assert.ok(r.body.every(o=>o.userId==='cliente-a'))});
test('CT-N01 / RN-03 cotação negativa rejeitada',async()=>{const r=await req('POST','/api/cart/quote',{items:[{productId:'produto-teste',quantity:-1}]});assert.equal(r.status,400)});
test('CT-N02 / RN-03 acima do estoque rejeitado',async()=>{const r=await req('POST','/api/cart/quote',{items:[{productId:'produto-teste',quantity:99}]});assert.equal(r.status,400)});
test('CT-N03 / RN-04 cupom vencido rejeitado',async()=>{const r=await req('POST','/api/cart/quote',{items:[{productId:'produto-teste',quantity:1}],couponCode:'ANTIGO'});assert.equal(r.status,400)});
test('CT-S01 / RN-10 cliente B não acessa pedido A',async()=>{const r=await req('GET',`/api/orders/${createdOrder.id}`,null,clientBToken);assert.equal(r.status,404)});
test('CT-S02 / RN-11 alteração administrativa sem token rejeitada',async()=>{const r=await req('PUT','/api/admin/products/produto-teste',{price:0.01});assert.equal(r.status,401)});
test('CT-S03 / RN-11 alteração administrativa com cliente rejeitada',async()=>{const r=await req('PUT','/api/admin/products/produto-teste',{price:0.01},clientToken);assert.equal(r.status,403)});
test('CT-S04 / RN-12 entrada administrativa negativa rejeitada',async()=>{const r=await req('PUT','/api/admin/products/produto-teste',{stock:-100},adminToken);assert.equal(r.status,400)});
test('CT-R01 / RN-09 repetição imediata não cria dois pedidos',async()=>{const body={items:[{productId:'produto-teste',quantity:1}],address:{...address,number:'300'}};const first=await req('POST','/api/checkout',body,clientToken);const second=await req('POST','/api/checkout',body,clientToken);assert.equal(first.status,201);assert.equal(second.status,201);assert.equal(first.body.order.id,second.body.order.id)});
test('CT-R02 / RN-12 preço enviado pelo navegador não altera cálculo',async()=>{const r=await req('POST','/api/cart/quote',{items:[{productId:'produto-teste',quantity:1,unitPrice:0.01}]});assert.equal(r.status,200);assert.equal(r.body.subtotal,150)});
test('CT-R03 / RN-10 histórico não expõe pedidos de outro cliente',async()=>{const r=await req('GET','/api/orders',null,clientBToken);assert.equal(r.status,200);assert.ok(r.body.every(o=>o.userId==='cliente-b'))});
test('CT-CP01 / caixa-preta equivalência + valor-limite do desconto (199,99/200/200,01)',async()=>{
 const r=await req('POST','/api/admin/products',{name:'Produto Limiar Desconto',price:199.99,stock:10,category:'Testes'},adminToken);assert.equal(r.status,201);const id=r.body.id;
 async function quote(price){const patch=await req('PUT',`/api/admin/products/${id}`,{price},adminToken);assert.equal(patch.status,200);const q=await req('POST','/api/cart/quote',{items:[{productId:id,quantity:1}]});assert.equal(q.status,200);return q.body;}
 assert.equal((await quote(199.99)).discount,0);
 assert.equal((await quote(200)).discount,20);
 assert.equal((await quote(200.01)).discount,20);
});
test('CT-CP02 / caixa-preta equivalência + valor-limite do frete (299,99/300/300,01)',async()=>{
 const r=await req('POST','/api/admin/products',{name:'Produto Limiar Frete',price:299.99,stock:10,category:'Testes'},adminToken);assert.equal(r.status,201);const id=r.body.id;
 async function quote(price){const patch=await req('PUT',`/api/admin/products/${id}`,{price},adminToken);assert.equal(patch.status,200);const q=await req('POST','/api/cart/quote',{items:[{productId:id,quantity:1}]});assert.equal(q.status,200);return q.body;}
 assert.equal((await quote(299.99)).shipping,18.5);
 assert.equal((await quote(300)).shipping,0);
 assert.equal((await quote(300.01)).shipping,0);
});
test('CT-F02B / RF-02 logout encerra a sessão do cliente',async()=>{
 const token=await login('cliente-a@loja.test');
 const out=await req('POST','/api/auth/logout',{},token);
 assert.equal(out.status,200);
 const after=await req('GET','/api/auth/me',null,token);
 assert.equal(after.status,401);
});
