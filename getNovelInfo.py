# -*- coding:utf-8 -*-
import requests
import re
from bs4 import BeautifulSoup
import dbm
import sender
import importlib, sys, os
import logging
from logging.handlers import TimedRotatingFileHandler

# 命令行运行时添加sys.path保证能导入webdriver
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), ".\\lib\\site-packages")))
from selenium import webdriver
import time

# 添加日志
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = TimedRotatingFileHandler("log/log.txt", when='D', encoding="utf-8")
handler.setLevel(logging.DEBUG)
handler.setFormatter(formatter)
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
console.setFormatter(formatter)
logger.addHandler(handler)
logger.addHandler(console)


# 创建了一个类
class getNovelInfo():
    """
    @desc 小说更新监听程序
    @date 2020/7/17
    @author qiulm
    @:param toMail 发送邮箱(必选)
    @:param url url(必选)
    @:param record 阅读记录
    @:param timeout 超时时间
    @:param file_path 文件路径
    @:param mode 打开文件类型
    @:param file_encode 文件字符集
    空列表
    """

    def __init__(self,
                 toMail,
                 url,
                 getUrl,
                 record=0,
                 timeout=10,
                 file_path='./count.pag',
                 file_encode='utf-8'):
        self.toMail = toMail
        self.url = url
        self.record = record
        self.timeout = timeout
        self.filePath = file_path
        self.getUrl = getUrl
        self.fileEncode = file_encode
        self.li_dataInfo = []
        self.db = dbm.open(file_path, 'c')

    def getHTMLText(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument(' --disable-gpu')
        driver = webdriver.Chrome(chrome_options=chrome_options)
        # time.sleep(1)
        driver.get(self.url)  # 获取网页
        time.sleep(1)
        return driver.page_source

    # 解析html，需要解析小说名称，并保存
    def parseYuanZun(self):
        html = self.getHTMLText()
        try:
            # 解析html
            soup = BeautifulSoup(html, "html.parser")

            # 小说名称
            novelName = soup.find('div', attrs={"class": "book-info"}).find('em').text

            # 章节ID
            chapterID = re.findall(r'(\w*[0-9]+)\w*', soup.find('span', attrs={"id": "J-catalogCount"}).text)

            # 小说注册,db中键值都必须是字符串
            if self.db.get(novelName) is None:
                self.db[novelName] = str(self.record)

            # 章节详细信息
            chapterUpdate = soup.find('li', attrs={"class": "update"})

            # 更新信息
            chapterTitle = chapterUpdate.find(
                'a', attrs={
                    "class": "blue"
                }).get("title")

            # 更新时间
            lastUpdateTime = chapterUpdate.find(
                'em', attrs={
                    "class": "time"
                }).text

            # 更新到全局变量
            self.li_dataInfo.append(chapterID)
            self.li_dataInfo.append(chapterTitle)
            self.li_dataInfo.append(lastUpdateTime)
            self.li_dataInfo.append(novelName)

            # 保存+发送邮件
            self.send_mail()

        except:
            print('解析html失败!')

    def send_mail(self):

        # 获取章节数
        paper_num = int(self.li_dataInfo[0][0])

        # 读取记录章节数
        old_num = int(self.db[self.li_dataInfo[3]])

        # old_num = 0
        # 未更新
        if paper_num == old_num:
            pass
            logger.debug("Not updated")

        # 记录过大
        elif paper_num < old_num:

            # 拼接上小说
            s = "您的记录章节数：%s 大于最新章节数： %s! 特此通知！\n\n系统自动从最新章节：%s开始为您推送。\n" % (
                old_num, paper_num, paper_num) + self.getNovel()

            # 发送邮件
            sender.send_mail(self.toMail, self.li_dataInfo[3], s)

            # 章节异常这则重置阅读章节
            self.db[self.li_dataInfo[3]] = str(paper_num)


        # 小说更新
        elif paper_num > old_num:
            total = paper_num - old_num

            # 拼接上小说
            s = "更新到: %s 章\n%s\n\n最新更新时间: %s\n\n您共有%s章未读\n" % (
                self.li_dataInfo[0], self.li_dataInfo[1], self.li_dataInfo[2], total) + self.getNovel()

            # 发送邮件
            sender.send_mail(self.toMail, self.li_dataInfo[3], s)

            # 刷新库
            self.db[self.li_dataInfo[3]] = str(paper_num)

    # 获取笔趣阁的小说
    def getNovel(self):
        timeout = 10
        kv = {'user-agent': 'Mozilla/5.0'}
        # 创建请求
        r = requests.get(self.getUrl, headers=kv, timeout=timeout)
        r.encoding = r.apparent_encoding
        t = requests.get(self.getUrl + BeautifulSoup(r.text, "html.parser")
                         .find('div', attrs={'id': 'info'})
                         .find_all('a').pop(0).get('href'),
                         headers=kv,
                         timeout=timeout)
        t.encoding = r.apparent_encoding
        return BeautifulSoup(t.text, 'html.parser') \
            .find(id='content').text.replace('\xa0' * 8, '\n')


if __name__ == "__main__":

    # 设置为utf8的编码格式。
    importlib.reload(sys)

    # sys.argv[0]是脚本名称
    if len(sys.argv) - 1 != 3:
        logger.error(
            'Three parameters are required: toMail URL, but ' + str(len(sys.argv) - 1) + ' parameters are detected')
        sys.exit(1)

    """
    编码调整
    传入字符串位unicode编码，采用的是命令行的解码方式，得先使用命令行编码方式重新编码后再解码位utf-8得编码
    """
    toMail = sys.argv[1].encode(sys.getdefaultencoding()).decode('UTF-8', 'strict')
    url = sys.argv[2].encode(sys.getdefaultencoding()).decode('UTF-8', 'strict')
    getUrl = sys.argv[3].encode(sys.getdefaultencoding()).decode('UTF-8', 'strict')

    # 检查邮箱格式
    if not re.match(r'^[0-9a-zA-Z_]{0,19}@[0-9a-zA-Z]{1,13}\.[com,cn,net]{1,3}$', toMail):
        logger.error('Email: ' + toMail + ' is not right')
        sys.exit(1)

    # 检查url格式
    if not re.match(r'^https?:/{2}\w.+$', url):
        logger.error('Url: ' + url + ' is look valid')
        sys.exit(1)

    # 检查getUrl格式
    if not re.match(r'^https?:/{2}\w.+$', getUrl):
        logger.error('GetUrl: ' + getUrl + ' is look valid')
        sys.exit(1)

    # 实例初始化
    yuanZun = getNovelInfo(toMail, url, getUrl)

    # 业务流程
    yuanZun.parseYuanZun()

    # 关闭dbm资源
    yuanZun.db.close()
