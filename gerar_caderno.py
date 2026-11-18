from pathlib import Path
import re,json,datetime
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT,WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
ROOT=Path(__file__).resolve().parent.parent
TESTS=ROOT/'codigo/tests'; perf=json.loads((ROOT/'relatorios/desempenho.json').read_text())
DATE='18/11/2026'
COL=RGBColor(24,69,107);PALE='DFEAF2';GRAY=RGBColor(79,88,94)
# Dados extraídos dos casos automatizados; esperado apresentado como assertiva, não como registro visual não executado.
M={
'CT-U01':('199,99; regra RN-01','desconto 0,00'),
'CT-U02':('200,00; regra RN-01','desconto 20,00'),
'CT-U03':('200,01; regra RN-01','desconto 20,00'),
'CT-U04':('299,99; RN-02','frete 18,50'),
'CT-U05':('300,00; RN-02','frete 0,00'),
'CT-U06':('quantidade -1','ok=false'),
'CT-U07':('quantidade 0','ok=false'),
'CT-U08':('quantidade 1','ok=true'),
'CT-U09':('R$ 200,05 x 10%','resultado 20,01 (half-up)'),
'CT-U10':('cupom ANTIGO vence em 06/10/2026; relógio em 07/10/2026','ok=false'),
'CT-U11':('cupom vence em 07/10/2026; relógio 07/10/2026 23:59:59 UTC','ok=true'),
'CT-U12':('subtotal 250; cupom fixo 30; desconto automático 25','desconto 30; total 238,50'),
'CT-U13':('subtotal 300, desconto 30, frete 0','total 270,00'),
'CT-U14':('endereço somente com rua','ok=false'),
'CT-U15':('produto R$ 150,00 x 2','subtotal 300; desconto 30; frete 0; total 270'),
'CT-F01':('POST /api/auth/register; nome Aluno Teste, email fictício único, Senha123!','HTTP 201 e token de sessão'),
'CT-F02':('GET /api/auth/me; token cliente-a','HTTP 200; email cliente-a@loja.test'),
'CT-F02B':('POST /api/auth/logout com token; em seguida GET /api/auth/me','HTTP 200 no logout; HTTP 401 na sessão revogada'),
'CT-F03':('GET /api/products','HTTP 200; catálogo contém produto-teste e campos obrigatórios'),
'CT-F04':('DOM simulado: cartões caderno, fone e lápis; buscar "fone"','apenas cartão fone visível; cartões não recriados'),
'CT-F04B':('DOM simulado: categorias Papelaria, Eletrônicos; filtrar Papelaria','2 cartões de Papelaria visíveis; Eletrônicos oculto'),
'CT-F05':('POST /api/cart/quote; produto-teste qtd 2','HTTP 200; 300 / 30 / 0 / 270'),
'CT-F05B':('carrinho DOM simulado; adicionar produto-teste duas vezes','um item no carrinho; quantidade 2'),
'CT-F05C':('carrinho DOM simulado; clique Remover em produto-teste','lista do carrinho vazia'),
'CT-F05D':('carrinho DOM simulado; campo de quantidade alterado para 3','quantidade 3, contador atualizado'),
'CT-F06':('GET /api/products/produto-teste','HTTP 200; estoque inicial 5'),
'CT-F07':('POST /api/cart/quote; produto-teste qtd 2 + cupom VINTE','HTTP 200; desconto 60; total 240'),
'CT-F08':('POST /api/checkout; endereço somente rua, cliente autenticado','HTTP 400; endereço incompleto rejeitado'),
'CT-F09':('POST /api/checkout; produto-teste qtd 2, endereço completo, preço forjado 0,01','HTTP 201; subtotal 300; total 270; estoque 3; pedido gravado'),
'CT-F10':('GET /api/orders; sessão cliente-a','HTTP 200; histórico inclui novo pedido e só pedidos do cliente'),
'CT-I01':('pedido de 2 unidades; estoque prévio 5','estoque final 3, persistido em arquivo JSON'),
'CT-I02':('ID retornado no checkout; GET /api/orders/{id}','HTTP 200 e mesmo ID'),
'CT-APISUP01':('GET /api/products','HTTP 200; campo category presente nos produtos'),
'CT-N01':('POST /api/cart/quote com quantidade -1','HTTP 400'),
'CT-N02':('POST /api/cart/quote com quantidade 99 (estoque 3)','HTTP 400'),
'CT-N03':('POST /api/cart/quote com cupom vencido ANTIGO','HTTP 400'),
'CT-S01':('token cliente-b; GET /api/orders/{id} de cliente-a','HTTP 404'),
'CT-S02':('PUT /api/admin/products/produto-teste sem token','HTTP 401'),
'CT-S03':('PUT /api/admin/products/produto-teste com token cliente','HTTP 403'),
'CT-S04':('PUT /api/admin/products/produto-teste; estoque -100 com token admin','HTTP 400'),
'CT-R01':('POST checkout mesma compra duas vezes no intervalo de 5s','mesmo ID nas duas respostas 201, sem duplicação'),
'CT-R02':('POST /api/cart/quote; produto-teste qtd 1 com preço cliente 0,01','subtotal calculado no servidor 150,00'),
'CT-R03':('GET /api/orders token cliente-b','apenas pedidos de cliente-b'),
'CT-CP01':('cotação com preço 199,99; 200,00; 200,01','descontos 0 / 20 / 20; equivalência + valor-limite'),
'CT-CP02':('cotação com preço 299,99; 300,00; 300,01','fretes 18,50 / 0 / 0; equivalência + valor-limite'),
'CT-US01':('inspeção estática public/index.html','label for=register-name associado ao input'),
'CT-US02':('inspeção estática catalog.js e index.html','ações usam elementos button nativos'),
'CT-US03':('inspeção estática styles.css','regra :focus-visible tem contorno identificável'),
'CT-US04':('inspeção estática api.js / routes/api.js','mensagens distinguem Nome, E-mail e Senha'),
'CT-US05':('inspeção estática cart.js','texto de carrinho vazio e link #catalogo'),
}
# Categorização precisa do escopo verificável
REQ={
'CT-I01':'RF-06; RF-09; RN-08','CT-I02':'RF-09; RF-10; RN-08',
'CT-F01':'RF-01','CT-F02':'RF-02','CT-F02B':'RF-02','CT-F03':'RF-03','CT-F04':'RF-04','CT-F04B':'RF-04','CT-F05':'RF-05; RN-01; RN-02','CT-F05B':'RF-05','CT-F05C':'RF-05','CT-F05D':'RF-05','CT-F06':'RF-06','CT-F07':'RF-07; RN-05','CT-F08':'RF-08; RN-13','CT-F09':'RF-09; RN-07; RN-08; RN-12','CT-F10':'RF-10; RN-10',
'CT-N01':'RN-03','CT-N02':'RN-03','CT-N03':'RN-04','CT-S01':'RN-10','CT-S02':'RN-11','CT-S03':'RN-11','CT-S04':'RN-11; RN-12','CT-R01':'RN-09','CT-R02':'RN-12','CT-R03':'RN-10','CT-APISUP01':'RF-03',
'CT-CP01':'RN-01','CT-CP02':'RN-02',
'CT-US01':'RNF-01','CT-US02':'RNF-02','CT-US03':'RNF-03','CT-US04':'RNF-04','CT-US05':'RNF-05'
}
for i,rn in enumerate(['RN-01','RN-01','RN-01','RN-02','RN-02','RN-03','RN-03','RN-03','RN-06','RN-04','RN-04','RN-05','RN-06','RN-13','RN-01; RN-02'],1):REQ[f'CT-U{i:02d}']=rn
files=[('p2-unit.test.js','Unitário'),('p2-api.test.js','Funcional/API, integração, segurança, regressão e caixa-preta'),('p2-ui-logic.test.js','Funcional/DOM simulado'),('p2-carrinho-logica.test.js','Funcional/carrinho DOM simulado'),('p2-inspecao.test.js','Usabilidade: inspeção estática')]
CASES=[]
for filename,fallback in files:
 text=(TESTS/filename).read_text()
 for name in re.findall(r"test\('([^']+)'",text):
  id,description=(x.strip() for x in name.split(' / ',1))
  if id not in M:raise ValueError('Sem metadados: '+id)
  if id.startswith('CT-U'):mode='Unitário'
  elif id.startswith('CT-I'):mode='Integração'
  elif id.startswith('CT-S'):mode='Segurança básica'
  elif id.startswith('CT-R'):mode='Regressão'
  elif id.startswith('CT-CP'):mode='Funcional / Caixa-preta'
  elif id.startswith('CT-N'):mode='Funcional negativo'
  elif id.startswith('CT-US'):mode='Usabilidade / inspeção estática'
  elif id=='CT-APISUP01':mode='API / apoio'
  elif id in ('CT-F04','CT-F04B'):mode='Funcional (DOM simulado)'
  elif id in ('CT-F05B','CT-F05C','CT-F05D'):mode='Funcional (carrinho DOM simulado)'
  else:mode='Funcional / sistema (API)'
  status='APROVADO'
  if id in ('CT-F04','CT-F04B','CT-F05B','CT-F05C','CT-F05D'):status='APROVADO (lógica DOM simulada; sem navegador)'
  if id.startswith('CT-US'):status='APROVADO (inspeção estática; sem navegador)'
  data,expected=M[id]
  step_test=f'node --test tests/{filename}'
  if mode=='Unitário':
   steps=f'1. Abrir terminal na pasta codigo. 2. Executar {step_test}. 3. Localizar {id}; conferir a assertiva correspondente aos dados e valores esperados.'
  elif id.startswith('CT-US'):
   steps=f'1. Abrir os arquivos de interface listados no teste. 2. Executar {step_test}. 3. Verificar a condição estática no código e o resultado do teste {id}.'
  elif id in ('CT-F05B','CT-F05C','CT-F05D'):
   steps=f'1. Preparar carrinho e eventos com documento fictício. 2. Acionar operação descrita em dados de entrada. 3. Executar {step_test} e comparar estado do carrinho.'
  elif id in ('CT-F04','CT-F04B'):
   steps=f'1. Construir DOM fictício de três cartões pelo script. 2. Aplicar texto/categoria indicada por meio de renderCatalog(). 3. Executar {step_test}; conferir quais cartões ficaram ocultos.'
  else:
   steps=f'1. Executar {step_test}; o script prepara banco e servidor locais temporários. 2. Realizar a requisição descrita nos dados de entrada, com token quando indicado. 3. Conferir status, corpo e persistência previstos na assertiva {id}.'
  evpath='evidencias/CT-SUITE-FINAL.txt'
  CASES.append({'id':id,'description':description,'mode':mode,'requirement':REQ[id], 'priority':'Alta' if id.startswith(('CT-S','CT-R','CT-I','CT-CP','CT-N')) or id in ('CT-F08','CT-F09') else 'Média','pre':'Node.js >=18; código e dependências nativas disponíveis; banco didático copiado nos testes de API.' if not id.startswith('CT-US') else 'Código-fonte da interface disponível para leitura.', 'data':data,'steps':steps,'expected':expected,'obtained':f'Assertiva de {id} satisfeita na suíte final; {expected}. Não se trata de captura de interface.' if mode not in ('Funcional (DOM simulado)','Funcional (carrinho DOM simulado)','Usabilidade / inspeção estática') else f'Condição verificada no escopo indicado: {expected}.','status':status,'date':DATE,'ev':evpath+f' (buscar ID {id}); codigo/tests/{filename}'})
