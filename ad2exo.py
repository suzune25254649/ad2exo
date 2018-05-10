import urllib.request
import json
import copy
import re
import os
import sys
from pprint import pprint
from datetime import datetime

TOP5_SOURCE_EXO = 'top5.exo'
OTHERS_SOURCE_EXO = 'others.exo'
OUTPUT_DIR = 'output'

#トップ5exoではないファイルについて、1つのexoファイルに全広告者の情報をまとめるかのフラグ
#まとめる場合、必要な数だけオブジェクトが時系列順に増える
FLG_OTHER_ONE_DEST_EXO = False

API_LIMIT = 100


###############################################################################################################
#	関数定義
###############################################################################################################

#---------------------------------------
#文字列置換用の関数
# '#N%d#' -> 順位 %d位の人のName
# '#C%d#' -> 順位 %d位の人のComment(コメントが存在しない場合は空文字列になる)
# '#P%d#' -> 順位 %d位の人のPoint(貢の値)
#---------------------------------------
def macro_replacer(matchobj):
	global histories
	global offset
	index = offset + int(matchobj.group(2)) - 1

	if len(histories) <= index:
		return matchobj.group(0)

	if 'N' == matchobj.group(1):
		return histories[index]['advertiserName']
	elif 'C' == matchobj.group(1):
		if 'message' in histories[index]:	return histories[index]['message']
		else:								return ''
	elif 'P' == matchobj.group(1):
		return str(histories[index]['contribution'])
	else:
		return matchobj.group(0)

#---------------------------------------
#コンバート元のexoファイルに置換処理を行い、コンバート済みexoファイルを出力する.
#---------------------------------------
def convert_exo(lines):
	outputs = []
	for line in lines:
		if line.startswith('text='):
			line = bytes.fromhex(line[5:-1]).decode('utf-16')
			line = line[0:line.find('\0')]
			line = re.sub(r'#(N|C|P)([1-9][0-9]*)#', macro_replacer, line)
			line = line[0:1024].ljust(1024, '\0')
			line = line.encode('utf-16LE').hex()
			line += '\n'
			outputs.append('text=' + line)
		else:
			outputs.append(line)
	return outputs

#---------------------------------------
#コンバート元のexoファイルをサーチし、そのexoの中で最も順位数字の大きいものを探し、その数字を返します
#---------------------------------------
def search_max_rank(lines):
	num = 0
	for line in lines:
		if line.startswith('text='):
			line = bytes.fromhex(line[5:-1]).decode('utf-16')
			line = line[0:line.find('\0')]
			matches = re.findall(r'#(N|C|P)([1-9][0-9]*)#', line)
			for item in matches:
				num = max(num, int(item[1]))
	return num


###############################################################################################################
#	メイン実行
#	1) 動画IDの入力待ち
#	2) APIを使い広告者のデータをすべて取得する
#	3) 同じ人物の広告をまとめる
#	4) TOP5用のexoファイルの置換処理を行い、置換したファイルを出力する
#	5) 6位以降用のexoファイルも同様にする
###############################################################################################################

print('Input video ID. for example : sm33134812')
video_id = input('>>>  ')

#APIにアクセスし、すべての広告情報を取得する
#旧仕様には未対応
histories = []
while True:
	with urllib.request.urlopen("https://api.nicoad.nicovideo.jp/v1/contents/video/%s/histories?offset=%s&limit=%s" % (video_id, len(histories), API_LIMIT)) as res:
		text = res.read().decode("utf-8")
		js = json.loads(text)

		if 200 != js['meta']['status']:
			break

		histories.extend(js['data']['histories'])

		#print(json.dumps(js, sort_keys=True, indent=2, ensure_ascii=False))

		if API_LIMIT != len(js['data']['histories']):
			break

