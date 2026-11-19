# Ubuntu Server Monitor

Ubuntu サーバーの CPU・メモリ・ディスク・GPU の稼働状況をターミナルで確認する、読み取り専用のツールです。

## 必要なもの

- Ubuntu と Python 3.8 以降（追加の Python パッケージは不要）
- GPU 情報には NVIDIA GPU と、動作する NVIDIA ドライバー・`nvidia-smi` が必要です。AMD / Intel GPU の取得には未対応です。

## 起動

サーバーに SSH 接続し、このフォルダーで実行します。

```bash
python3 terminal.py
```

5 秒ごとに更新します。終了は Ctrl+C です。更新間隔を変えるには `python3 terminal.py --interval 10`、1 回だけ表示するには `python3 terminal.py --once` を使います。

## 指標について

- CPU：前回取得時との差分から計算。
- メモリ：全容量から、空き領域と再利用可能なキャッシュを含む利用可能量を差し引いた概算。
- ディスク：ルート `/` のファイルシステム。別マウントの `/home` などは含まれません。
- GPU：`nvidia-smi` の値。複数枚ある場合はすべて表示します。
- ネットワーク：ループバックを除くインターフェースの受信・送信速度の合計。仮想インターフェースを含むため、環境によっては同じ通信が重複して計上されます。
- プロセス：`ps` の CPU 使用率順に最大 5 件。CPU 使用率はプロセス起動からの平均で、マルチコアでは 100% を超える場合があります。メモリは全物理メモリに対する割合です。
- 負荷平均：1、5、15 分間のロードアベレージ。CPU 使用率とは異なり、コア数を超える値になることもあります。

GPU が表示されない場合は、サーバー上で `nvidia-smi` を実行し、ドライバーが正常に動いているか確認してください。

## GitHub に載せる

GitHub に空のリポジトリを作成した後、このフォルダー内で次を実行します。URL は自分のリポジトリに置き換えてください。

```bash
git init
git add README.md terminal.py .gitignore
git commit -m "Add Ubuntu terminal monitor"
git branch -M main
git remote add origin https://github.com/ユーザー名/リポジトリ名.git
git push -u origin main
```

Git のユーザー設定や GitHub への認証が別途必要な場合があります。
