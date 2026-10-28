# PRbot

他プロジェクトへ、ドキュメントの typo 修正だけの小さな Pull Request を出すための半自動 Bot スターターキット。

自分のリポジトリを整理する githubbot とは別物で、こちらは他人のプロジェクトが対象。そのため自動で PR を提出することはしない。

- 候補探しと diff 作成は自動、**PR 提出は本人が diff と相手のルールを確認してから手動**
- 対象はドキュメントだけ（`.md` / `.mdx` / `.rst` / `.txt` / `.adoc`）。コードファイルは対象外
- コードブロック・インラインコード・URL の中は書き換えない
- `bot/typo_logic.py` — typo 検出と置換の純粋ロジック（ネットワークなし、単体テスト付き）
- `bot/scan_local.py` — ローカルのチェックアウトを dry-run で走査し、レポートを出す CLI。リポジトリは変更しない
- `bot/plan_pr.py` — 走査レポートから PR 計画（ブランチ名・タイトル・本文案）を作る CLI。GitHub へは送信しない
- `bot/github_client.py` — 提出ガードだけを持つ最小クライアント。既定では提出を拒否する
- `config/typos.json` — 誤りが一意に確定するものだけを集めた置換辞書
- `templates/` — PR 本文と提出前チェックリスト、CI 雛形
- `docs/design.md` — 設計と安全の既定値 / `docs/workflow.md` — 実際の作業手順 / `docs/install.md` — 導入手順

## ローカル検証

```bash
python -m unittest discover -s tests -v
python -m bot.scan_local --root /path/to/checkout --report out/report.json
python -m bot.plan_pr --report out/report.json --repo owner/name
```

## ステータス

スターターキット作成済み・ローカル検証済み（単体テスト14件を3回とも成功、走査の dry-run とプレビュー、PR計画生成、提出ガードの拒否を確認）。実際の PR 提出は未実施で、提出は本人が手順書どおり手動で行う。
