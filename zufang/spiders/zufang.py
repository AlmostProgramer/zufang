import scrapy
from bs4 import BeautifulSoup
from zufang.items import ZufangItem
class zufang(scrapy.Spider):
    #spider name
    name = 'zufang'
    baseUrl = 'http://gz.zu.fang.com/'
    allUrlList = []     #所有区域所有页面的url
    headUrlList = []    #各个区域的首页url
    allowed_domains = ['fang.com']
    def start_requests(self):
        url = self.baseUrl
        yield scrapy.FormRequest(url=url,callback=self.head_url_callback)

    #首页中有每个地区的头部url,解析首页中的信息来获取各个地区的头部url
    #（只运行一次）
    def head_url_callback(self,response):
        soup = BeautifulSoup(response.body,'html5lib')
        #小区所在标签
        d1 = soup.find_all('dl',attrs={'id':'rentid_D04_01'})
        my_as = d1[0].find_all('a')
        for my_a in my_as:
            #不限地区，url就是为base_url
            if my_a.text == '不限':
                self.headUrlList.append(self.baseUrl)
                self.allUrlList.append(self.baseUrl)
                continue
            #清楚周边地区的数据
            if "周边" in my_a.text:
                continue
            print(my_a['href'])
            print(my_a.text)
            self.allUrlList.append(self.baseUrl+my_a['href'])
            self.headUrlList.append(self.baseUrl+my_a['href'])
        print(self.allUrlList)
        url = self.headUrlList.pop(0)#pop出索引为0的元素
        yield scrapy.Request(url,callback=self.all_url_callback,dont_filter=True)

    #遍历整个headurllist,找出每个小区首页中的总页数，按照相应规律append进allurllist中，
    #直到遍历完，则开始解析allurllist
    def all_url_callback(self,response):
        soup = BeautifulSoup(response.body,'html5lib')
        #找到总页数
        div = soup.find_all('div',attrs={'id':'rentid_D10_01'})
        span = div[0].find_all('span')
        span_text = span[0].text
        #遍历总页数
        for index in range(int(span_text[1:len(span_text)-1])):
            #当地区为不限，url的拼接不一样
            if response.url == self.baseUrl:
                self.allUrlList.append(response.url+"house/i3"+str(index+1)+"/")
                continue
            self.allUrlList.append(response.url+'i3'+str(index+1)+'/')
        #如果解析完headurllist,开始解析allurllist
        if len(self.headUrlList)==0:
            url = self.allUrlList.pop(0)
            yield scrapy.Request(url,callback=self.parse,dont_filter=True)
        #解析下一个headurllist
        else:
            url = self.headUrlList.pop(0)
            yield scrapy.Request(url,callback=self.all_url_callback,dont_filter=True)

    #解析整个allurllist
    def parse(self, response):
        self.logger.info("=======================")
        soup = BeautifulSoup(response.body,'html5lib')
        divs = soup.find_all("dd",attrs={'class':'info rel'})
        for div in divs:
            ps = div.find_all('p')
            #捕获异常，因为页面中有些数据没有被填写完整，或者插入了一条广告，
            #则会没有相应的标签，所以会报错(important)
            try:
                roomMsg = ps[1].text.split('|')
                area = roomMsg[2].strip()[:len(roomMsg[2])-1]
                item = ZufangItem()
                item['title'] = ps[0].text.strip()
                item['rooms'] = roomMsg[1].strip()
                item['area'] = int(float(area))
                item['price'] = int(ps[len(ps) - 1].text.strip()[:len(ps[len(ps) - 1].text.strip()) - 3])
                item['address'] = ps[2].text.strip()
                item['traffic'] = ps[3].text.strip()
                if (self.baseUrl+"house/") in response.url:
                    item['region'] = "不限"
                else:
                    item['region'] = ps[2].text.strip()[:2]
                item['direction'] = roomMsg[3].strip()
                #输出可视化，看信息是否正确
                print(item)
                yield item
            except Exception as e:
                print(e)
                print('awful,excepiton happened!')
                continue
        #遍历整个allurllist
        if len(self.allUrlList)!=0:
            url = self.allUrlList.pop(0)
            yield scrapy.Request(url,callback=self.parse,dont_filter=True)

