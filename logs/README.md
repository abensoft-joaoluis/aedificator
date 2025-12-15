# Logs

Este diretório contém logs de todas as execuções dos projetos.

## Estrutura dos Logs

Cada execução gera um arquivo de log com o formato:
```
{projeto}_{timestamp}.log
```

### Projetos Logados:
- **superleme**: Logs do Zotonic/Superleme
- **sl_phoenix**: Logs do SL Phoenix
- **extension**: Logs da extensão Chrome

### Exemplo:
```
superleme_20231215_143022.log
sl_phoenix_20231215_143022.log
```

## Limpeza

Os arquivos de log não são versionados (estão no .gitignore).
Você pode deletar logs antigos manualmente quando necessário.

## Visualização

Para ver logs em tempo real:
```bash
tail -f logs/superleme_*.log
```

Para ver logs lado a lado de múltiplas execuções:
```bash
tail -f logs/superleme_*.log logs/sl_phoenix_*.log
```