assert len(CASES)==50,len(CASES)

def shade(cell,fill):
 tcPr=cell._tc.get_or_add_tcPr(); shd=OxmlElement('w:shd');shd.set(qn('w:fill'),fill);tcPr.append(shd)
def addtable(d,headers,rows,widths=None,size=8):
 t=d.add_table(rows=1,cols=len(headers));t.style='Table Grid';t.alignment=WD_TABLE_ALIGNMENT.CENTER
 for c,h in zip(t.rows[0].cells,headers):c.text=h;shade(c,'16466E')
 trPr=t.rows[0]._tr.get_or_add_trPr();repeat=OxmlElement('w:tblHeader');repeat.set(qn('w:val'),'true');trPr.append(repeat)
 for c in t.rows[0].cells:
  for para in c.paragraphs:para.paragraph_format.keep_with_next=True
 for r in t.rows:
  for c in r.cells:
   for p in c.paragraphs:
    for run in p.runs:run.font.size=Pt(size);run.font.bold=True;run.font.color.rgb=RGBColor(255,255,255)
 for index,row in enumerate(rows):
  cells=t.add_row().cells
  for i,v in enumerate(row):
   cells[i].text=str(v);cells[i].vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
   if index%2==0:shade(cells[i],'F2F6FA')
   for p in cells[i].paragraphs:
    p.paragraph_format.space_after=Pt(1)
    for run in p.runs:run.font.size=Pt(size)
 d.add_paragraph().paragraph_format.space_after=Pt(1)
 return t

