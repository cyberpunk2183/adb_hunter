# adb_hunter

Ferramenta em Python para testar conectividade ADB (Android Debug Bridge) em uma lista de endereços IP, usando o binário `adb` do sistema e threads paralelas.

> **Aviso:** use apenas em dispositivos próprios ou com autorização explícita. O operador é o único responsável pelo uso.

## Requisitos

- Python 3
- `adb` instalado e disponível no PATH

## Uso

```bash
python3 adb_hunter.py -f ips.txt [-p 5555] [-w 20] [-o resultados.txt]
```

| Flag | Descrição | Padrão |
|------|-----------|--------|
| `-f, --file` | Arquivo com IPs (um por linha, `#` ignora a linha) | obrigatório |
| `-p, --port` | Porta ADB | 5555 |
| `-w, --workers` | Threads paralelas | 20 |
| `-o, --output` | Arquivo para salvar os IPs confirmados | — |
