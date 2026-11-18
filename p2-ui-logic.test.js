'use strict';
const test=require('node:test');const assert=require('node:assert/strict');const vm=require('node:vm');const fs=require('node:fs');const path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'../public/js/catalog.js'),'utf8');
function prepare(){
 const nodes=[{dataset:{search:'caderno escolar papelaria',category:'Papelaria'},hidden:false},{dataset:{search:'fone bluetooth eletronicos',category:'Eletrônicos'},hidden:false},{dataset:{search:'lapis de cor papelaria',category:'Papelaria'},hidden:false}];
 const search={value:''},category={value:''},grid={children:nodes};
 const document={getElementById(id){return {'search':search,'category-filter':category,'catalog-grid':grid}[id]}};
 const window={Aurora:{}};const context={document,window,console};vm.createContext(context);vm.runInContext(source,context);
 return {nodes,search,category,render:window.Aurora.renderCatalog};
}
test('CT-F04 / RF-04 busca filtra produtos pelo texto sem recriar cartões',()=>{const ui=prepare();ui.search.value='fone';ui.render();assert.deepEqual(ui.nodes.map(n=>n.hidden),[true,false,true]);assert.equal(ui.nodes.length,3)});
test('CT-F04B / RF-04 filtro de categoria restringe catálogo',()=>{const ui=prepare();ui.category.value='Papelaria';ui.render();assert.deepEqual(ui.nodes.map(n=>n.hidden),[false,true,false])});