def addp(d,text,bold_start=None):
 p=d.add_paragraph();p.paragraph_format.space_after=Pt(4)
 if bold_start and text.startswith(bold_start):p.add_run(bold_start).bold=True;p.add_run(text[len(bold_start):])
 else:p.add_run(text)
 return p

def section(d,title):d.add_heading(title,level=1)
d=Document();sec=d.sections[0];sec.top_margin=Inches(.68);sec.bottom_margin=Inches(.62);sec.left_margin=Inches(.78);sec.right_margin=Inches(.78)
normal=d.styles['Normal'];normal.font.name='Aptos';normal.font.size=Pt(9);normal.font.color.rgb=RGBColor(25,34,43)
normal.paragraph_format.space_after=Pt(4)
for style_name,sz in [('Title',22),('Heading 1',13),('Heading 2',10)]:
 st=d.styles[style_name];st.font.name='Aptos Display';st.font.size=Pt(sz);st.font.bold=True;st.font.color.rgb=COL
 st.paragraph_format.space_before=Pt(12);st.paragraph_format.space_after=Pt(5)
header=sec.header.paragraphs[0];header.text='P2 • GESTÃO DA QUALIDADE E TESTE DE SOFTWARE  |  LOJA AURORA';header.style='Caption';header.runs[0].font.color.rgb=COL
footer=sec.footer.paragraphs[0];footer.alignment=WD_ALIGN_PARAGRAPH.CENTER;footer.add_run('Loja Aurora | P2 | 18/11/2026  •  Página ')
fld=OxmlElement('w:fldSimple');fld.set(qn('w:instr'),'PAGE');footer._p.append(fld)

