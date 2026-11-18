# Teste visual de compatibilidade e usabilidade (executar na máquina da equipe)

Este ambiente registrou bloqueio do navegador. Reproduza os casos abaixo no seu computador com a Loja Aurora em execução local.

**CT-COMP01:** abrir `http://127.0.0.1:3000` em janela Chromium com tamanho 1280x850; confirmar que catálogo, busca, filtro, carrinho e cadastro funcionam; registrar captura de tela identificada.

**CT-COMP02:** repetir com viewport 390x850 (modo responsivo, ferramentas do desenvolvedor); comparar legibilidade, quebra de colunas, rolagem horizontal e botões. Anotar diferenças reais, ainda que nenhuma seja observada.

**CT-US01–05 visual:** inspecionar rótulo do Nome, navegação por Tab/Enter em Adicionar ao carrinho e Aplicar cupom, contorno de foco, erro que identifica o campo incorreto e mensagem de carrinho vazio com caminho de retorno.

**Automação opcional:** de uma pasta que contenha `codigo` e `ferramentas`, execute `python ferramentas/testar_interface.py` com Python Playwright instalado; imagens, quando capturadas, ficam em `evidencias/`. Não utilize capturas artificiais ou de outras versões.

| Caso | Ambiente / versão | Resultado real | Diferenças | Evidência |
|---|---|---|---|---|
| CT-COMP01 | | | | |
| CT-COMP02 | | | | |

Ao concluir, atualize o Caderno DOCX e reexporte o PDF.
