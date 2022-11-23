# generate_from_json

## Install

- Script Extensions for webui automatic1111
  - Extenstions tab - Install from URL
  - https://github.com/aka7774/generate_from_json.git

- 手動でScriptsに入れても動きます
  - Extensionsとして使う場合は Scripts/generate_from_json.pyは消してください

- It will work even if you put it in Scripts manually.
  - If you use it as Extensions, please delete Scripts/generate_from_json.py  

## これは何か What is this?

- 複数の絵をバッチ的に出せる(Prompts from fileの強化版)
- 1枚の絵に対して色んなParameterを指定した複数の画像を生成できる
  - SamplerやStepsやPromptの強調を変えたりして変化を確認できる

- Generate multiple pictures in batch (enhanced version of prompts from file)
- Generate multiple images with various parameters for a single picture.
  - You can change the Sampler, Steps, emphasis of Prompts and more to see the changes.

## 活用イメージ Image of use

- 1枚の絵に対して設定を詰めて追求する
- generate foreverしてガチャ放置する
- 新しいモデルに対して貯蔵してたプロンプトを一括で試す

- Pursuing a single picture with a lot of settings.
- Generate forever like lootbox
- Try out all stored prompts for a new model at once, etc.


## 制限事項 Limitations

- Reported https://github.com/AUTOMATIC1111/stable-diffusion-webui/issues/4824

- hypernetの内部名称を取得するために、処理開始時に一度すべてのhypernetをロードする
  - models/hypernetworks 内にファイルが沢山あると時間がかかるかも
  
- Load all hypernetworks once at the start of processing to get the internal name of hypernetworks.
  - It may take a long time if there are many files in models/hypernetworks

## 操作方法 How to operate

- webui直下にpromptsディレクトリを作って拡張子をjsonにしたファイルを入れる
  - 書式とキーはexample.jsonを参考にする。
  - 値はPNG Infoから取ってくる。
- txt2imgのScriptで「Generate from json」を選択し、generateボタンを押す
- フォルダに入れたすべてのjsonファイルを対象に処理を行う
  - glob() のデフォルト順なのでたぶん昇順ソート

- Create a prompts directory under webui and put in a file with json extension.
  - Refer to example.json for format and keys.
  - Get the value from PNG Info.
- Select "Generate from json" in Script of txt2img and press generate button.
  - All json files in the folder will be processed.
    - Sort in ascending order, probably because that is the default order of glob()

## jsonファイルについて About json files

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
  
- key can be omitted.
  - If omitted, the value specified in the web UI is applied.
- value is the same as the Parameters value that can be obtained from PNG Info
  - Model specification is an 8-character hash using sd_model_hash.
  - Sampler is the display name of the part to be selected by radio buttons.
  - hypernet is the internal name (note that it is not a file name)
    - "None" is used to specify None
  - The reason it's all so disjointed is due to the original spec.
- sd_model_hash and hypernet should be written at the top
  - It takes time to reload each time it switches.
- Note that if an item does not exist in the txt2img screen, the Settings value itself will be rewritten during processing.
  - sd_model_hash
  - hypernet
  - hypernet_strength
  - eta
  - ensd

### 複数生成の指定 Specify multiple generation

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

- If value is an array, an image is generated for each element.
  - Type must be strictly specified (no "" if it is a numeric type)
  - For example, if {"cfg_scale": [3,4,5], "steps": [20,28]}, 3x2=6 images are generated
    - The order would be as follows.

### prompt_countによる強調変化機能 Emphasis change function by prompt_count

- "prompt_count" が 2 以上の時、(hoge:1.0~1.5)のような書式で複数枚出力できる
  - "prompt_count" が 6 なら、1.0, 1.1, 1.2, 1.3, 1.4, 1.5が出る
  - 複数個所で強調を指定しても同時に増減する

- When "prompt_count" is 2 or more, multiple images can be output in a format such as (hoge:1.0~1.5)
  - If "prompt_count" is 6, then 1.0, 1.1, 1.2, 1.3, 1.4, 1.5 are output.
  - Emphasis can be specified in multiple places, but they increase or decrease at the same time.

## FAQ

### 1つのjsonでいろんな絵を出したい

- いちおう prompt を配列にすることが出来る
  - 二人の女の子のどっちが映えるか比較するみたいな使い方を想定
  - ex. "prompt": ["red hair", "blue hair"],
  - このときは prompt_count は不要だし併用はできない
- でもあくまで1ファイルで1枚の絵が完成するイメージ
  - 複数のparametersを1ファイルにまとめる機能とかは考えてない
  - 配列を一次元増やすような改造はそんなに難しくないような
  
- I want to produce various pictures in one json.
  - I can make an array of prompts.
  - Assuming a use like comparing which of two girls looks better
  -  ex. "prompt": ["red hair", "blue hair"],
  - In this case, prompt_count is not necessary and cannot be used together.
- But it is just an image that one picture is completed in one file.
  - I'm not thinking of a function to combine multiple parameters into one file.
  - I don't think it's so difficult to modify it to add one dimension to the array.

## 対応しなさそうなリスト

- Highres. fixには対応できそうだけど使う予定がないので実装してない。
