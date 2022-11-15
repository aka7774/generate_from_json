# generate_from_json

## What is this?

- webui automatic1111用のScript
- 複数の絵をバッチ的に出せる(Prompts from fileの強化版)
- 1枚の絵に対して色んなParameterを指定した複数の画像を生成できる
  - SamplerやStepsやPromptの強調を変えたりして変化を確認できる

## 活用イメージ

- 1枚の絵に対して設定を詰めて追求する
- generate foreverしてガチャ放置する
- 新しいモデルに対して貯蔵してたプロンプトを一括で試す
などなど

## 制限事項

- hypernetの内部名称を取得するために、処理開始時に一度すべてのhypernetをロードする
  - models/hypernetworks 内にファイルが沢山あると時間がかかるかも

## 操作方法

- webui直下にpromptsディレクトリを作って拡張子をjsonにしたファイルを入れる
  - 書式とキーはexample.jsonを参考にする。
  - 値はPNG Infoから取ってくる。
- txt2imgのScriptで「Generate from json」を選択し、generateボタンを押す
- フォルダに入れたすべてのjsonファイルを対象に処理を行う
  - glob() のデフォルト順なのでたぶん昇順ソート

## jsonファイルについて

- keyは省略可能
  - 省略時はweb UIで指定した値が適用される
- valueはPNG Infoで取得できるParametersの値に準じている
  - モデル指定は sd_model_hash で8文字のハッシュ
  - サンプラー指定はラジオボタンで選択する部分の表示名
  - hypernetは内部名称(ファイル名ではないので注意)
    - "None" を指定すると None になる
  - こんなにバラバラになってるのは元仕様のせいです
- sd_model_hashとhypernetは先頭に書きましょう
  - 切り替わるたびにロードし直すので時間がかかります。
- txt2imgの画面に存在しない項目は、処理時にSettingsの値自体を書き換えるので注意
  - sd_model_hash
  - hypernet
  - hypernet_strength
  - eta
  - ensd

### 複数生成の指定

- value を配列にすると、それぞれの要素に対して画像を生成する
  - 型は厳密に記載してください(数値型なら""をつけない)
  - たとえば {"cfg_scale": [3,4,5], "steps": [20,28]} なら、3x2=6枚出す
  - 順番は以下のようになる。
    - {"cfg_scale": 3, "steps": 20}
    - {"cfg_scale": 3, "steps": 28}
    - {"cfg_scale": 4, "steps": 20}
    - {"cfg_scale": 4, "steps": 28}
    - {"cfg_scale": 5, "steps": 20}
    - {"cfg_scale": 5, "steps": 28}

### prompt_countによる強調変化機能

- "prompt_count" が 2 以上の時、(hoge:1.0~1.5)のような書式で複数枚出力できる
  - "prompt_count" が 6 なら、1.0, 1.1, 1.2, 1.3, 1.4, 1.5が出る
  - 複数個所で強調を指定しても同時に増減する

## FAQ的な

### 1つのjsonでいろんな絵を出したい

- いちおう prompt を配列にすることが出来る
  - 二人の女の子のどっちが映えるか比較するみたいな使い方を想定
  - ex. "prompt": ["red hair", "blue hair"],
  - このときは prompt_count は不要だし併用はできない
- でもあくまで1ファイルで1枚の絵が完成するイメージ
  - 複数のparametersを1ファイルにまとめる機能とかは考えてない
  - 配列を一次元増やすような改造はそんなに難しくないような

## 対応しなさそうなリスト

- Highres. fixには対応できそうだけど使う予定がないので実装してない。
- Extensionにするほどユーザーが増えそうなイメージが無いのでとりあえずScriptのまま。
