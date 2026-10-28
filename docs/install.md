# 導入手順

依存ライブラリはない（Python 3.11+ の標準ライブラリだけ）。

```bash
# このリポジトリを clone して
python -m unittest discover -s tests -v

# 対象プロジェクトを別ディレクトリに clone してから走査
python -m bot.scan_local --root /path/to/target --report out/report.json --apply-preview out/preview
python -m bot.plan_pr --report out/report.json --repo owner/name --out out/plan.md
```

- 認証情報はこのリポジトリに置かない。将来 GitHub API を使う場合もトークンは環境変数 `GITHUB_TOKEN` だけから読む
- `config/targets.json` は gitignore 対象。対象リストと対応メモはローカルにだけ置く
- CI を使う場合は `templates/workflows/ci.yml` を `.github/workflows/ci.yml` へコピーする
