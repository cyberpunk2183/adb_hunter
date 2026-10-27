#!/usr/bin/env python3
import argparse
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

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

def main():
    ap = argparse.ArgumentParser(description="ADB Auto-Connect Hunter")
    ap.add_argument("-f", "--file", required=True, help="Arquivo com IPs (um por linha)")
    ap.add_argument("-p", "--port", type=int, default=5555, help="Porta ADB (padrão 5555)")
    ap.add_argument("-w", "--workers", type=int, default=20, help="Threads paralelas")
    ap.add_argument("-o", "--output", help="Salvar IPs confirmados em arquivo")
    args = ap.parse_args()

    try:
        with open(args.file, "r") as f:
            ips = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    except FileNotFoundError:
        sys.exit(f"[!] Arquivo {args.file} não encontrado.")

    ips = list(dict.fromkeys(ips))
    print(f"[*] Testando {len(ips)} IPs na porta {args.port} com {args.workers} threads...")

    found = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(check_adb_connection, ip, args.port) for ip in ips]
        for future in as_completed(futures):
            ip, ok = future.result()
            if ok:
                print(f"[+] CONFIRMADO: {ip}:{args.port}")
                found.append(ip)

    print(f"\n[✓] Total de dispositivos acessíveis: {len(found)}")
    
    if found and args.output:
        with open(args.output, "w") as f:
            for ip in found:
                f.write(f"{ip}:{args.port}\n")
        print(f"[i] Resultados salvos em {args.output}")

if __name__ == "__main__":
    main()
