#!/usr/bin/env python3
"""Display Ubuntu Monitor metrics in a terminal."""
import argparse
import os
import shutil
import socket
import subprocess
from pathlib import Path
import datetime
import sys
import time
import unicodedata

START_CPU = None
START_NET = None

def read(path):
    try:
        return Path(path).read_text().strip()
    except (OSError, UnicodeError):
        return None

def cpu():
    global START_CPU
    raw = read('/proc/stat')
    if not raw:
        return None
    values = [int(v) for v in raw.splitlines()[0].split()[1:]]
    # guest and guest_nice are already counted in user and nice.
    total, idle = sum(values[:8]), values[3] + values[4]
    previous = START_CPU
    START_CPU = (total, idle)
    if previous is None or total <= previous[0]:
        return None
    return round(100 * (1 - (idle - previous[1]) / (total - previous[0])), 1)

def memory():
    raw = read('/proc/meminfo')
    if not raw:
        return None
    values = {}
    for line in raw.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[1].isdigit():
            values[parts[0].rstrip(':')] = int(parts[1]) * 1024
    total = values.get('MemTotal', 0)
    if not total:
        return None
    used = total - values.get('MemAvailable', values.get('MemFree', 0))
    return {'total': total, 'used': used, 'percent': round(used / total * 100, 1)}

def gpu():
    cmd = ['nvidia-smi', '--query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu', '--format=csv,noheader,nounits']
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3, check=True)
        cards = []
        for line in result.stdout.splitlines():
            fields = [v.strip() for v in line.split(',')]
            if len(fields) == 5:
                def number(s):
                    try: return float(s)
                    except ValueError: return None
                cards.append(dict(name=fields[0], utilization=number(fields[1]), memory_used=number(fields[2]), memory_total=number(fields[3]), temperature=number(fields[4])))
        return {'cards': cards, 'error': None if cards else 'GPU 情報を取得できませんでした'}
    except (OSError, subprocess.SubprocessError):
        return {'cards': [], 'error': 'NVIDIA GPU の情報を取得できません。nvidia-smi とドライバーを確認してください。'}

def network():
    """Aggregate non-loopback interface traffic; speeds are interval averages."""
    global START_NET
    raw = read('/proc/net/dev')
    if not raw:
        return None
    received = sent = 0
    for line in raw.splitlines()[2:]:
        if ':' not in line:
            continue
        interface, values = line.split(':', 1)
        fields = values.split()
        if interface.strip() == 'lo' or len(fields) < 16:
            continue
        try:
            received += int(fields[0])
            sent += int(fields[8])
        except ValueError:
            continue
    now = time.monotonic()
    previous = START_NET
    START_NET = (received, sent, now)
    if not previous or now <= previous[2]:
        return None
    elapsed = now - previous[2]
    return {'receive': max(0, received - previous[0]) / elapsed,
            'send': max(0, sent - previous[1]) / elapsed}


def top_processes():
    try:
        result = subprocess.run(['ps', '-eo', 'pid=,pcpu=,pmem=,comm=', '--sort=-pcpu'],
                                capture_output=True, text=True, timeout=3, check=True)
        rows = []
        for line in result.stdout.splitlines()[:5]:
            parts = line.split(None, 3)
            if len(parts) == 4:
                rows.append({'pid': parts[0], 'cpu': float(parts[1]),
                             'memory': float(parts[2]), 'name': parts[3]})
        return rows
    except (OSError, ValueError, subprocess.SubprocessError):
        return []


def metrics():
    disk = shutil.disk_usage('/')
    uptime = read('/proc/uptime')
    try:
        load = list(os.getloadavg())
    except (OSError, AttributeError):
        load = None
    return {'hostname': socket.gethostname(), 'timestamp': time.time(), 'cpu_percent': cpu(), 'cpu_count': os.cpu_count(), 'memory': memory(), 'disk': {'used': disk.used, 'total': disk.total, 'percent': round(disk.used / disk.total * 100, 1)}, 'uptime': float(uptime.split()[0]) if uptime else None, 'load': load, 'gpu': gpu(), 'network': network(), 'processes': top_processes()}



def percentage(value):
    return f'{value:.1f}%' if value is not None else '取得できません'


def size(value):
    return f'{value / (1024 ** 3):.1f} GiB'


