# AI 向けの作業ルール

このリポジトリは VRChat ワールド「フォトポータル」「写真家のアトリエ」のポータルメニューが読む掲載リスト。頼まれる作業はほぼ「ワールドの追加・取り下げ・並べ替え」で、触るのは `data/gallery.json`（写真ギャラリー）と `data/spot.json`（撮影スポット）だけ。書き方は README のとおり。

## コミット

- 作者は `seitokairuri <232708746+seitokairuri@users.noreply.github.com>` にする。本人の Gmail などの実アドレスは公開リポジトリなので絶対に使わない
  - 未設定なら `git config user.name seitokairuri` と `git config user.email 232708746+seitokairuri@users.noreply.github.com` を先に実行する
- コミットメッセージは日本語で、何を追加・削除したか分かるように書く（例：「撮影スポットに〇〇を追加」）
- `main` に直接 push してよい。push すると Actions が自動で公開し直す

## 追加・取り下げのとき

- ワールドの URL（`https://vrchat.com/home/world/wrld_...`）から `worldId` だけ取り出して `{ "worldId": "wrld_..." }` を足す。名前やサムネは自動で入るので、頼まれない限り書かない
- 「ギャラリー」「展示」なら `gallery.json`、「撮影」「スポット」なら `spot.json`。どちらか分からなければ聞く
- 取り下げは該当項目を消すだけ。ワールド名で頼まれたら、`title` か `_memo` で探し、無ければ VRChat のワールドページで名前を確かめてから消す
- 並び順は配列の順。指定がなければ末尾に足す
- 編集後に JSON として壊れていないか確かめる（`python -c "import json;json.load(open('data/spot.json',encoding='utf-8'))"` など）
- push 後、Actions の実行が成功したか、警告（非公開ワールド・重複など）が出ていないかを見て報告する

## 触らないもの

- `scripts/`・`.github/workflows/`・`public/` は、頼まれない限り変更しない
- 公開される URL（`https://yaeza-kura.github.io/photo-portal/<名前>/worlds.json`）はワールド側に埋め込んであるので、`data/` のファイル名を変えたり消したりしない