p=d.add_paragraph();p.style='Title';p.add_run('Caderno de Testes\nLoja Aurora')
addp(d,'P2 - Planejamento, implementação, execução e documentação de testes de software')
addp(d,'Versão consolidada e corrigida • 18 de novembro de 2026 • sistema local Node.js')
addtable(d,['Identificação','Registro'],[
('Curso / disciplina','Engenharia de Software, 7º período | Gestão da Qualidade e Teste de Software'),('Sistema','Loja Aurora 1.0.0 - versão revisada para a P2'),('Equipe / turma','[PREENCHER NOMES E TURMA]'),('Responsável / matrícula','[PREENCHER]'),('Repositório','[PREENCHER, se publicado]'),('Ambiente verificado','Node.js v22.16.0; Linux em execução local; testes com banco JSON fictício'),('Data de consolidação',DATE)
],size=9)
addp(d,'Declaração de integridade: os resultados automatizados e as métricas deste caderno têm logs reais anexados. A execução do navegador foi bloqueada pela infraestrutura com ERR_BLOCKED_BY_ADMINISTRATOR; não há capturas de tela inventadas. A sessão exploratória de 15 minutos não foi executada e permanece explicitamente pendente.')

section(d,'1. Objetivo e escopo')
addp(d,'Validar os dez primeiros requisitos funcionais RF-01 a RF-10 do arquivo REQUISITOS.md, além de regras de negócio (RN), acessibilidade e segurança. RF-11, a administração do catálogo, aparece como cobertura complementar. Dados são didáticos e o sistema está executável em 127.0.0.1:3000.')
addp(d,'A fonte da verdade para valores de desconto/frete é codigo/REQUISITOS.md: desconto automático de 10% a partir de R$ 200,00 e frete de R$ 18,50 abaixo de R$ 300,00. Os valores divergentes do caderno anterior foram ajustados. O desconto não entra no limiar do frete, definido sobre o subtotal antes de descontos.')
section(d,'2. Inventário: funcionalidades, pré-condições e riscos')
inventory=[
('RF-01','Cadastro de usuário','API ativa; e-mail fictício único','Alto: credenciais inválidas/duplicadas'),
('RF-02','Entrada e saída da conta','Conta ativa de teste','Alto: sessão/autenticação'),
('RF-03','Exibição do catálogo','Produtos e servidor disponíveis','Médio: itens ocultos/dados incorretos'),
('RF-04','Busca textual e filtro de categoria','Catálogo carregado no navegador','Médio: filtragem e desempenho de UI'),
('RF-05','Adicionar, atualizar e remover carrinho','Produto com estoque disponível','Alto: quantidades e preços'),
('RF-06','Controle de estoque','Base fictícia consistente','Alto: venda além do estoque'),
('RF-07','Aplicação de cupom','Cupom válido/inativo/vencido configurado','Alto: desconto e validade'),
('RF-08','Endereço no pedido','Usuário autenticado; endereço fictício','Alto: pedido sem endereço válido'),
('RF-09','Finalização do pedido','Carrinho, sessão e estoque válidos','Alto: idempotência, pagamento não incluído'),
('RF-10','Histórico e detalhe dos próprios pedidos','Pedido criado e autenticação','Alto: vazamento entre contas'),
]
addtable(d,['Req.','Funcionalidade','Pré-condição','Risco'],inventory,size=7.5)
section(d,'3. Ambiente, ferramentas e massa de dados')
addtable(d,['Elemento','Identificação verificada'],[
('Aplicação','Node.js v22.16.0, API HTTP e interface HTML/CSS/JS; pacote original sem dependências npm externas.'),
('Persistência','Arquivo data/db.json, com cópias temporárias independentes nos testes de integração/desempenho.'),
('Automação','node:test e assert/strict; comando npm test; 63 execuções aprovadas.'),
('Interface','Chromium detectado no ambiente, mas abertura da aplicação bloqueada pelo navegador por política; tentativas registradas em evidencias/CT-INTERFACE.json.'),
('Massa fictícia','produto-teste R$ 150,00 e estoque inicial 5; cliente-a@loja.test, cliente-b@loja.test, admin@loja.test; cupons ANTIGO e VINTE.'),
('Horário dos registros','18/11/2026; UTC nos logs JSON, data local do documento no Brasil.'),
('Limites','Carga e estresse somente em 127.0.0.1, sobre cópia temporária. Nenhum serviço de terceiros testado.'),
],size=8)
section(d,'4. Plano, critérios e priorização')
addp(d,'Critérios de entrada: código e README disponíveis; Node.js >=18 instalado; dados fictícios restaurados; servidor local acessível; casos com entradas, pré-condições e resultados esperados registrados.')
addp(d,'Critérios de saída: no mínimo 3 testes unitários, 2 de integração, 10 funcionais com 3 negativos, 2 caixa-preta com equivalência e valor-limite, reteste após correção, 3 regressões, carga e estresse medidos; segurança com 2 cenários; 5 critérios de usabilidade; compatibilidade em 2 ambientes; sessão exploratória de 15 minutos; evidências organizadas.')
addp(d,'Prioridade alta: segurança, checkout, preços, cupons, quantidade, estoque e persistência. Média: catálogo, busca, rotulagem, teclado e compatibilidade. Pendências não são tratadas como aprovações.')
section(d,'5. Matriz de rastreabilidade - requisito x casos')
matrix=[
('RF-01','CT-F01; CT-US01; CT-US04','Cadastro API comprovado; inspeção estática da UI'),
('RF-02','CT-F02; CT-F02B','Sessão autenticada e logout por API aprovados'),
('RF-03','CT-F03; CT-APISUP01','API do catálogo aprovada'),
('RF-04','CT-F04; CT-F04B','Lógica de busca/filtro aprovada em DOM simulado; navegador pendente'),
('RF-05','CT-F05; CT-F05B a CT-F05D; CT-N01; CT-N02','API e lógica simulada de adicionar/alterar/remover; navegador pendente'),
('RF-06','CT-F06; CT-I01','Consulta de estoque e redução persistida'),
('RF-07','CT-F07; CT-N03; CT-U10; CT-U11','Cupom válido/vencido e regras de domínio'),
('RF-08','CT-F08; CT-U14','Endereço incompleto rejeitado; envio válido em CT-F09'),
('RF-09','CT-F09; CT-I01; CT-I02; CT-R01','Checkout, persistência, idempotência'),
('RF-10','CT-F10; CT-I02; CT-S01; CT-R03','Histórico próprio, detalhe, autorização'),
('RF-11 (extra)','CT-S02; CT-S03; CT-S04; CT-CP01; CT-CP02','Admin restrito; catálogo de testes criado com token admin'),
]
addtable(d,['Requisito','Casos associados','Interpretação'],matrix,size=7.5)
section(d,'6. Cobertura de modalidades exigidas pela P2')
coverage=[
('Unitário: >=3','15 casos novos automatizados, todos aprovados','Atendido'),
('Integração: >=2','CT-I01, CT-I02 com API e persistência reais','Atendido'),
('Funcional: 10, com 3 negativos','CT-F01 a CT-F10, F02B, F04B, F05B-D, e CT-N01 a N03; interações de DOM simuladas','Parcial: interface manual pendente'),
('Caixa-preta: 2','CT-CP01 e CT-CP02; classes e valores-limite','Atendido na API'),
('Exploratório: 15 min','Roteiro entregue sem hora inicial/final verdadeira','Pendente'),
('Confirmação: 1','CT-CONF01, comparação antes/depois de RN-01','Atendido'),
('Regressão: 3','CT-R01, CT-R02, CT-R03 aprovados','Atendido'),
('Carga: 1','Patamares 2/6/12; média, p95, erros, vazão','Atendido local'),
('Estresse: 1','24 concorrentes + fase de recuperação 2','Atendido local'),
('Segurança básica: 2','CT-S01 a CT-S04 não destrutivos','Atendido'),
('Usabilidade: checklist 5','CT-US01 a US05 aprovados por inspeção estática','Parcial: inspeção visual pendente'),
('Compatibilidade: 2 ambientes','Tentativas 1280x850 e 390x850 bloqueadas','Bloqueado'),
]
addtable(d,['Modalidade','Cobertura realizada','Situação'],coverage,size=7.6)
section(d,'7. Registro de defeitos reais, correção e reteste')
pre=json.loads((ROOT/'evidencias/CT-CONF01-antes.json').read_text())['cases'];post=json.loads((ROOT/'evidencias/CT-CONF01-depois.json').read_text())['cases']
desc={'BUG-01':'Desconto com operador > em vez de >= (Alta)','BUG-02':'Frete aplicado sobre base artificial reduzida (Alta)','BUG-03':'Quantidade negativa aceita (Alta)','BUG-04':'Cupom vencido aceito (Alta)','BUG-05':'Arredondamento com truncamento (Média)'}
fix={'BUG-01':'src/domain/discount.js - comparação >=','BUG-02':'src/domain/shipping.js - subtotal original','BUG-03':'src/domain/quantity.js - rejeita <=0','BUG-04':'src/domain/coupon.js - compara validade com relógio','BUG-05':'src/domain/money.js - half-up'}
addtable(d,['Defeito / severidade','Antes (obtido; esperado)','Após correção','Arquivo'],[(b['id']+' • '+desc[b['id']],str(b['obtained'])+' ; '+str(b['expected']),str(post[i]['obtained'])+' • PASS',fix[b['id']]) for i,b in enumerate(pre)],size=7.6)
addp(d,'CT-CONF01 (confirmação): executado após correção de BUG-01. Condição: subtotal = R$ 200,00; esperado: R$ 20,00; obtido antes: 0; após: 20; status APROVADO. Comandos: node ferramentas/registrar_antes.js para referência original e node ferramentas/registrar_depois.js para implementação corrigida. Os logs originais assinados pela data constam em evidencias/CT-CONF01-antes.json e CT-CONF01-depois.json. O arquivo antes foi gerado ANTES das alterações; não executar novamente sobre a versão corrigida para simular o passado.')
addp(d,'A versão inicial incluía outros problemas de acesso e persistência identificados na revisão de código; o diff completo em relatorios/ALTERACOES_NO_CODIGO.diff permite conferir essas alterações. Somente os cinco defeitos listados acima têm medições numéricas antes/depois gravadas.')
section(d,'8. Carga e estresse - resultados medidos')
addp(d,'Cenário controlado: GET /api/products/produto-teste, aplicação em 127.0.0.1, dataset fictício isolado; carga limitada por número de clientes concorrentes durante aproximadamente 3 s por patamar. Vazão = requisições HTTP 200 / segundo; p95 = 95º percentil da latência. Os resultados são específicos desta execução e não são uma garantia de produção.')
addtable(d,['Etapa','Conc.','Req.','Erros','Média ms','p95 ms','Vazão req/s'],[(x['cenario'],x['concorrencia'],x['requisicoes'],x['erros'],x['latencia_media_ms'],x['p95_ms'],x['vazao_req_s']) for x in perf['stages']],size=7.3)
addp(d,'Interpretação: não houve erros HTTP nas medições. A latência p95 aumentou conforme a concorrência, chegando ao patamar de estresse com 24 clientes. Na fase de recuperação, a latência caiu novamente. Sem SLA pré-estabelecido, não se atribui conformidade a um limite arbitrário. Evidências: relatorios/desempenho.json; evidencias/CT-CARGA-STRESS-amostras.csv; script ferramentas/medir_desempenho.py.')
section(d,'9. Usabilidade, compatibilidade e exploração')
addp(d,'Checklist de cinco critérios verificado ESTATICAMENTE com assertivas sobre o código: (1) associação rótulo/campo Nome; (2) ações principais em button; (3) indicador CSS de foco; (4) mensagens de erro específicas; (5) instrução para carrinho vazio. Esses resultados NÃO constituem navegação visual automatizada. Testes em navegador continuam necessários para confirmar que funcionam em uso real.')
addp(d,'Compatibilidade: as tentativas CT-COMP01 (Chromium 1280x850) e CT-COMP02 (Chromium 390x850) falharam ao iniciar a navegação local com ERR_BLOCKED_BY_ADMINISTRATOR; status BLOQUEADO, não reprovação do aplicativo. Reexecutar ferramentas/testar_interface.py em computador com navegador permitido; comparar telas e guardar as imagens CT-COMP*.png.')
addp(d,'Exploratório CT-EXP01: duração exigida de 15 minutos, ainda NÃO EXECUTADO. O roteiro em SESSAO_EXPLORATORIA_15MIN.md reserva blocos de 3 minutos para cadastro, catálogo, limites de carrinho, pedido, histórico e teclado. Registrar data, horários, observações e achados reais.')
section(d,'10. Métricas, conclusão e entregáveis')
addtable(d,['Indicador','Resultado consolidado'],[
('Execuções npm test','63 aprovadas, 0 reprovadas, 0 canceladas (CT-SUITE-FINAL.txt)'),
('Casos P2 automatizados com ID','50 (inclui 5 de inspeção estática e 5 com DOM simulado); 13 testes originais também passaram'),
('Funcionalidades RF-01...RF-10','10/10 mapeadas; confirmação de interação por navegador ainda incompleta'),
('Negativos','CT-N01, CT-N02, CT-N03 executados e aprovados'),
('Defeitos','5 reproduzidos antes, corrigidos e confirmados após'),
('Regressão','3 casos identificados aprovados'),
('Desempenho','5 estágios (3 de carga, estresse, recuperação), 0 erros na amostra'),
('Pendências','Sessão exploratória real 15 min; compatibilidade em 2 ambientes; verificação visual de acessibilidade; equipe e demonstração'),
],size=8)
addp(d,'Conclusão técnica: a versão revisada atende às assertivas da suíte automatizada e demonstrou correções reprodutíveis e métricas locais de carga/estresse. Ainda NÃO se pode declarar que todos os critérios da P2 foram plenamente satisfeitos, pois a exploração cronometrada e a compatibilidade visual não foram executadas com evidências. Os passos faltantes estão em VERIFICACAO_FINAL.md. Todas as falhas e limitações permanecem visíveis para que a equipe apresente a situação com integridade.')
addp(d,'Entregáveis: (1) este caderno em PDF e DOCX, (2) diretório codigo com fonte e testes, (3) evidencias organizadas por ID, (4) LEIA_PRIMEIRO.md e codigo/README.md com comandos, (5) roteiro prático de demonstração. O pacote ZIP centraliza tudo.')

