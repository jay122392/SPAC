import pandas as pd #数据表处理模块
from selenium.webdriver.common.keys import Keys #模拟浏览器组成模块
import pandas_datareader as pdr #纳斯达克股票symbol读取工具
from selenium import webdriver as wd #模拟浏览器引擎
import bs4 as bs #网页爬虫模块
import requests #网页爬虫请求器
from selenium.webdriver.support.ui import WebDriverWait #模拟浏览器自动等待设置
import time #自动化计时器
import schedule #自动化定时工具


#############更新新闻数据库#####################
def get_news():
    keyword_checklist = [] #新闻标题关键词检索
    driver = wd.Chrome()
    driver.set_page_load_timeout(15) #加载限时15秒
    symbol_list = pd.read_csv('symbols.csv')
    lists = symbol_list['symbols']  #读取股票代码列表
    all_lists = list(symbol_list['symbols'])
    updatelist = [] #准备放当日更新新闻的link

    for ticker in lists: #对每个股票循环操作
        try:
            old_news = pd.read_csv('{}_news.csv'.format(ticker)) #上次存储的数据
        except:
            old_news = pd.DataFrame()
            old_news['date'] = []
            old_news['title'] = []
            old_news['link'] = []
            old_news.to_csv('{}_news.csv'.format(ticker))
    
        old_len = len(old_news['link']) #存储的新闻条数
        news_file = pd.DataFrame() #初始化数据表
        date=[] #准备存储数据的空列表
        title=[]
        link=[]
        url = 'http://data.eastmoney.com/notices/stock/{}.html'.format(ticker) #个股东方财富网公告页
        try:
            driver.get(url) #模拟浏览器登陆公告页面，加载
        except:
            driver.execute_script('window.stop()') #停止加载 跳过

        try:
            element = driver.find_element_by_id('dt_1')
            trs = element.find_elements_by_tag_name('tr') #找到发表时间，标题，pdf链接网址所在位置
            for tr in trs[1:]: #对每一条新闻循环
                title.append(tr.find_elements_by_tag_name('td')[0].text) #标题
                date.append(tr.find_elements_by_tag_name('td')[1].text) #日期
                link.append(tr.find_element_by_tag_name('a').get_attribute('href')) #网址
        except:
            continue
        
        news_file['date'] = date
        news_file['title'] = title
        news_file['link'] = link
        news_file.to_csv('{}_news.csv'.format(ticker)) #存成新的csv文件
        new_len = len(link) #本次新闻条数
        print(ticker)
        print(new_len)

        ###如果新闻不在xxxxU中
        if new_len == 0:
            if ticker[-2] == '.' or ticker[-2] =='$':
                ticker = ticker[0:3]
            else:
                ticker = ticker[0:4]
            print(ticker)
            all_lists.append(ticker)
            url = 'http://data.eastmoney.com/notices/stock/{}.html'.format(ticker)
            try:
                driver.get(url) #模拟浏览器登陆公告页面，加载
            except:
                driver.execute_script('window.stop()') #停止加载 跳过

            try:
                element = driver.find_element_by_id('dt_1')
                trs = element.find_elements_by_tag_name('tr') #找到发表时间，标题，pdf链接网址所在位置
                for tr in trs[1:]: #对每一条新闻循环
                    title.append(tr.find_elements_by_tag_name('td')[0].text) #标题
                    date.append(tr.find_elements_by_tag_name('td')[1].text) #日期
                    link.append(tr.find_element_by_tag_name('a').get_attribute('href')) #网址
            except:
                continue

            news_file['date'] = date
            news_file['title'] = title
            news_file['link'] = link
            news_file.to_csv('{}_news.csv'.format(ticker)) #存成新的csv文件
            new_len = len(link) #本次新闻条数

        if old_len < new_len: #如果新的条数比老的多，说明更新了
            print('{}新闻更新！'.format(ticker)) #提示更新
            len_update = new_len - old_len #更新条数
            for i in range(len_update): #准备检索所更新的几条新闻
                for keyword in keyword_checklist: #关键词对新闻标题逐个检索
                    if keyword in title[i]: #如果符合就加入待下载link列表
                        updatelist.append(link[i])
    
    driver.quit() #退出模拟浏览器
    all_symbols = pd.DataFrame()
    all_symbols['ticker'] = all_lists
    all_symbols.to_csv('all_symbols.csv')
    return updatelist #返回待下载link列表备用

#############获取最新代码列表及URL#####################
def get_symbols_and_URLs():  
        existing_file = pd.read_csv('symbols.csv') #原文件
        new_file = pd.DataFrame()
        old_lists = existing_file['symbols'] #原列表
        df = pdr.get_nasdaq_symbols() 
        symbols = df.index #获取新列表
        new_lists = []
        for i in symbols: #SPAC的symbol特点是5个字母，以U结尾，作为条件筛选
                if (i[-1] == 'R') and (len(i) == 5): 
                        new_lists.append(i)                
        
        extra = list(set(new_lists).difference(set(old_lists))) #对比新老列表，给出提示
        if extra == []:
            print('今天没有新增的SPAC')
        else:
            for i in extra:
                print(i)
            print('为今天新增SPAC!')

        new_file['symbols'] = new_lists
        new_urls = []
        for i in new_lists:
            url = 'http://data.eastmoney.com/notices/stock/{}.html'.format(i)
            new_urls.append(url)
        new_file['url'] = new_urls #存储新列表和url
        new_file.to_csv('symbols.csv')
        #新开文件代替原有
        return new_lists

#############获取最新代码列表及URL#####################
def get_update_pdfs(): #下载更新新闻的pdf
    updates = get_news() #用get_news函数返回的待下载列表

    if updates == []: #列表为空，没有要闻更新
        print('今日无重要新闻更新')
    else:
        driver = wd.Chrome() #模拟浏览器
        length = len(updates) #要下载的个数
        for lin in updates: #逐个下载
            driver.get(lin)
            WebDriverWait(driver,2) #下载一个等待2秒
        
        driver.quit() #关闭浏览器
        print('今日更新已完成，共下载新闻文件{}个'.format(length)) #结果提示

###############自动化运行################
def auto_do_job():
    get_symbols_and_URLs() #执行函数获取URL和网址列表
    get_news() #执行函数获取新闻csv
    get_update_pdfs() #执行函数下载要闻pdf

def exist_check(): #关键词检索股票是否有效
    listfile = pd.read_csv('all_symbols.csv') #由函数返回最新SPAC列表
    newlist = listfile['ticker']
    keyword_checklist2 = ['prospectus','Prospectus'] #关键词表
    exist_list = [] #准备存放有效股票
    for ticker in newlist:
        datafile = pd.read_csv('{}_news.csv'.format(ticker))
        titles = datafile['title']
        dts = datafile['dat']
        for tle in titles:
            for key in keyword_checklist2:
                if key in tle:
                    exist_list.append(ticker)
                    
    exist_list = list(set(exist_list))
    exist_list_file = pd.DataFrame()
    exist_list_file['symbols'] = exist_list
    exist_list_file.to_csv('exist_list_file.csv')
    print('使用关键词')
    print(keyword_checklist2)
    print('新闻中含有关键词的共{}家'.format(len(exist_list)))
    print(exist_list)           

'''
schedule.every().day.at('20:30').do(auto_do_job) #每天20:30顺次执行工作

while True: #循环监测，一到时间自动开始工作
    schedule.run_pending()
    time.sleep(1)
'''
get_symbols_and_URLs()
'''
get_news()
exist_check()
'''