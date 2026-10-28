# 作業手順（1 PR ごと）

1. **候補を選ぶ** — `config/targets.example.json` を `targets.json` にコピーし、対象を 1 件だけ書く
2. **相手のルールを確認する** — CONTRIBUTING、PR テンプレート、最近マージされた typo / docs PR の有無、外部 PR を受け付けているか
3. **fork してローカルに clone する**（この作業は本人が GitHub 画面 / 手元で行う）
4. **走査する** — `python -m bot.scan_local --root <checkout> --report out/report.json`
   - 0 件ならその候補は終わり。無理に探さない
   - 上限（3ファイル・20件）を超えたら候補を捨てるか、ファイルを絞る
5. **プレビューを作って全件目視する** — `--apply-preview out/preview` で修正後コピーを作り、元の文と 1 件ずつ見比べる。固有名詞・引用・原文ママが混ざっていたら辞書ではなく、その場で除外する
6. **PR 計画を作る** — `python -m bot.plan_pr --report out/report.json --repo owner/name --out out/plan.md`
7. **提出は手動** — fork 側に `docs/fix-typos-prbot` ブランチを作り、確認済みの差分だけを commit して、計画の本文案を相手のテンプレートに合わせて PR を開く
8. **記録する** — 出した PR の URL、相手の反応、マージ / 却下とその理由を targets.json の notes に残す

## やらないこと

- 同じ日に複数のプロジェクトへ一斉に同じ PR を出す
- 却下された PR を別表現で出し直す
- コードの typo（変数名・関数名）をドキュメント修正のついでに直す
- 相手の CI が落ちたまま放置する（落ちたら直すか PR を閉じる）
