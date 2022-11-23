# config.json

- ガチャするのには使わんはず
- 生成したものを一括で拡大したいだけならExtrasのBetch from Directoryのほうが便利
- 単にwebpで出したいだけならSettingsのFile format for imagesにwebpと入れれば済む

## 概要

- webp形式で出力できる
  - ファイルサイズが少なくなる
  - PNG Infoは失われる
- 本来の出力には全く影響を及ぼさない
  - 本来の出力先にはwebp出力の有無を問わず出力される
- upscaleはwebpに対してのみ有効
  - 本来の出力に対してはupscaleは効かない
- 文字入れ機能
- webp出力先でファイル名が重複した場合のみ、ファイル名にタイムスタンプを付与

## 使い方

- extensions/generate_from_json/Examples/config.json を extensions/generate_from_json/ に移動する
- 中身を編集する
- Generateする
- extensions/generate_from_json/webp に加工後の画像が出力される

### 中身

webp設定
- "webp_quality": int webpの画質。

拡大機能
- "upscaler": str upscalerの名前。Extrasを参照。
- "upscaling_resize": float リサイズ倍率。こっちが優先。
- "upscaling_resize_w": int リサイズ幅。
- "upscaling_resize_h": int リサイズ高さ。
- "upscaling_crop": int クロップするかどうか。0/1かな?

文字入れ機能
-	"imagefont_truetype": str Windowsなら C:\Windows\fonts にあるファイル名。
-	"imagefont_truetype_index": int ttcの時に何番目のttfを使うか。
-	"imagefont_truetype_size": int フォントサイズ。たぶんピクセル。
-	"draw_text_left": int 文字の左位置
-	"draw_text_top": int 文字の上位置
-	"draw_text_color": str 文字の色
-	"draw_text": str 表示させたい文字
