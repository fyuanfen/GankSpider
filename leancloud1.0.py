# -*- coding: utf-8 -*-
import leancloud
import urllib2
import json
import cookielib
import socket
import time
import datetime


def getPage(pagesize=None):
    # 页面大小默认为20

    if pagesize == None:
        pagesize="20"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:47.0) Gecko/20100101 Firefox/47.0',
    }

    cj=cookielib.MozillaCookieJar()#cookie
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))

    dict={"Android" : "Android",
        "iOS" : "iOS",
        "休息视频" : "Video",
        "福利" : "Welfare",
        "拓展资源" : "ExpandResource",
        "前端" : "Web",
        "瞎推荐" : "Random",
        "App" : "App"
    }




    for i in dict:#对于每个版块的内容
        print("===============%s==================" % i)
        pageindex = "1"
        while True:
            try:
                # 构建URL

                url = "http://gank.io/api/data/" + i + "/" + pagesize + "/" + pageindex

                request = urllib2.Request(url,headers = headers)
                response= opener.open(request,timeout=10)
                result=response.read()

                if isEmpty(result):#如果当前读取页面为空
                    break
                storeData(dict[i],result)#若不空则把数据存储到leancloud
                print ("第%s页存储成功" % pageindex)
                pageindex = str(int(pageindex) + 1)

        # 无法连接，报错
            except socket.error, e:
                print "建立socket错误：%s" % e
                #抓住错误，让他睡几秒再来
                print("睡个十秒，再来~~~")
                time.sleep(100)

            except urllib2.URLError, e:
                if hasattr(e, "reason"):
                    print ("连接失败,错误原因", e.reason)
                    return None
        opener.close()
        print("========================================")
        print("<%s>'版块终于存完了，累死老子了，TAT"% i)



#判断读取的页面是否为空
def isEmpty(result):
    d = json.loads(result)
    if d["results"]==[]:
        return True
    return False



def storeData(type,response):
    d=json.loads(response)
    imageList=[]
    for i in d["results"]:
        #query = Resource.query
        #query_list = query.equal_to('identity',i["_id"]).find()
        #if query_list==[]:

        Resource = leancloud.Object.extend(type)
        # type有七种类型，分别存为7个Class格式
        re = Resource()
        #re.set('identity', i["_id"])

        #把string转化为python的时间格式
        #%f是微秒格式
        #createtime = datetime.datetime.strptime(i["createdAt"], '%Y-%m-%dT%H:%M:%S.%fZ')
        #re.set('resourceCreated', createtime)

        publishtime = datetime.datetime.strptime(i["publishedAt"], '%Y-%m-%dT%H:%M:%S.%fZ')
        changetime = datetime.datetime.strptime("2016-06-25", '%Y-%m-%d')
        if publishtime < changetime:#如果是旧版内容

            re.set('resourcePublished', publishtime)
            re.set('title', i["desc"])
            #if "source" in d.keys():#有些数据没有source字段
            #   re.set('source', i["source"])
            #re.set('type', i["type"])
            re.set('url', i["url"])
            #re.set('used', i["used"])
            if i["who"]== None:
                i["who"]=""
            # Android类的who字段有一个值为null，因此leanCloud默认存为Object类型,应当自己设置为string类型
            re.set('author', i["who"])
            re.set('image', imageList)
            re.save()

        else:
            print publishtime
            print ("哎呀，这个是新版的，奴家收拾不了,用2.0版本存了啦~~~")



#APPID和APPKEY
leancloud.init("Your APPID", "Your KEY")#我
page=getPage()

