'use strict';
const path=require('path');
const root=path.resolve(__dirname,'../evidencias/versao_anterior');
const {automaticDiscount}=require(path.join(root,'src/domain/discount'));
const {shippingCost}=require(path.join(root,'src/domain/shipping'));
const {validateQuantity}=require(path.join(root,'src/domain/quantity'));
const {percentOf}=require(path.join(root,'src/domain/money'));
const {evaluateCoupon}=require(path.join(root,'src/domain/coupon'));
const cases=[
{id:'BUG-01',rule:'RN-01 desconto no limiar de R$200',expected:20,obtained:automaticDiscount(200)},
{id:'BUG-02',rule:'RN-02 frete no limiar de R$300',expected:0,obtained:shippingCost(300)},
{id:'BUG-03',rule:'RN-03 quantidade negativa',expected:false,obtained:validateQuantity(-1).ok},
{id:'BUG-04',rule:'RN-04 cupom vencido',expected:false,obtained:evaluateCoupon({code:'ANTIGO',type:'percent',value:20,expiresAt:'2026-10-06',active:true}).ok},
{id:'BUG-05',rule:'RN-06 arredondamento half-up',expected:20.01,obtained:percentOf(200.05,10)}
];
console.log(JSON.stringify({stage:'ANTES',date:new Date().toISOString(),cases:cases.map(c=>({...c,pass:c.expected===c.obtained}))},null,2));
