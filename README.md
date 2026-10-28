<p align="center">
  <img src="brasil.gif" alt="Bandeira do Brasil" width="640">
</p>

<p align="center">
  🇧🇷 <strong>Feito com orgulho por brasileiros</strong> 🇧🇷
</p>

# adb_hunter 🇧🇷

Ferramenta em Python para testar conectividade ADB (Android Debug Bridge) em uma lista de alvos — de arquivo local ou buscados via API do **Shodan** / **Censys** — usando o binário `adb` do sistema e threads paralelas.

> **Aviso:** use apenas em dispositivos próprios ou com autorização explícita. O operador é o único responsável pelo uso.

## Requisitos

- Python 3 (apenas stdlib — nenhum pacote extra)
- `adb` instalado e disponível no PATH
- `scrcpy` (opcional, apenas para a flag `--scrcpy`; requer display gráfico)

## Uso

```bash
python3 adb_hunter.py [-f ips.txt] [--shodan API_KEY] [--censys ID:SECRET] \
    [--query QUERY] [-p 5555] [-w 20] [--limit 100] [-o resultados.txt] [-s] [--scrcpy]
```

É preciso informar pelo menos uma fonte de alvos: `-f`, `--shodan` ou `--censys`. Elas podem ser combinadas; os IPs são unidos e deduplicados antes do teste.

| Flag | Descrição | Padrão |
|------|-----------|--------|
| `-f, --file` | Arquivo com IPs (um por linha, `#` ignora a linha) | — |
| `--shodan API_KEY` | Busca alvos no Shodan usando esta API key | — |
| `--censys ID:SECRET` | Busca alvos no Censys v2 usando `api_id:secret` | — |
| `--query QUERY` | Sobrescreve a query padrão de ADB usada nas APIs | padrão embutido |
| `--limit` | Máximo de hosts por fonte de API | 100 |
| `-p, --port` | Porta ADB | 5555 |
| `-w, --workers` | Threads paralelas | 20 |
| `-o, --output` | Arquivo para salvar os IPs confirmados | — |
| `-s, --shell` | Confirma apenas shells realmente vivos (descarta `error: closed`, `offline` e `unauthorized`) | desligado |
| `--scrcpy` | Abre o `scrcpy` (`--no-audio`) para cada dispositivo confirmado | desligado |

A chave de API vai direto no comando. As queries padrão de busca são:

- **Shodan:** `Android Debug Bridge port:5555`
- **Censys:** `services.port=5555 and services.service_name=ADB`

Use `--query` para trocar a busca.

## Modos de verificação

- **Padrão:** conecta e confere se o dispositivo aparece como `device` em `adb devices`.
- **`-s / --shell`:** além de conectar, executa um comando real no aparelho (`adb -s <alvo> shell`) e só confirma se o shell responder de verdade — assim os `error: closed` não entram na lista.

## Exemplos

```bash
# De arquivo, só shells vivos, salvando o resultado
python3 adb_hunter.py -f ips.txt -s -o vivos.txt

# Shodan: passa a API key e usa a query padrão de ADB; abre o scrcpy
python3 adb_hunter.py --shodan SUA_KEY -s --scrcpy

# Censys: credenciais no formato id:secret
python3 adb_hunter.py --censys SEU_ID:SEU_SECRET -s

# Trocando a query da busca
python3 adb_hunter.py --shodan SUA_KEY --query 'port:5555 product:"Android Debug Bridge"' -s

# Combinando arquivo + Shodan + Censys
python3 adb_hunter.py -f ips.txt --shodan SUA_KEY --censys SEU_ID:SEU_SECRET -s -o vivos.txt
```
