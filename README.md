# photo-portal-site

VRChat ワールド「フォトポータル」のポータルセレクターが読み込む掲載リストとサムネを、GitHub Pages で公開するリポジトリ。

ワールドが読むのは次の2ファイルだけ。URL は固定で、中身だけが更新される。

- `https://<ユーザー名>.github.io/<リポジトリ名>/worlds.json`
- `https://<ユーザー名>.github.io/<リポジトリ名>/thumbs.jpg`

## 掲載の追加・取り下げ

`data/worlds-source.json` の `items` を編集して `main` に push するだけ。GitHub Actions が VRChat からサムネを取り直し、2ファイルを作り直して公開する。ワールドの再アップロードはいらない。

```json
{
  "worldId": "wrld_xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "title": "ワールド名（省略すると VRChat 上の名前）",
  "author": "作者名（省略すると VRChat 上の作者名）",
  "description": "紹介文（1〜2行）",
  "category": "個人展示"
}
```

- 並び順は `items` の順番どおり
- カテゴリは自由に書いてよい。ワールド側のタブは、出てきた順に自動で作られる（「全部」を含めて最大8個）
- 取り下げは、その項目を消すだけ
- サムネを差し替えたいときは `"thumbUrl": "https://..."` を足す

## 自動で飛ばされるもの

Actions のログに警告が出る。

- `worldId` の形式が違う
- 同じワールドの重複
- 非公開ワールド（ほかの人がポータルから入れないため。確認用にあえて載せるときは `"allowPrivate": true`）
- 112件を超えた分（アトラス 2048×2048 に入る上限）

## 手元で試す

```bash
pip install pillow
python scripts/build.py
```

`public/` に `worlds.json` と `thumbs.jpg` ができる。

## 定期更新

作者がサムネを変えたときのために、週に1回（月曜 6:00）作り直す。Actions の画面から手動でも実行できる。
