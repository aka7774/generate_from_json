# generate_from_json

## What is this?

- webui automatic1111用のScript
- 寝ている間とかに色んな指定でgenetate foreverしたい
- 1枚の絵に対して複数のパラメタを指定できる

## Usage

### Basic

- webui直下にpromptsディレクトリを作ってjsonを入れる
- フォルダに入れたjsonを全部なめて出力してくれる
- 複数のパラメタを指定したい時は値を配列にして列挙する(型に注意)

### 強調とprompt_count

- "prompt_count" が 2 以上の時、(hoge:1.0~1.5)のような書式で複数枚出力できる
  - "prompt_count" が 6 なら、1.0, 1.1, 1.2, 1.3, 1.4, 1.5が出る
  - 複数指定しても同時に増減する

### webpとupscale

- UIとjsonのどちらでも指定できる(json優先、チェックに関わらず有効)
  - jsonのupscaleには名前を指定することが出来ない(intでsd_upscalerのindexを指定)
- 本来の出力には全く影響を及ぼさない(原寸で出力される)

## ToDo List

- Hypernet, Hypernet strength, ENSDに対応したいが、processing.pyが対応してないのでしんどい。
- Highres. fixにも対応してない? してそうだけど指定の仕方がわからない。
- Scriptプルダウンの下に選択前からUIの残骸が表示されてしまっているが隠し方がわからない。
