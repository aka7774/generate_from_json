# generate_from_json

## What is this?

- webui automatic1111用のScript
- 1枚の絵に対して色んなParameterを指定した複数の画像を生成できる
  - SamplerやStepsやPromptの強調を変えたりして変化を確認できる
- generate foreverして放置すればガチャにも便利

## 操作方法

- webui直下にpromptsディレクトリを作って拡張子をjsonにしたファイルを入れる
- txt2imgのScriptで「Generate from json」を選択し、generateボタンを押す
- フォルダに入れたすべてのjsonファイルを対象に処理を行う
  - glob() のデフォルト順なのでたぶん昇順ソート

## jsonファイルについて

- example.json に記載されているkeyが使用できる
  - 省略時はweb UIで指定した値が適用されるはず
  - 将来対応可能なのは modules/processing.py の Processed の js にあるもの
- value を配列にすると、それぞれの要素に対して画像を生成する
  - 型は厳密に記載してください(数値型なら""をつけない)
  - たとえば {"cfg_scale": [3,4,5], "steps": [20,28]} なら、3x2=6枚出す

### prompt_countによる強調変化機能

- "prompt_count" が 2 以上の時、(hoge:1.0~1.5)のような書式で複数枚出力できる
  - "prompt_count" が 6 なら、1.0, 1.1, 1.2, 1.3, 1.4, 1.5が出る
  - 複数個所で強調を指定しても同時に増減する

## webpとupscale

- webp形式で出力できる(デプロイ用機能なので不要ならスルー推奨)
  - ファイルサイズが少なくなる
  - PNG Infoは失われる
- 本来の出力には全く影響を及ぼさない
  - 本来の出力先にはwebp出力の有無を問わず出力される
- upscaleはwebpに対してのみ有効
  - 本来の出力に対してはupscaleは効かない
- UIとjsonのどちらでも指定できる(json優先、UIのcheckboxに関わらず有効)
  - 制限: jsonのupscaleには名前を指定することが出来ない(intでsd_upscalerのindexを指定)

## FAQ的な

### 1つのjsonでいろんな絵を出したい

- いちおう prompt を配列にすることが出来る
  - 二人の女の子のどっちが映えるか比較するみたいな使い方を想定
  - ex. "prompt": ["red hair", "blue hair"],
  - このときは prompt_count は不要だし併用はできない
- でもあくまで1ファイルで1枚の絵が完成するイメージ
  - 複数のparametersを1ファイルにまとめる機能とかは考えてない
  - 配列を一次元増やすような改造はそんなに難しくないような

## ToDo List

- Hypernet, Hypernet strength, ENSDに対応したいが、processing.pyが対応してないのでしんどい。
- Highres. fixには対応できそうだけどしてない。
- Extensionにするほどユーザーが増えそうなイメージが無いのでとりあえずScriptのまま。
