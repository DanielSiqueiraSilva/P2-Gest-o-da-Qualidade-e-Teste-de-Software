"use strict";
const FIELDS=["street","number","district","city","state","zip"];
function normalizeAddress(input){
 const source=input && typeof input==="object" ? input : {};
 const address={};
 for(const field of FIELDS) address[field]=String(source[field]??"").trim();
 if(FIELDS.some((field)=>!address[field]))return {ok:false,message:"Preencha o endereço de entrega completo."};
 if(!/^[A-Za-z]{2}$/.test(address.state)|| !/^\d{5}-?\d{3}$/.test(address.zip)) return {ok:false,message:"UF ou CEP inválido."};
 address.state=address.state.toUpperCase();
 return {ok:true,address};
}
module.exports={normalizeAddress,FIELDS};
