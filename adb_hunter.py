#!/usr/bin/env python3
import argparse
import shutil
import subprocess
import sys
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
    ap.add_argument("-f", "--file", required=True, help="Arquivo com IPs (um por linha)")
    ap.add_argument("-p", "--port", type=int, default=5555, help="Porta ADB (padrão 5555)")
    ap.add_argument("-w", "--workers", type=int, default=20, help="Threads paralelas")
    ap.add_argument("-o", "--output", help="Salvar IPs confirmados em arquivo")
    ap.add_argument("-s", "--shell", action="store_true",
                    help="Confirmar apenas shells vivos (descarta 'error: closed')")
    ap.add_argument("--scrcpy", action="store_true",
                    help="Abrir scrcpy (--no-audio) para cada dispositivo confirmado")
    args = ap.parse_args()

    try:
        with open(args.file, "r") as f:
            ips = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    except FileNotFoundError:
        sys.exit(f"[!] Arquivo {args.file} não encontrado.")

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
