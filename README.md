# ad2exo
ニコニ広告の情報を取得し、aviutlの拡張編集に広告者紹介画面を作ってくれるツール

# ダウンロードの仕方
右上にある"Code"をクリックし、"Download ZIP"を選んでください。

# 使い方
python3系をインストールする(python3でぐぐればトップにやり方が出るでしょう)  
top5.exo  
others.exo  
を用意する。  
（サンプルを同梱しておきます）  
ad2exo.pyを実行する。  

# もととなるexoの作り方
aviutlの拡張編集で、それっぽい画面を作る。  
右クリック＞ファイル＞オブジェクトファイルのエクスポート  
テキストオブジェクトのテキストに含まれる、以下の文字を置換します。  
 #N1# 名前  
 #C1# コメント  
 #P1# 貢ポイント  
 ※数字部分は1～の数字が入り、貢ポイントによる順位を表します  
  
サンプルを見て、実際に動かしてみて、挙動を察してください。  
またはソースコード読んで。  

# 貢トップ5を特別扱いするか
top5.exoがある場合、貢のトップ5人はそのファイルをもとに画面が作られ、残りがothers.exoをもとに作られます。  
top5.exoがない場合、トップ5も含めて全員がothers.exoをもとに作られます。  

# FAQ

## 端数が出た時に、置換元の文字が残っちゃうんだけど？
仕様です。
どうせ端数が出た時に残っちゃう「貢」「様」といった文字も削除しなくちゃいけないだろうし、それなら空文字とかに置換するよりも分かりやすいと判断しました。

## 同じ人が複数種類のコメントを残している場合、どうなる？
コメントのある広告のうち、最も新しいもののコメントのみを採用します。

