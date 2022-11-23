# CHANGELOG

- 利用方法に影響のある変更点をまとめていきます。

## Extensions対応

- 2022-11-23頃からExtensionsとして動作するようになりました。

- Scriptsとして使う方法はサポートされなくなります。
  - Scripts/generate_from_json.pyは削除してください。

- JSONを入れるディレクトリは extensions/generate_from_json/json/ になりました。
  - 以前はデフォルトが prompts で、変更可能でした。

- WEBPが出力されるディレクトリは extensions/generate_from_json/webp/ になりました。
  - 以前はデフォルトが outputs_webp で、変更可能でした。

## config.json対応

- webp出力設定をUIから行う機能は廃止になりました。
- config.jsonを用意してください。
- 詳細は CONFIG.md をお読みください。
