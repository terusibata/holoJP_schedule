from logging import getLogger, StreamHandler, DEBUG
logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(DEBUG)
logger.setLevel(DEBUG)
logger.addHandler(handler)
logger.propagate = False

import os
import time
from urllib.request import urlopen
from bs4 import BeautifulSoup
import requests
import urllib
from replit import db
import keep_alive
import re
import sys
import io
import json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from datetime import datetime, timedelta,date
#notionアップロード
from notion.client import NotionClient
from notion.block import TextBlock
from notion.block import DividerBlock
from notion.block import ImageBlock
from notion.block import QuoteBlock
from notion.block import CollectionViewPageBlock
from notion.block import VideoBlock

from uuid import uuid1
from random import choice

colors = [
  "default",
  "gray",
  "brown",
  "orange",
  "yellow",
  "green",
  "blue",
  "purple",
  "pink",
  "red",
]

def main():
  while True:
    print('Content-type: text/html; charset=UTF-8\n')
    URL = 'https://schedule.hololive.tv/simple/hololive'
    list_data = make_bs_obj(URL).find_all("a")

    today =str(datetime.today()).replace("-","")[:8]
    one_ago= str(datetime.today() - timedelta(days=1)).replace("-","")[:8]
    two_ago= str(datetime.today() - timedelta(days=2)).replace("-","")[:8]
    three_ago= str(datetime.today() - timedelta(days=3)).replace("-","")[:8]
    today = today[:4]+"-"+today[4:6]+"-"+today[6:8]
    one_ago = one_ago[:4]+"-"+one_ago[4:6]+"-"+one_ago[6:8]
    two_ago = two_ago[:4]+"-"+two_ago[4:6]+"-"+two_ago[6:8]
    three_ago = three_ago[:4]+"-"+three_ago[4:6]+"-"+three_ago[6:8]

    if not today in db.keys():
      db[today] = []
    if not one_ago in db.keys():
      db[one_ago] = []
    if not two_ago in db.keys():
      db[two_ago] = []
    
    if three_ago in db.keys():
      del db[three_ago]

    for holo_url in list_data:
      youtube_list = holo_url.get('href')
      res = re.match("https://www.youtube.com/watch", youtube_list)

      #記録済みの場合削除
      today_data = db[today]
      one_ago_data = db[one_ago]
      two_ago_data = db[two_ago]

      if (res != None):
        if youtube_list in today_data:
          continue
        elif youtube_list in one_ago_data:
          continue
        elif youtube_list in two_ago_data:
          continue

        time.sleep(5)
        print(youtube_list)

        Date,year,title,channel,description,img = youtube_data(youtube_list)

        #ジャンル
        if 'cover' in title:
          tag="歌ってみた"
        elif 'Cover' in title:
          tag="歌ってみた"
        elif '歌ってみた' in title:
          tag="歌ってみた"
        elif 'オリジナル' in title:
          tag="オリジナルソング"
        elif 'ショート' in title:
          tag="ショート動画"
        elif 'short' in title:
          tag="ショート動画"
        else:
          tag="配信アーカイブ"

        #内容タグ
        if title.find('【')>=0&title.find('】')>=0:
          search_tag_1=int(title.find('【'))+1
          search_tag_2=int(title.find('】'))
          title_tag=title[search_tag_1:search_tag_2]
          if title_tag=="":
              title_tag="その他"
        else:
          title_tag="その他"

        #notionのURL
        parent_page_url = "https://www.notion.so/terusibata/b60c1fa40b874876b36c0e9f0e3cad16" 
        page = client.get_block(parent_page_url)

        schema = {
            "title": {
              "name": "タイトル",
              "type": "title"
            },
            "channel_select": {
              "name": "チャンネル",
              "type": "multi_select"
            },
            "tag_select": {
              "name": "タイトルタグ",
              "type": "multi_select"
            },
            "tag": {
              "name": "動画タイプ",
              "type": "multi_select"
            },
            "URL":{
              "name": "動画リンク",
              "type": "url"
            },
            "date": {
              "name": "日付", 
              "type": "date"
            },
          }

        Collection_data = False
        for child in page.children :
          if child.title==year:
            Collection_data = True
            channelnamedata_id=child

        if not Collection_data:
          print("データベースを作成します")
          cvb = page.children.add_new(CollectionViewPageBlock)
          cvb.collection = client.get_collection(client.create_record("collection", parent=cvb, schema=schema))
          cvb.title = year
          view = cvb.views.add_new(view_type="gallery")
          row = cvb.collection.add_row()
        else:
          row = channelnamedata_id.collection.add_row()
          view = channelnamedata_id
        
        row.タイトル = title
        add_new_multi_select_value("タイトルタグ", title_tag ,view.collection, color=None)
        row.タイトルタグ = title_tag
        add_new_multi_select_value("チャンネル", channel ,view.collection, color=None)
        row.チャンネル = channel
        add_new_multi_select_value("動画タイプ", tag ,view.collection, color=None)
        row.動画タイプ = tag
        row.動画リンク = youtube_list
        row.日付 = Date

        #ページ内を作成する
        notion_up(row,img,youtube_list,description)
        #作成済みを保存
        db[today].append(youtube_list)
    
    #待機時間
    time.sleep(30)
  

