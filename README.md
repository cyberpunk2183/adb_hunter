# adb_hunter

Ferramenta em Python para testar conectividade ADB (Android Debug Bridge) em uma lista de alvos — de arquivo local ou buscados via API do **Shodan** / **Censys** — usando o binário `adb` do sistema e threads paralelas.

> **Aviso:** use apenas em dispositivos próprios ou com autorização explícita. O operador é o único responsável pelo uso.

## Requisitos

- Python 3 (apenas stdlib — nenhum pacote extra)
- `adb` instalado e disponível no PATH
- `scrcpy` (opcional, apenas para a flag `--scrcpy`; requer display gráfico)
- Chaves de API em variáveis de ambiente (apenas se usar `--shodan` / `--censys`)

## Uso

```bash
python3 adb_hunter.py [-f ips.txt] [--shodan QUERY] [--censys QUERY] \
    [-p 5555] [-w 20] [--limit 100] [-o resultados.txt] [-s] [--scrcpy]
```

É preciso informar pelo menos uma fonte de alvos: `-f`, `--shodan` ou `--censys`. Elas podem ser combinadas; os IPs são unidos e deduplicados antes do teste.

| Flag | Descrição | Padrão |
|------|-----------|--------|
| `-f, --file` | Arquivo com IPs (um por linha, `#` ignora a linha) | — |
| `--shodan QUERY` | Busca alvos no Shodan (requer `SHODAN_API_KEY`) | — |
| `--censys QUERY` | Busca alvos no Censys v2 (requer `CENSYS_API_ID` e `CENSYS_API_SECRET`) | — |
| `--limit` | Máximo de hosts por fonte de API | 100 |
| `-p, --port` | Porta ADB | 5555 |
| `-w, --workers` | Threads paralelas | 20 |
| `-o, --output` | Arquivo para salvar os IPs confirmados | — |
| `-s, --shell` | Confirma apenas shells realmente vivos (descarta `error: closed`, `offline` e `unauthorized`) | desligado |
| `--scrcpy` | Abre o `scrcpy` (`--no-audio`) para cada dispositivo confirmado | desligado |

## Chaves de API

As credenciais são lidas do ambiente (nunca ficam no código):

```bash
export SHODAN_API_KEY="sua_chave"
export CENSYS_API_ID="seu_id"
export CENSYS_API_SECRET="seu_secret"
```

## Modos de verificação

- **Padrão:** conecta e confere se o dispositivo aparece como `device` em `adb devices`.
- **`-s / --shell`:** além de conectar, executa um comando real no aparelho (`adb -s <alvo> shell`) e só confirma se o shell responder de verdade — assim os `error: closed` não entram na lista.

## Exemplos

```bash
# De arquivo, só shells vivos, salvando o resultado
python3 adb_hunter.py -f ips.txt -s -o vivos.txt

# Buscando no Shodan e abrindo o scrcpy de cada confirmado
python3 adb_hunter.py --shodan 'Android Debug Bridge port:5555' -s --scrcpy

# Censys v2, limitando a 50 hosts
python3 adb_hunter.py --censys 'services.port=5555 and services.service_name=ADB' --limit 50 -s

# Combinando arquivo + Shodan + Censys
python3 adb_hunter.py -f ips.txt --shodan 'port:5555 product:"Android Debug Bridge"' \
    --censys 'services.service_name=ADB' -s -o vivos.txt
```