def render(data):
    width = max(20, min(shutil.get_terminal_size((72, 24)).columns, 72))
    use_color = sys.stdout.isatty() and os.environ.get('TERM') != 'dumb' and 'NO_COLOR' not in os.environ
    encoding = sys.stdout.encoding or 'utf-8'
    try:
        '━●─█◆'.encode(encoding)
        rule, full, empty, dot, diamond = '━', '█', '─', '●', '◆'
    except (UnicodeEncodeError, LookupError):
        rule, full, empty, dot, diamond = '-', '#', '-', '*', '*'

    def color(value, code):
        return f'\033[{code}m{value}\033[0m' if use_color else value

    def visual_width(text):
        return sum(2 if unicodedata.east_asian_width(ch) in 'WF' else 1 for ch in text)

    def meter(label, value, detail=''):
        length = max(6, min(16, width - 24))
        if value is None:
            graph = color(empty * length, '90')
            amount = '   —'
        else:
            filled = round(max(0, min(100, value)) / 100 * length)
            code = '31' if value >= 90 else '33' if value >= 75 else '36'
            graph = color(full * filled, code) + color(empty * (length - filled), '90')
            amount = f'{value:5.1f}%'
        padding = ' ' * max(1, 12 - visual_width(label))
        base = f'  {label}{padding}{graph}  {amount}'
        if detail and 2 + 12 + length + 2 + len(amount) + 2 + visual_width(detail) <= width:
            return [base + color(f'  {detail}', '90')]
        return [base, color('    ' + detail, '90')] if detail else [base]

    stamp = datetime.datetime.fromtimestamp(data['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
    lines = [
        color(f'  {diamond}  UBUNTU MONITOR', '1;36'),
        color('  ' + rule * (width - 4), '90'),
        f"  {color(dot, '32')}  {color(data['hostname'], '1')}  {color('/  LIVE', '32')}",
        color(f'     最終更新  {stamp}', '90'),
        '',
        color('  SYSTEM  /  システム', '1;34'),
    ]
    lines += meter('CPU', data['cpu_percent'], f"{data['cpu_count'] or '?'} 論理 CPU")
    for key, name in [('memory', 'メモリ'), ('disk', 'ディスク /')]:
        item = data[key]
        detail = f"{size(item['used'])} / {size(item['total'])}" if item else '取得できません'
        lines += meter(name, item['percent'] if item else None, detail)
    uptime = data['uptime']
    if uptime is not None:
        seconds = int(uptime)
        lines += ['', f'  稼働時間  {seconds // 86400}日 {(seconds % 86400) // 3600}時間 {(seconds % 3600) // 60}分']
    if data['load']:
        lines.append(f"  負荷平均  {data['load'][0]:.2f} / {data['load'][1]:.2f} / {data['load'][2]:.2f}  (1 / 5 / 15 分)")
    lines += ['', color('  GPU  /  グラフィックス', '1;35')]
    gpu_data = data['gpu']
    if not gpu_data['cards']:
        lines.append('  ' + (gpu_data['error'] or 'GPU が見つかりません'))
    for index, card in enumerate(gpu_data['cards']):
        if index:
            lines.append('')
        lines.append('  ' + card['name'])
        lines += meter('使用率', card['utilization'])
        used, total = card['memory_used'], card['memory_total']
        mem = f'{used / 1024:.1f} / {total / 1024:.1f} GiB' if used is not None and total is not None else '取得できません'
        mem_percent = 100 * used / total if used is not None and total is not None and total > 0 else None
        lines += meter('GPU メモリ', mem_percent, mem)
        temp = f"{card['temperature']:.0f} °C" if card['temperature'] is not None else '取得できません'
        lines.append(f'  温度  {temp}')
    lines += ['', color('  NETWORK  /  通信速度', '1;34')]
    net = data.get('network')
    def rate(value):
        for unit in ('B/s', 'KiB/s', 'MiB/s', 'GiB/s'):
            if value < 1024 or unit == 'GiB/s':
                return f'{value:.1f} {unit}'
            value /= 1024
    if net:
        lines.append(f"  受信  {rate(net['receive'])}    送信  {rate(net['send'])}")
    else:
        lines.append('  通信速度を取得できません')
    lines += ['', color('  PROCESSES  /  CPU 使用率の高いプロセス', '1;34')]
    processes = data.get('processes', [])
    if processes:
        lines.append(color('  PID       CPU      メモリ   名前', '90'))
        for process in processes:
            name = process['name'].replace('\x1b', '?')[:max(8, width - 30)]
            lines.append(f"  {process['pid']:<9} {process['cpu']:>5.1f}%    {process['memory']:>5.1f}%   {name}")
    else:
        lines.append('  プロセス情報を取得できません')
    lines += ['', color('  ' + rule * (width - 4), '90')]
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='Ubuntu の稼働状況をターミナルに表示')
    parser.add_argument('--interval', type=float, default=5, help='更新間隔（秒、既定: 5）')
    parser.add_argument('--once', action='store_true', help='1回だけ表示して終了')
    args = parser.parse_args()
    if not 0.1 <= args.interval <= 3600:
        parser.error('--interval は 0.1〜3600 秒の範囲で指定してください')
    cpu()
    network()
    time.sleep(0.2)  # CPU の使用率を差分から求めるための最初の測定間隔
    try:
        while True:
            data = metrics()
            if sys.stdout.isatty() and not args.once:
                print('\033[H\033[2J', end='')
            print(render(data), flush=True)
            if args.once:
                break
            print(f'  更新間隔 {args.interval:g}秒  ·  終了 Ctrl+C', flush=True)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print('\n終了しました。')


if __name__ == '__main__':
    main()
