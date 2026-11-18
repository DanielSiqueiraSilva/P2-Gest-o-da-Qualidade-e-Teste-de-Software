"use strict";
function listVisibleOrders(db,userId){
 const owned=db.listOrders().filter(order=>order.userId===userId);
 const sums=new Map();
 for(const order of owned)for(const item of order.items)sums.set(item.productId,(sums.get(item.productId)||0)+Number(item.quantity||0));
 return owned.map(order=>({...order,items:order.items.map(item=>({...item,quantitySoldToCustomer:sums.get(item.productId)||0}))}));
}
module.exports={listVisibleOrders};