section(d,'11. Fichas individuais de testes e evidências')
addp(d,'As 50 fichas seguintes correspondem às assertivas realmente executadas em node:test. "Obtido" se refere ao resultado do teste automatizado sobre o escopo indicado; não à abertura da tela no Chromium. Todos os IDs são únicos.')
for j,c in enumerate(CASES):
 h=d.add_heading(f"{c['id']} - {c['description']}",level=2)
 # avoid orphan headings
 h.paragraph_format.keep_with_next=True
 fields=[('Requisito / modalidade',c['requirement']+' | '+c['mode']),('Prioridade / responsável / data',c['priority']+' | Responsável: [PREENCHER] | '+c['date']),('Pré-condições',c['pre']),('Dados de entrada',c['data']),('Passos numerados',c['steps']),('Resultado esperado',c['expected']),('Resultado obtido',c['obtained']),('Status',c['status']),('Evidência / automação',c['ev'])]
 t=d.add_table(rows=0,cols=2);t.style='Table Grid'
 for ix,(key,val) in enumerate(fields):
  a,b=t.add_row().cells;a.text=key;b.text=val
  if ix%2==0:shade(a,'E9F0F6');shade(b,'F4F7FA')
  a.width=Inches(1.53);b.width=Inches(5.23)
  for cell in (a,b):
   for p_ in cell.paragraphs:
    p_.paragraph_format.space_after=Pt(0)
    for run in p_.runs:run.font.size=Pt(7.3)
  for run in a.paragraphs[0].runs:run.bold=True
 d.add_paragraph().paragraph_format.space_after=Pt(0)

