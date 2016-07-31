# -*- coding: utf-8 -*-
import leancloud
import json
import requests
import socket
import time
import datetime
import re
import oss2
from bs4 import BeautifulSoup

def login(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:47.0) Gecko/20100101 Firefox/47.0',
    }


    #proxy = {'http': '58.222.254.11'}

    r= requests.get(url,headers=headers,timeout = 40 )
    time.sleep(3)
    result = r.json()['results']

    return result

dict = {"Android": "Android",
        "iOS": "iOS",
        "休息视频": "Video",
        "福利": "Welfare",
        "拓展资源": "ExpandResource",
        "前端": "Web",
        "瞎推荐": "Random",
        "App": "App"
        }

def getDates():
    url = 'http://gank.io/api/day/history'
    result = login(url)
    return result#返回日期列表


def storeDates(date):#date为datetime格式的日期
    Date = leancloud.Object.extend("HistoryDate")
    re = Date()
    re.set('date', date)
    re.save()
    print (date)
    print ("已经存好啦~~")


#存储旧版的日期列表
def storeHistory():
    for date in getDates():
        d = datetime.datetime.strptime(date, '%Y-%m-%d')
        changetime = datetime.datetime.strptime("2016-06-25", '%Y-%m-%d')
        if d < changetime:  # 如果是旧版内容
            storeDates(d)


#从history表中获取新版内容的页面
def getAllPage(list):
    for date in list:
        getOnePage(date)


def getOnePage(date):
    # 获取每一天的日期，拼接到url中
    d = datetime.datetime.strptime(date, '%Y-%m-%d')
    changetime = datetime.datetime.strptime("2016-06-25", '%Y-%m-%d')
    if d > changetime:  # 如果是新版内容
        url = 'http://gank.io/api/history/content/day/' + str(d.year) + '/' + str(d.month) + '/' + str(d.day)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:47.0) Gecko/20100101 Firefox/47.0',
        }

        r = requests.get(url, headers=headers)
        content = r.json()['results'][0]['content']  # 把页面转为json格式读取
        day = r.json()['results'][0]['publishedAt']
        processContent(content, day)

        # 存储日期列表
        storeDates(d)  # date为json格式的日期  存储新版的日期

        # time.sleep(100000)




def processContent(content,day):


    soup=BeautifulSoup(content,'lxml')

    for i in soup.find_all(['h3','h2']):#找到h3,h2元素。从2016.2.25开始是h2标签

        module=(i.text).encode("utf-8")#每个版块的内容

        #i.text是unicode编码，要编码成utf-8格式

        if module in dict.keys():

            module=dict[module]#module存为字典对应的格式，作为lenancloud中存储的类型
            m=i.find_next("ul")#m为tag
            if m!=None:
                itemindex = 0#每个版块第几个推文
                for item in m.contents:#m为一个版块的所有内容
                    if item.name!=None:#item为每条推文

                        title = item.a.string  # 每条推文的名称
                        #print title
                        imageList = []  # 图片列表
                        url = item.a["href"]  # 输出内容的链接


                        s=item.prettify().encode('utf-8')

                        pattern = re.compile(r'</a>(.|\n)*\((.*?)\)(.|\n)*(<ul>|</li>)')
                        match = re.search(pattern,s)
                        author= match.group(2) if match and match.group(2)!=None and str(match.group(2))!='None' else ""


                        if item.find("ul") != None: # 如果有图片
                            # 输出图片列表

                            for image in item.ul.find_all("li"):  # 图片列表
                                if image.img!=None:
                                    s = image.find('img')['src']
                                    imageList.append(s)

                        #print day
                        #print title
                        #print author
                        #print type(author)
                        #print imageList
                        #print "====================="

                        # 存储每条数据
                        itemindex = itemindex + 1#推文索引
                        storeContent(module,title,author,url,imageList,day,itemindex)#存储数据





def storeContent(module,title,author,url,imageList,day,itemindex):
    #query = Resource.query
    #query_list = query.equal_to('identity',i["_id"]).find()
    #if query_list==[]:


    Resource = leancloud.Object.extend(module)
    # type有七种类型，分别存为7个Class格式
    re = Resource()
    #re.set('identity', i["_id"])
    #把string转化为python的时间格式
    #%f是微秒格式
    publishtime = datetime.datetime.strptime(day, '%Y-%m-%dT%H:%M:%S.%fZ')
    re.set('resourcePublished', publishtime)
    re.set('title', title)
    #re.set('module', module)
    re.set('url', url)
    # Android类的who字段有一个值为null，因此leanCloud默认存为Object类型,应当自己设置为string类型
    re.set('author', author)
    if imageList != []:
        imageList = changeImg(imageList, day, module,itemindex)  # 把图片转为阿里云存储格式
    re.set('image', imageList)
    re.save()


