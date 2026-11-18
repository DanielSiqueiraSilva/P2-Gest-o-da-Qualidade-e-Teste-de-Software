'use strict';
const test=require('node:test');const assert=require('node:assert/strict');const vm=require('node:vm');const fs=require('node:fs');const path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'../public/js/cart.js'),'utf8');
function makeEnv(){
 const store=new Map();const handlers={};const els={};
 for(const id of ['cart-count','cart-content','apply-coupon','checkout-button'])els[id]={textContent:'',value:'',disabled:false,addEventListener(type,fn){handlers[`${id}:${type}`]=fn}};
 const document={getElementById(id){return els[id]||{value:''}}};
 const localStorage={getItem(k){return store.get(k)||null},setItem(k,v){store.set(k,v)},removeItem(k){store.delete(k)}};
 const window={Aurora:{}};vm.runInNewContext(source,{window,document,localStorage,location:{hash:''},console});
 const A=window.Aurora;A.renderCart=async()=>{};return {A,els,handlers,store};
}
test('CT-F05B / RF-05 adicionar item e incrementar quantidade no carrinho',async()=>{
 const {A,els}=makeEnv();await A.addToCart('produto-teste');await A.addToCart('produto-teste');assert.equal(A.state.cart.length,1);assert.equal(A.state.cart[0].quantity,2);assert.equal(els['cart-count'].textContent,'2');
});
test('CT-F05C / RF-05 remover item do carrinho',async()=>{
 const {A,handlers}=makeEnv();A.initCart();await A.addToCart('produto-teste');handlers['cart-content:click']({target:{closest(selector){return {dataset:{remove:'produto-teste'}}}}});assert.equal(A.state.cart.length,0);
});
test('CT-F05D / RF-05 alterar quantidade no carrinho',async()=>{
 const {A,handlers,els}=makeEnv();A.initCart();await A.addToCart('produto-teste');handlers['cart-content:change']({target:{matches(){return true},dataset:{productId:'produto-teste'},value:'3'}});assert.equal(A.state.cart[0].quantity,3);assert.equal(els['cart-count'].textContent,'3');
});