section(d,'12. Casos complementares (desempenho, confirmação e não executados)')
for key,req,mode,inputs,steps,expected,result,status,evidence in [
('CT-CONF01','RN-01','Confirmação','200,00 e regra desconto','1. Comparar arquivo antes. 2. Aplicar correção >=. 3. Executar unitário CT-U02. 4. Comparar arquivo depois.','0 antes e 20 depois, com correção confirmada','Antes 0, depois 20; CT-U02 aprovado','APROVADO','evidencias/CT-CONF01-antes.json e CT-CONF01-depois.json'),
('CT-CARGA01','RNF-06; desempenho','Carga crescente','2, 6, 12 clientes; GET /api/products/produto-teste','1. Executar python ferramentas/medir_desempenho.py. 2. Registrar tempo médio, p95, erros e vazão por patamar. 3. Comparar.','Métricas mensuráveis sem extrapolar ambiente local','Todas as etapas registradas em desempenho.json; 0 erros','APROVADO','relatorios/desempenho.json; CT-CARGA-STRESS-amostras.csv'),
('CT-EST01','RNF-06; desempenho','Estresse','24 concorrentes além de 12 referência; retorno a 2','1. Executar ferramenta local. 2. Observar degradação no patamar 24. 3. Medir recuperação em 2.','Registrar falhas e recuperação; falhas podem ser zero','0 erros; p95 maior no estresse e menor na recuperação','APROVADO','relatorios/desempenho.json'),
('CT-EXP01','RF-01 a RF-10','Exploratório','Navegação do sistema por 15 minutos REAIS','1. Preencher abertura e horários. 2. Seguir roteiro com liberdade para investigar. 3. Registrar observações e achados.','15 min cronometrados, notas e screenshots','Sessão não realizada neste ambiente','BLOQUEADO / NÃO EXECUTADO','SESSAO_EXPLORATORIA_15MIN.md'),
('CT-COMP01','RNF-01 a RNF-05','Compatibilidade','Chromium, 1280x850','1. Executar python ferramentas/testar_interface.py. 2. Observar cadastro, busca, carrinho e teclado. 3. Capturar tela.','Fluxo funcional com capturas e diferenças anotadas','ERR_BLOCKED_BY_ADMINISTRATOR ao abrir endereço local','BLOQUEADO','evidencias/CT-INTERFACE.json'),
('CT-COMP02','RNF-01 a RNF-05','Compatibilidade','Chromium, 390x850','1. Repetir o roteiro em viewport menor. 2. Registrar alterações de layout e problemas. 3. Capturar tela.','Comparação registrada com ambiente desktop','ERR_BLOCKED_BY_ADMINISTRATOR ao abrir endereço local','BLOQUEADO','evidencias/CT-INTERFACE.json'),
]:
 h=d.add_heading(key+' - '+mode,level=2);h.paragraph_format.keep_with_next=True
 addtable(d,['Campo','Registro'],[("Requisito / modalidade",req+' | '+mode),("Prioridade / pré-condições",'Alta | aplicação local com dados fictícios; responsável [PREENCHER]'),('Dados de entrada',inputs),('Passos numerados',steps),('Resultado esperado',expected),('Resultado obtido',result),('Status / data',status+' | '+DATE),('Evidência',evidence)],size=7.7)

