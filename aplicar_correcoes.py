from pathlib import Path
p=Path('/mnt/data/Entrega_P2_Loja_Aurora/codigo')
def upd(fn,a,b):
 f=p/fn;t=f.read_text();assert a in t, (fn,a[:90]);f.write_text(t.replace(a,b))
upd('src/domain/discount.js','Number(subtotal) > AUTO_DISCOUNT_MIN_SUBTOTAL','Number(subtotal) >= AUTO_DISCOUNT_MIN_SUBTOTAL')
upd('src/domain/shipping.js','  const considered = Math.trunc((cents * 9) / 10);\n  if (considered >= toCents(FREE_SHIPPING_MIN_SUBTOTAL)) {','  if (cents >= toCents(FREE_SHIPPING_MIN_SUBTOTAL)) {')
upd('src/domain/quantity.js','  if (value === 0) {\n    return { ok: false, message: "A quantidade não pode ser zero." };','  if (value <= 0) {\n    return { ok: false, message: "A quantidade deve ser positiva." };')
upd('src/domain/money.js','  const resultCents = Math.trunc((cents * Number(percent)) / 100);','  const resultCents = Math.round((cents * Number(percent)) / 100 + Number.EPSILON);')
upd('src/domain/orderTotals.js','  total: fromCents(toCents(subtotal) + toCents(shipping)),','  total: fromCents(toCents(subtotal) - toCents(discount) + toCents(shipping)),')
(p/'src/domain/coupon.js').write_text('''"use strict";
const { now } = require("./clock");
const { toCents, fromCents, percentOf } = require("./money");
function evaluateCoupon(coupon) {
  if (!coupon || coupon.active === false || !["percent", "fixed"].includes(coupon.type) || !Number.isFinite(Number(coupon.value)) || Number(coupon.value)<0) {
    return {ok:false,message:"Cupom inválido."};
  }
  if (coupon.expiresAt) {
    const stamp=String(coupon.expiresAt);
    const expiry=stamp.length===10 ? new Date(stamp+"T23:59:59.999Z") : new Date(stamp);
    if (Number.isNaN(expiry.getTime()) || now().getTime()>expiry.getTime()) return {ok:false,message:"Cupom vencido ou inválido."};
  }
  return {ok:true};
}
function couponBenefit(subtotal,coupon){
 if(!coupon) return 0;
 if(coupon.type==="percent") return percentOf(subtotal,coupon.value);
 if(coupon.type==="fixed") return fromCents(Math.min(toCents(coupon.value),toCents(subtotal)));
 return 0;
}
module.exports={evaluateCoupon,couponBenefit};
''')
(p/'src/domain/address.js').write_text('''"use strict";
const FIELDS=["street","number","district","city","state","zip"];
function normalizeAddress(input){
 const source=input && typeof input==="object" ? input : {};
 const address={};
 for(const field of FIELDS) address[field]=String(source[field]??"").trim();
 if(FIELDS.some((field)=>!address[field]))return {ok:false,message:"Preencha o endereço de entrega completo."};
 if(!/^[A-Za-z]{2}$/.test(address.state)|| !/^\\d{5}-?\\d{3}$/.test(address.zip)) return {ok:false,message:"UF ou CEP inválido."};
 address.state=address.state.toUpperCase();
 return {ok:true,address};
}
module.exports={normalizeAddress,FIELDS};
''')
# Persistence: rely on consistent in-memory state and atomic rewrite, not stale on-disk orders
f=p/'src/persistence/database.js';s=f.read_text();start=s.index('  function persist() {');end=s.index('  function publicUser',start)
s=s[:start]+'''  function persist() {
    const temporary = `${filePath}.tmp`;
    fs.writeFileSync(temporary, JSON.stringify(state, null, 2));
    fs.renameSync(temporary, filePath);
  }

'''+s[end:]
s=s.replace('      state.orders.push(order);\n','      state.orders.push(order);\n      persist();\n')
s=s.replace('      return readFile(filePath).orders.map((order) => ({','      return state.orders.map((order) => ({')
s=s.replace('      persist();\n      return { ...product };','      persist();\n      return { ...product };')
f.write_text(s)
# checkout: trusted prices, quantity/stock checks, addr, stock on successful order
f=p/'src/services/checkout.js';s=f.read_text()
s=s.replace('  const items = (body.items || [])','  const items = (Array.isArray(body.items) ? body.items : [])')
start=s.index('function resolveUnitPrice(');end=s.index('function placeOrder(',start)
s=s[:start]+s[end:]
s=s.replace('    const unitPrice = resolveUnitPrice(product, item.unitPrice);','''    if (!Number.isInteger(Number(item.quantity)) || Number(item.quantity)<=0 || Number(item.quantity)>Number(product.stock)) {
      return {ok:false,status:400,error:"Quantidade inválida ou estoque insuficiente."};
    }
    const unitPrice = Number(product.price);''')
s=s.replace('  const addressResult = normalizeAddress(body.address);','''  const addressResult = normalizeAddress(body.address);
  if (!addressResult.ok) return {ok:false,status:400,error:addressResult.message};''')
s=s.replace('  db.addOrder(order);','''  for (const item of quote.items) {
    const product=db.findProduct(item.productId);
    db.updateProduct(item.productId, {stock:Number(product.stock)-item.quantity});
  }
  db.addOrder(order);''')