def changeImg(imageList,day,module,itemindex):
    #阿里云存储
    count = 1#图片列表元素的数目
    imgList =[]
    for imageurl in imageList:

        input = requests.get(imageurl)
        match = re.search(r'\w\.(png|gif|jpg).*',imageurl)

        if match :
            suffix = str(match.group(1))
        else:
            suffix='jpg'#默认后缀为jpg
        date = datetime.datetime.strptime(day, "%Y-%m-%dT%H:%M:%S.%fZ")  #字符串转为日期
        date = date.strftime('%Y-%m-%d')  # 将时间转换为字符串
        path = 'ITGank/' + date+ '-' + module + '-'+ str(itemindex) + '-' +str(count) + '.' +suffix

        print path
        bucket.put_object(path, input)#存到阿里云服务器上
        print "存好了"
        imgItem = "http://geekbing.oss-cn-hangzhou.aliyuncs.com/"+ path
        count = count+1
        imgList.append(imgItem)

    return imgList



def createPage():
    # 外包通缉令操作
    undoWanted()  # 撤销
    wanted()  # 重建

    getAllPage(getDates())#存储所有的新版内容和日期列表
    storeHistory()#存储旧版的日期列表


def updatePage():
    #外包通缉令操作
    undoWanted()#撤销
    wanted()#重建


#日期内容
    historyDate = leancloud.Object.extend("HistoryDate")
    query = historyDate.query
    query.descending("date")
    result = query.limit(100).find()#找到最新的100条日期记录

    hlist=[]
    for r in result:
        item = r.get("date").strftime('%Y-%m-%d')#将时间转换为字符串
        hlist.append(item)
    #print hlist


    dates = getDates()

    dlist= dates[0:50]#只获取最新的50个日期


    if set(dlist).issubset(set(hlist)):
        print "已经是最新的了呢，不用再更新了啦"

    else:
        print "卧槽，我错过了好几个亿！！！"
        for d in dlist:
            if d not in hlist:
                getOnePage(d)#获取一页内容
                print d


    #print hlist
    #print dlist
    #diff=list(set(dlist).difference(set(hlist)))#d中有而h没有的
    #print diff
    #getPage(diff)




#删除新版本的内容和日期列表
def undoPage():
    for module in dict.values():
        Resuorce = leancloud.Object.extend(module)
        #date 函数接收的日期格式必须是 2011-08-20T02:06:57.931Z 的 UTC 时间。
        sql_string = "select * from " + module + " where resourcePublished > date('2016-06-25T00:00:00.931Z')"

        #leancloud更新、删除要求一定要提供 objectId=xxx 的条件，只能根据 objectId 和其他条件来更新或者删除某个文档，不提供批量更新和删除。
        results = leancloud.Query.do_cloud_query(sql_string).results
        for result in results:

            del_string = "delete from " + module + " where objectId =?"
            leancloud.Query.do_cloud_query(del_string , result.id)


    #删除新版日期列表

    # date 函数接收的日期格式必须是 2011-08-20T02:06:57.931Z 的 UTC 时间。
    sql = "select * from HistoryDate where date > date('2016-06-25T00:00:00.931Z')"
    # leancloud更新、删除要求一定要提供 objectId=xxx 的条件，只能根据 objectId 和其他条件来更新或者删除某个文档，不提供批量更新和删除。
    results = leancloud.Query.do_cloud_query(sql).results
    for result in results:

        del_string = "delete from HistoryDate where objectId =?"
        leancloud.Query.do_cloud_query(del_string, result.id)


def wanted():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:47.0) Gecko/20100101 Firefox/47.0',
    }
    url="http://waibao.io/projects"
    r = requests.get(url, headers=headers, timeout=40)
    time.sleep(3)


    soup =BeautifulSoup(r.text,"lxml")
    items = soup.find_all(class_="card")#每个项目
    for item in items:
        url = "http://waibao.io"+item.a["href"]
        title = item.h4.string
        kind = item.find(class_="card-meta").contents[2].strip().strip("/").strip()#类型
        price = item.span.get_text().strip()
        detail = item.find(class_="card-body").string.strip()
        status = item.find(class_="card-footer").get_text().strip()


#存储
        Resource = leancloud.Object.extend("Wanted")
        # type有七种类型，分别存为7个Class格式
        re = Resource()
        # re.set('identity', i["_id"])
        # 把string转化为python的时间格式
        # %f是微秒格式

        re.set('url', url)
        re.set('title', title)
        re.set('kind', kind)
        re.set('price', price)
        re.set('detail', detail)
        re.set('status', status)
        re.save()

def undoWanted():
    Want = leancloud.Object.extend('Wanted')
    query_list = Want.query.limit(1000).find()
    leancloud.Object.destroy_all(query_list)


leancloud.init("Your APPID", "Your KEY")#我
auth = oss2.Auth('AliyunID', 'Aliyunkey')
bucket = oss2.Bucket(auth, 'oss-cn-hangzhou.aliyuncs.com', 'geekbing')


#createPage()#存储所有新版内容和日期列表
#undoPage()#撤销所有新版内容和新版日期列表,与createPage是对应相反的操作,
updatePage()#每天都要用一下我哦~~




