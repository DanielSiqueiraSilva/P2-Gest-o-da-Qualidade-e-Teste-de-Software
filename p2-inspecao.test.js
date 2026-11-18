'use strict';
const test=require('node:test');const assert=require('node:assert/strict');const fs=require('node:fs');const path=require('node:path');
const read=(p)=>fs.readFileSync(path.join(__dirname,'..',p),'utf8');
const html=read('public/index.html'),catalog=read('public/js/catalog.js'),cart=read('public/js/cart.js'),css=read('public/css/styles.css'),api=read('src/routes/api.js');
test('CT-US01 / checklist rótulo Nome associado',()=>{assert.match(html,/<label for="register-name">Nome<\/label>/)});
test('CT-US02 / checklist controles primários são buttons nativos',()=>{assert.match(catalog,/document\.createElement\("button"\)/);assert.match(html,/<button type="button"[^>]*id="apply-coupon"/)});
test('CT-US03 / checklist foco visível por CSS',()=>{assert.match(css,/:focus-visible\s*\{outline:/)});
test('CT-US04 / checklist erro identifica campo de cadastro',()=>{assert.match(api,/Nome deve ter pelo menos/);assert.match(api,/E-mail inválido/);assert.match(api,/Senha deve ter/)});
test('CT-US05 / checklist carrinho vazio apresenta instrução e link',()=>{assert.match(cart,/Seu carrinho está vazio/);assert.match(cart,/#catalogo/)});
