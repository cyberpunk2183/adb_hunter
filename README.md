# adb_hunter

Ferramenta em Python para testar conectividade ADB (Android Debug Bridge) em uma lista de endereços IP, usando o binário `adb` do sistema e threads paralelas.

> **Aviso:** use apenas em dispositivos próprios ou com autorização explícita. O operador é o único responsável pelo uso.

## Requisitos

- Python 3
- `adb` instalado e disponível no PATH
- `scrcpy` (opcional, apenas para a flag `--scrcpy`; requer display gráfico)

## Uso

```bash
python3 adb_hunter.py -f ips.txt [-p 5555] [-w 20] [-o resultados.txt] [-s] [--scrcpy]
```

| Flag | Descrição | Padrão |
|------|-----------|--------|
| `-f, --file` | Arquivo com IPs (um por linha, `#` ignora a linha) | obrigatório |
| `-p, --port` | Porta ADB | 5555 |
| `-w, --workers` | Threads paralelas | 20 |
| `-o, --output` | Arquivo para salvar os IPs confirmados | — |
| `-s, --shell` | Confirma apenas shells realmente vivos (descarta `error: closed`, `offline` e `unauthorized`) | desligado |
| `--scrcpy` | Abre o `scrcpy` (`--no-audio`) para cada dispositivo confirmado | desligado |

## Modos de verificação

- **Padrão:** conecta e confere se o dispositivo aparece como `device` em `adb devices`.
- **`-s / --shell`:** além de conectar, executa um comando real no aparelho (`adb -s <alvo> shell`) e só confirma se o shell responder de verdade — assim os `error: closed` não entram na lista.

## Exemplos

```bash
# Só confirmar shells vivos e salvar o resultado
python3 adb_hunter.py -f ips.txt -s -o vivos.txt

# Confirmar shells vivos e já abrir o scrcpy de cada um
python3 adb_hunter.py -f ips.txt -s --scrcpy
```
