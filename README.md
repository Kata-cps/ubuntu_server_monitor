<div align="center">

# 🖥️ Ubuntu Server Monitor

**サーバーの「いま」を、ターミナルでひと目で確認。**

![Ubuntu](https://img.shields.io/badge/Ubuntu-E95420?logo=ubuntu&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)
![NVIDIA GPU](https://img.shields.io/badge/GPU-NVIDIA-76B900?logo=nvidia&logoColor=white)
![Dependencies](https://img.shields.io/badge/dependencies-none-0D9488)

SSH で接続した Ubuntu サーバーの稼働状況を確認できる、読み取り専用のモニターです。  
Python の追加パッケージは必要ありません。

</div>

## ✨ プレビュー

![ターミナルでの表示例](assets/preview.png)

> 画像のホスト名・GPU・数値は表示例です。実際の値はサーバーの環境に応じて変わります。

## 📊 表示する情報

| 項目 | 確認できること |
| --- | --- |
| 💻 **CPU** | モデル名、使用率、論理 CPU 数、負荷平均 |
| 🐧 **OS** | OS 名、CPU アーキテクチャ、カーネルのバージョン |
| 🧠 **メモリ** | 使用率と使用量 |
| 💾 **ディスク** | ルート `/` の使用率と使用量 |
| 🎮 **GPU** | NVIDIA GPU の使用率、メモリ、温度 |
| 🌐 **ネットワーク** | IP アドレス、受信・送信の通信速度 |
| ⚙️ **プロセス** | CPU 使用率の高いプロセスを最大 5 件 |
| ⏱️ **稼働時間** | サーバーの連続稼働時間 |

## 🚀 使い方

### 必要なもの

- Ubuntu と **Python 3.8 以降**
- GPU 情報を表示する場合は、NVIDIA GPU と動作するドライバー・`nvidia-smi`。AMD / Intel GPU の取得には対応していません。

### 起動する

サーバーに SSH 接続し、このフォルダーで実行します。

```bash
python3 terminal.py
```

表示は **5 秒ごと**に更新されます。終了するときは `Ctrl + C` を押してください。

### 更新間隔を変える

```bash
# 10 秒ごとに更新
python3 terminal.py --interval 10

# 1 回だけ表示して終了
python3 terminal.py --once
```

## 🔎 指標について

- **CPU**：前回取得時との差分から計算します。
- **メモリ**：全容量から、再利用可能なキャッシュを含む利用可能量を差し引いた概算です。
- **ディスク**：ルート `/` のファイルシステムを表示します。別マウントの `/home` などは含まれません。
- **GPU**：`nvidia-smi` の値を表示します。複数枚ある場合はすべて表示します。
- **IP アドレス**：`ip` コマンドで取得した、ループバック以外のグローバルスコープの IPv4 / IPv6 アドレスを表示します。プライベート IPv4 アドレスも含みます。
- **ネットワーク**：ループバックを除くインターフェースの通信速度を合計します。仮想インターフェースを含むため、環境によっては同じ通信が重複して計上されます。
- **プロセス**：`ps` の CPU 使用率順に表示します。CPU 使用率はプロセス起動からの平均で、マルチコアでは 100% を超える場合があります。メモリは全物理メモリに対する割合です。
- **負荷平均**：1・5・15 分間のロードアベレージです。CPU 使用率とは異なり、コア数を超える値になることもあります。

## 🛠️ GPU が表示されないとき

サーバー上で次のコマンドを実行し、NVIDIA ドライバーが正常に動作しているか確認してください。

```bash
nvidia-smi
```
