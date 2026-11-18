# Entrega P2 - Gestão da Qualidade e Teste de Software

**Projeto:** Loja Aurora (versão revisada, 18/11/2026). **Equipe / turma:** preencher antes do envio.

## Conteúdo
- `Caderno_de_Testes_Loja_Aurora_P2.pdf`: relatório principal para entrega.
- `Caderno_de_Testes_Loja_Aurora_P2.docx`: versão editável do mesmo relatório.
- `codigo/`: aplicação completa Node.js, testes e requisitos originais (`REQUISITOS.md`).
- `evidencias/`: logs de testes, antes/depois, métricas brutas e impedimento da automação visual.
- `relatorios/desempenho.json`: métricas de carga/estresse locais.
- `ferramentas/`: scripts reproduzíveis para gerar as evidências e conferir interface.
- `ROTEIRO_DEMONSTRACAO.md`, `SESSAO_EXPLORATORIA_15MIN.md`, `VERIFICACAO_FINAL.md`.

## Execução rápida
Requer Node.js >=18. Na pasta `codigo`:

```bash
npm run reset
npm start
```

Abra `http://127.0.0.1:3000` no navegador local. Use apenas dados fictícios. Em outro terminal na pasta `codigo`:

```bash
npm test
```

A suíte final executada neste ambiente apresentou **63 testes aprovados, 0 falhas**. Alguns cenários de interface não foram executados em navegador: a infraestrutura de automação retornou `ERR_BLOCKED_BY_ADMINISTRATOR`. Não confundir inspeção de código com teste visual executado.

## Repetir medidas e capturas
Execute a partir da pasta raiz desta entrega:

```bash
python ferramentas/medir_desempenho.py
python ferramentas/testar_interface.py
```

Para o teste visual, instale Playwright no computador com acesso ao navegador:

```bash
python -m pip install playwright
python -m playwright install chromium
```

Em ambientes sem Chromium instalado no local esperado, deixe o Playwright usar a versão incluída no pacote, ou defina a variável `CHROMIUM_PATH`. O teste de carga é **exclusivamente local, limitado e contra a cópia temporária da base**.

## Aviso de integridade e pendências
Esta entrega inclui resultados reais de testes automatizados e medições de carga. **Ainda é necessário:** realizar uma sessão exploratória real de 15 minutos com observações próprias; validar em dois ambientes no navegador com screenshots; preencher integrantes/responsável; conferir visualmente o sistema; e executar a demonstração ao professor. O caderno identifica essas pendências. Não foram inventados logs, capturas de tela ou nomes.

Para finalizar no seu computador, siga `VERIFICACAO_FINAL.md` e exporte novamente o PDF se preencher os campos do DOCX.

Os arquivos de regras anteriores à correção foram conservados em `evidencias/versao_anterior/src/domain/` para permitir reproduzir sem falsificação os resultados de `CT-CONF01-antes.json`. Os comandos `node ferramentas/registrar_antes.js` e `node ferramentas/registrar_depois.js` comparam essa versão anterior e a revisada, respectivamente.
