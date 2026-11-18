# Roteiro de demonstração prática - Loja Aurora (P2)

Objetivo: mostrar que a aplicação e os testes executam e interpretar resultados, sem apresentar resultados estimados como medidos.

1. **Ambiente (1 min):** abra `codigo/REQUISITOS.md` e mostre RF-01 a RF-10. Na pasta `codigo`, execute `npm run reset` e `npm start`; abra `http://127.0.0.1:3000`. Utilize as contas fictícias informadas no `codigo/README.md`.
2. **Testes automatizados (1-2 min):** em outro terminal execute `npm test`. Mostre no resultado os IDs `CT-U02`, `CT-CP01`, `CT-F09`, `CT-S01`, `CT-I01`, `CT-R01`. Explique que os resultados são obtidos no projeto local e não significam que os testes manuais já ocorreram.
3. **Defeito, correção e confirmação (1 min):** abra `evidencias/CT-CONF01-antes.json` e `evidencias/CT-CONF01-depois.json`, compare RN-01 (R$ 200: R$ 0 antes, R$ 20 depois). Abra `codigo/src/domain/discount.js` e mostre o uso de `>=`. Explique a regressão `CT-R01` a `CT-R03`.
4. **Desempenho (1 min):** abra `relatorios/desempenho.json` e apresente concorrência 2, 6 e 12 (carga), 24 (estresse), 2 (recuperação); descreva p95, vazão e erros. As cargas foram aplicadas somente a `127.0.0.1`.
5. **Limitações e próximos passos (30s):** deixe claro que testes visuais/compatibilidade estão bloqueados neste ambiente de execução e que a sessão exploratória de 15 minutos deve ser realizada e documentada na máquina da equipe.

Perguntas esperadas: por que diferenciar testes unitários e integração? O unitário exercita uma função isolada; a integração envolve API, regras e persistência. Por que testar limite? Porque comparações `>` e `>=` frequentemente introduzem defeitos. Por que o p95? Mede tempo abaixo do qual 95% das requisições terminam.