f.write_text(s)
# visibility, admin authorization
f=p/'src/routes/api.js';s=f.read_text();s=s.replace('  if (method === "GET" && path === "/api/products") {','  if (method === "GET" && path === "/api/products") {')
s=s.replace('''    if (!order) {
      send(res, 404, { error: "Pedido não encontrado." });
      return;
    }
    send(res, 200, order);''','''    if (!order || order.userId !== user.id) {
      send(res, 404, { error: "Pedido não encontrado." });
      return;
    }
    send(res, 200, order);''')
s=s.replace('''  if (method === "PUT" && adminProductMatch) {
    const productId''','''  if (method === "PUT" && adminProductMatch) {
    if (!user) {send(res,401,{error:"Autenticação necessária."});return;}
    if (user.role!=="admin") {send(res,403,{error:"Acesso restrito a administradores."});return;}
    const productId''')
s=s.replace('  if (name.length < 3 || !emailOk || password.length < 6 || duplicate) {\n    return { ok: false };\n  }','''  if (name.length < 3) return {ok:false,error:"Nome deve ter pelo menos 3 caracteres."};
  if (!emailOk) return {ok:false,error:"E-mail inválido."};
  if (password.length < 6) return {ok:false,error:"Senha deve ter pelo menos 6 caracteres."};
  if (duplicate) return {ok:false,error:"E-mail já cadastrado."};''')
s=s.replace('send(res, 400, { error: "Dados inválidos" });','send(res, 400, { error: result.error });')
s=s.replace('''      lines.push({
        productId: product.id,''','''      if (!hasAvailableStock(Number(item.quantity),product.stock)) {
        send(res,400,{error:"Quantidade inválida ou estoque insuficiente."});return;
      }
      lines.push({
        productId: product.id,''')
f.write_text(s)
# order history: linear aggregation rather than O(n^2) nested
(p/'src/services/orderHistory.js').write_text('''"use strict";
function listVisibleOrders(db,userId){
 const owned=db.listOrders().filter(order=>order.userId===userId);
 const sums=new Map();
 for(const order of owned)for(const item of order.items)sums.set(item.productId,(sums.get(item.productId)||0)+Number(item.quantity||0));
 return owned.map(order=>({...order,items:order.items.map(item=>({...item,quantitySoldToCustomer:sums.get(item.productId)||0}))}));
}
module.exports={listVisibleOrders};
''')
# interface: labels and button support
f=p/'public/index.html';s=f.read_text();import re
s=s.replace('<input id="search"','<label for="search" class="sr-only">Buscar produtos</label>\n        <input id="search"')
# convert label based on following input or select
s=re.sub(r'<label>([^<]+)</label>\s*<(input|select) id="([^"]+)"',lambda m: f'<label for="{m.group(3)}">{m.group(1)}</label>\n          <{m.group(2)} id="{m.group(3)}"',s)
s=s.replace('<span class="button button-secondary" id="apply-coupon"','<button type="button" class="button button-secondary" id="apply-coupon"').replace('data-testid="apply-coupon">Aplicar cupom</span>','data-testid="apply-coupon">Aplicar cupom</button>')
f.write_text(s)
f=p/'public/js/catalog.js';s=f.read_text().replace('const add = document.createElement("div");','const add = document.createElement("button");\n  add.type = "button";')
s=s.replace('''  document.getElementById("refresh-catalog").addEventListener("click", () => {
    Aurora.loadCatalog();
  });
''','')
s=s.replace('''  document.getElementById("search").addEventListener("input", () => {
    Aurora.loadCatalog();
  });''','''  document.getElementById("search").addEventListener("input", () => {
    Aurora.renderCatalog();
  });
  document.getElementById("refresh-catalog").addEventListener("click", () => Aurora.loadCatalog());''')
f.write_text(s)
f=p/'public/js/main.js';s=f.read_text();s=s.replace('''  setInterval(() => {
    fetch("/api/products").catch(() => {});
  }, 2000);
''','');f.write_text(s)
f=p/'public/js/orders.js';s=f.read_text();s=s.replace('''  let orders = [];
  for (let attempt = 0; attempt < 8; attempt += 1) {
    orders = await Aurora.api.get("/api/orders");
  }
''','''  const orders = await Aurora.api.get("/api/orders");
''');f.write_text(s)
f=p/'public/js/auth.js';s=f.read_text().replace('  admin.hidden = false;','  admin.hidden = Aurora.state.user.role !== "admin";');f.write_text(s)
f=p/'public/js/admin.js';s=f.read_text().replace('''  } catch (error) {
    products = await Aurora.api.get("/api/products");
  }
  renderAdminProducts(products);''','''  } catch (error) {
    status.textContent = error.message;
    document.getElementById("admin-products").replaceChildren();
    return;
  }
  renderAdminProducts(products);''');f.write_text(s)
f=p/'public/js/cart.js';s=f.read_text().replace('''    root.innerHTML = "";
    checkout.hidden = Aurora.state.receipt === null;''','''    root.innerHTML = "<p>Seu carrinho está vazio. <a href=\\\"#catalogo\\\">Voltar ao catálogo</a>.</p>";
    checkout.hidden = Aurora.state.receipt === null;''');f.write_text(s)
# style for sr-only, focus
f=p/'public/css/styles.css';s=f.read_text()+'''\n.sr-only {position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}\n:focus-visible {outline:3px solid #ff7a00;outline-offset:3px;}\n''';f.write_text(s)
print('Correcoes aplicadas')