def youtube_data(youtube_list):
  api_key =os.environ['api_key']
  YT_URL_FULL=youtube_list
  YT_URL = YT_URL_FULL.replace('https://www.youtube.com/watch?v=','')

  url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet&id={YT_URL}&key={api_key}"
  json_url = urllib.request.urlopen(url)
  json_data = json.loads(json_url.read())
  date_data = json_data["items"][0]["snippet"]["publishedAt"]
  date_full=(date_data.replace("-",""))[:8]
  Date = date(int(date_full[:4]),int(date_full[4:6]),int(date_full[6:8]))
  year = date_full[:4]+"年"
  title = json_data["items"][0]["snippet"]["title"]
  channel = json_data["items"][0]["snippet"]["channelTitle"]
  description = json_data["items"][0]["snippet"]["description"]

  thumbnails = ["maxres","standard","high","medium","default"]
  for thumbnail in thumbnails:
    try:
      img = json_data["items"][0]["snippet"]["thumbnails"][thumbnail]["url"]
      break
    except:
      print(f"{thumbnail}サイズはありませんでした")
      img = False

  return Date,year,title,channel,description,img


def add_new_multi_select_value(prop, value, collection,color=None):
    """`prop` is the name of the multi select property."""
    if color is None:
        color = choice(colors)

    collection_schema = collection.get("schema")
    prop_schema = next(
        (v for k, v in collection_schema.items() if v["name"] == prop), None
    )
    if not prop_schema:
        print("データベースに存在しない要素です")
        # raise ValueError(
        #     f'"{prop}" property does not exist on the collection!'
        # )
    if prop_schema["type"] != "multi_select":
        # raise ValueError(f'"{prop}" is not a multi select property!')
        print("このプロパティはマルチセレクトではありません")

    if "options" not in prop_schema: prop_schema["options"] = []
    dupe = next(
        (o for o in prop_schema["options"] if o["value"] == value), None
    )
    if dupe:
        # raise ValueError(f'"{value}" already exists in the schema!')
        print("すでにあるタグです")

    prop_schema["options"].append(
        {"id": str(uuid1()), "value": value, "color": color}
    )
    collection.set("schema", collection_schema)


def make_bs_obj(url):
  """
  BeautifulSoupObjectを作成
  """
  try:
    html = urlopen(url)
    logger.debug('access {} ...'.format(url))

    return BeautifulSoup(html,"html.parser")
  except urllib.error.HTTPError:
    return False
    

client = NotionClient(token_v2=os.environ['token_v2'])

def notion_up(page,img,youtube_list,description):
  if img:
    page.children.add_new(QuoteBlock, title='サムネイル')
    file_name = img[img.rfind("/")+1:]
    response = requests.get(img)
    image = response.content
    with open(file_name, "wb") as aaa:
      aaa.write(image)
    print(file_name+"で保存しました")
    page.children.add_new(ImageBlock).upload_file(f"./{file_name}")
    os.remove(f"./{file_name}")
    print("画像アップロード完了")
  else:
    print("画像はありませんでした")

  page.children.add_new(TextBlock, title='')
  page.children.add_new(DividerBlock)
  page.children.add_new(TextBlock, title='')

  page.children.add_new(QuoteBlock, title='youtube埋め込み')
  video = page.children.add_new(VideoBlock, width=700)
  video.set_source_url(youtube_list)
  print("埋め込み完了")

  page.children.add_new(TextBlock, title='')
  page.children.add_new(DividerBlock)
  page.children.add_new(TextBlock, title='')

  page.children.add_new(QuoteBlock, title='概要欄')
  page.children.add_new(TextBlock, title=description)

  print("概要欄書き込み完了")


keep_alive.keep_alive()

if __name__ == "__main__":
  main()