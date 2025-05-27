# Contribuindo para o JTech MCP Executor

Obrigado pelo seu interesse em contribuir com o JTech MCP Executor! Este documento fornece orientações para desenvolvimento interno na J-Tech.

## Confidencialidade

Este projeto contém informações confidenciais e proprietárias da J-Tech. Todo o código e documentação devem ser tratados conforme as políticas de segurança da informação da empresa.

## Como Contribuir

### Relatando Bugs

Bugs são rastreados como issues no GitLab. Ao criar uma issue sobre um bug, inclua:

- Um título claro e descritivo
- Passos detalhados para reproduzir o bug
- Comportamento esperado vs. comportamento atual
- Código de exemplo, capturas de tela ou logs de erro
- Informações sobre o ambiente (SO, versão do Python, etc.)

### Sugerindo Melhorias

Melhorias também são rastreadas como issues no GitLab. Ao sugerir melhorias:

- Use um título claro e descritivo
- Forneça uma descrição detalhada da melhoria sugerida
- Explique por que essa melhoria seria útil
- Se possível, inclua exemplos de como a melhoria funcionaria

### Merge Requests

1. Clone o repositório conforme as instruções de acesso fornecidas
2. Crie uma branch a partir de `main`: `git checkout -b dev-sua-funcionalidade`
3. Implemente suas mudanças
4. Adicione testes para sua nova funcionalidade
5. Certifique-se de que todos os testes passam: `make test`
6. Execute o linting: `make lint`
7. Commit suas alterações seguindo as convenções da J-Tech
8. Envie para o repositório: `git push origin dev-sua-funcionalidade`
9. Abra um Merge Request para a branch `main` do repositório

## Ambiente de Desenvolvimento

Recomendamos usar o Makefile para configurar seu ambiente de desenvolvimento:

```bash
# Cria ambiente virtual e instala dependências de desenvolvimento
make install-dev

# Ativa o ambiente virtual
source .venv/bin/activate
```

## Testes

Todos os MRs devem passar nos testes existentes e incluir novos testes para novas funcionalidades:

```bash
# Executa todos os testes
make test

# Executa testes específicos
.venv/bin/pytest tests/unit/test_specific.py
```

## Estilo de Código

Este projeto usa o Ruff para linting e formatação de código:

```bash
# Verifica o código
make lint
```

Seguimos as convenções PEP 8 com algumas modificações especificadas no arquivo `ruff.toml`.

## Documentação

- Docstrings devem seguir o formato Google
- Mantenha o README.md atualizado
- Adicione exemplos de código para novas funcionalidades

## Processo de Versão

Usamos versionamento semântico (SemVer):

- PATCH (x.y.Z) - correções de bugs retrocompatíveis
- MINOR (x.Y.z) - novas funcionalidades retrocompatíveis
- MAJOR (X.y.z) - mudanças que quebram compatibilidade

## Entre em contato

Se tiver dúvidas que não são abordadas por este documento, entre em contato com o líder técnico do projeto.