section(d,'Anexo A. Arquivos, comandos e organização de evidências')
addtable(d,['Arquivo','Finalidade'],[
('codigo/tests/p2-unit.test.js','15 casos unitários com assertivas'),
('codigo/tests/p2-api.test.js','25 casos API, integração, funcionais, negativos, segurança, regressão e caixa-preta'),
('codigo/tests/p2-ui-logic.test.js','2 casos de lógica de filtro em DOM simulado'),
('codigo/tests/p2-carrinho-logica.test.js','3 casos de carrinho em DOM simulado'),
('codigo/tests/p2-inspecao.test.js','5 critérios de inspeção estática'),
('evidencias/CT-SUITE-FINAL.txt','63 testes, 63 pass, 0 fail'),
('evidencias/CT-CONF01-antes.json; depois.json','Falhas reais antes e confirmações após'),
('evidencias/CT-CARGA-STRESS-amostras.csv','Amostras individuais de tempos e estados HTTP'),
('evidencias/CT-INTERFACE.json','Tentativas bloqueadas, sem capturas de tela'),
('relatorios/ALTERACOES_NO_CODIGO.diff','Diferenças entre o código original e o corrigido'),
('VERIFICACAO_FINAL.md','Pendências transparentes para entrega'),
],size=8)

out=ROOT/'Caderno_de_Testes_Loja_Aurora_P2.docx';d.save(out)
print('Created:',out,'casos:',len(CASES),'pages: render pending')
