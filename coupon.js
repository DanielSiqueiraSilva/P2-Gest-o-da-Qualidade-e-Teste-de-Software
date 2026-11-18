"use strict";
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