#同じ人物の広告を1つにまとめる
#基本的に同じuserIdでまとめるが、匿名の場合は名前でまとめる
if True:
	users = {}
	anonymice = {}

	for item in histories:
		if "userId" in item:
			index = "uid%010d" % item["userId"]
			if index in users:
				target = users[index]
				target["startedAt"] = item["startedAt"]
				target["adPoint"] += item["adPoint"]
				target["contribution"] += item["contribution"]
			else:
				users[index] = copy.deepcopy(item)
		else:
			index = 'ano_' + item["advertiserName"]
			if index in anonymice:
				target = anonymice[index]
				target["startedAt"] = item["startedAt"]
				target["adPoint"] += item["adPoint"]
				target["contribution"] += item["contribution"]
			else:
				anonymice[index] = copy.deepcopy(item)
	histories = list(users.values())
	histories.extend(list(anonymice.values()))

s = sorted(histories, key=lambda x:x['startedAt'])
s = sorted(s, key=lambda x:x['contribution'], reverse=True)
histories = s

#出力ディレクトリの名前を決定する
OUTPUT_DIR += '_' + datetime.now().strftime("%Y%m%d-%H%M%S")
os.mkdir(OUTPUT_DIR)

#トップ5用のexoファイルを処理する
offset = 0
try:
	with open(TOP5_SOURCE_EXO, 'r') as f:
		lines = f.readlines()
	outputs = convert_exo(lines)
	offset += 5

	with open(OUTPUT_DIR + '/' + TOP5_SOURCE_EXO, 'w') as outfile:
		outfile.write(''.join(outputs))

except IOError as e:
	print("\"%s\"が開けません。\nトップ5ユーザーも、他のユーザーと同列に扱います。\n" % TOP5_SOURCE_EXO)


#トップ5以外のexoファイルを処理する
try:
	with open(OTHERS_SOURCE_EXO, 'r') as f:
		lines = f.readlines()

	num = search_max_rank(lines)
	if num <= 0:
		print("\"%s\"の中に1つも置換対象が存在しません。\n" % OTHERS_SOURCE_EXO)
		sys.exit()

	if False:
		#複数のexoに出力するパターン
		while offset < len(histories):
			outputs = convert_exo(lines)
			with open(OUTPUT_DIR + '/' + str(offset + 1) + '_' + OTHERS_SOURCE_EXO, 'w') as outfile:
				outfile.write(''.join(outputs))
			offset += num

	else:
		#1つのexoとして出力するパターン
		header = []
		i = 0
		while True != lines[i].startswith('[0]'):
			header.append(lines[i])
			i += 1

		del lines[0:i]

		#オブジェクト番号で、一番大きな数字を探す
		#オブジェ番号にこの値(見つけた数字+1)を足していくことで、同じオブジェ番号が現れないようにする
		add_objno = 0

		for line in lines:
			matches = re.findall(r'^\[([0-9]+)', line)
			for item in matches:
				add_objno = max(add_objno, int(item))
		add_objno += 1

		#exoの長さを取得する。2つ目以降のstart, end にこれを足すことで、時系列方向にオブジェクトを並べることができる
		add_length = 1
		for line in header:
			if line.startswith('length='):
				add_length = int(line[7:-1])
				break

		i = 0
		outputs = []
		while offset < len(histories):
			temp = convert_exo(lines)

			#オブジェクトの以下のパラメータに修正を行う
			#
			#オブジェクト番号
			#start
			#end
			for k in range(len(temp)):
				temp[k] = re.sub(r'^\[([0-9]+)', lambda match: '[' + str(int(match.group(1)) + (add_objno * i)), temp[k])
				temp[k] = re.sub(r'^start=([0-9]+)', lambda match: 'start=' + str(int(match.group(1)) + (add_length * i)), temp[k])
				temp[k] = re.sub(r'^end=([0-9]+)', lambda match: 'end=' + str(int(match.group(1)) + (add_length * i)), temp[k])

			outputs.extend(temp)
			offset += num
			i += 1

		with open(OUTPUT_DIR + '/' + OTHERS_SOURCE_EXO, 'w') as outfile:
			outfile.write(''.join(header))
			outfile.write(''.join(outputs))

except IOError as e:
	print("\"%s\"が開けないためスキップします。\n" % OTHERS_SOURCE_EXO)

sys.exit()




