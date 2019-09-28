# 변수 및 라이브러리 part================================================================================================================================
import urllib.request
import re
import pandas                       # 날짜 구조를 위한 라이브러리
import time                         # 크롤링 시간 표기용도 라이브러리
import csv                          # CSV파일을 위한 라이브러리
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pytagcloud                   # WordCloud 관련 라이브러리
import random; random.seed(0)       # WordCloud 단어 색깔 관련 라이브러리
from PyQt5.QtWidgets import *       # PYQT(폼) 라이브러리
from PyQt5 import uic, QtCore
from PyQt5.QtGui import QPixmap
from datetime import datetime       # 날짜 관련 라이브러리
from bs4 import BeautifulSoup       # 크롤링 관련 라이브러리
from matplotlib import font_manager # 폰트 관련 라이브러리
from konlpy.tag import Okt          # 오픈 소스 한국어 분석기
from collections import Counter
# UI 파일 로드
form_class = uic.loadUiType("news_crawling.ui")[0]
ss_dict = {'청와대':'sid1=100&sid2=264', '국회/정당':'sid1=100&sid2=265', '북한':'sid1=100&sid2=268', '행정':'sid1=100&sid2=266'
           , '국방/외교':'sid1=100&sid2=267', '정치 일반':'sid1=100&sid2=269', '금융':'sid1=101&sid2=259', '증권':'sid1=101&sid2=258'
           , '산업/재계':'sid1=101&sid2=261', '중기/벤처':'sid1=101&sid2=771', '부동산':'sid1=101&sid2=260', '글로벌 경제':'sid1=101&sid2=262'
           , '생활경제':'sid1=101&sid2=310', '경제 일반':'sid1=101&sid2=263', '사건사고':'sid1=102&sid2=249', '교육':'sid1=102&sid2=250'
           , '노동':'sid1=102&sid2=251', '언론':'sid1=102&sid2=254', '환경':'sid1=102&sid2=252', '인권/복지':'sid1=102&sid2=59b'
           , '식품/의료':'sid1=102&sid2=255', '지역':'sid1=102&sid2=256', '인물':'sid1=102&sid2=276', '사회 일반':'sid1=102&sid2=257'
           , '건강정보':'sid1=103&sid2=241', '자동차/시승기':'sid1=103&sid2=239', '도로/교통':'sid1=103&sid2=240', '여행/레저':'sid1=103&sid2=237'
           , '음식/맛집':'sid1=103&sid2=238', '패션/뷰티':'sid1=103&sid2=376', '공연/전시':'sid1=103&sid2=242', '책':'sid1=103&sid2=243'
           , '종교':'sid1=103&sid2=244', '날씨':'sid1=103&sid2=248', '생활문화 일반':'sid1=103&sid2=245', '아시아/호주':'sid1=104&sid2=231'
           , '미국/중남미':'sid1=104&sid2=232', '유럽':'sid1=104&sid2=233', '중동/아프리카':'sid1=104&sid2=234', '세계 일반':'sid1=104&sid2=322'
           , '모바일':'sid1=105&sid2=731', '인터넷/SNS':'sid1=105&sid2=226', '통신/뉴미디어':'sid1=105&sid2=227', 'IT 일반':'sid1=105&sid2=230'
           , '보안/해킹':'sid1=105&sid2=732', '컴퓨터':'sid1=105&sid2=283', '게임/리뷰':'sid1=105&sid2=229', '과학 일반':'sid1=105&sid2=228'}
url = ''
sub_url = ''
crawlsection = ''
crawlword = ''  # 크롤링을 할 단어를 저장하는 변수
s_date = []     # 시작하는 날짜
e_date = []     # 끝나는 날짜
fname = []
cloudImagePath = ''
# Thread part===========================================================================================================================================
class CrawlingThread(QtCore.QThread):   # 수집 기능 스레드화
    def __init__(self, parent=None):
        super(CrawlingThread, self).__init__(parent)
    def run(self):
        MyWindow.crawlcode(self)
        self.quit()
class ProcessingThread(QtCore.QThread): # 가공 기능 스레드화
    def __init__(self, parent=None):
        super(ProcessingThread, self).__init__(parent)
    def run(self):
        MyWindow.datacode(self)
        self.quit()
        pixmap = QPixmap('chart.png')
        myWindow.label_5.setPixmap(pixmap)
        pixmap2 = QPixmap(cloudImagePath)
        myWindow.label.setPixmap(pixmap2)
# UI part===============================================================================================================================================
class MyWindow(QMainWindow, form_class):
    # UI의 기능을 추가 및 연결하는 함수
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.crawlthread = CrawlingThread()                 # 수집 스레드를 QT 내에 추가
        self.processthread = ProcessingThread()             # 가공 스레드를 QT 내에 추가
        self.sDate.setMaximumDate(datetime.now())           # 시작 날짜 범위를 오늘 날짜까지로 설정
        self.eDate.setMaximumDate(datetime.now())           # 끝 날짜 범위를 오늘 날짜까지로 설정
        self.eDate.setDateTime(datetime.now())              # 처음 끝 날짜를 오늘 날짜로 표기
        self.cb_ctgr.activated[str].connect(self.ctgrEvent) # 카테고리 콤보박스 선택 시 함수 발생
        self.cb_ss.activated[str].connect(self.ssEvent)     # 섹션 콤보박스 선택 시 함수 발생
        self.Search.clicked.connect(self.Ser_clicked)       # 수집 버튼 클릭 시 함수 발생
        self.Process.clicked.connect(self.Prc_clicked)      # 가공 버튼 클릭 시 함수 발생
    # 카테고리 콤보박스 함수
    def ctgrEvent(self, text):
        global sub_url
        sub_url = ''
        self.cb_ss.clear()
        if text == '정치':
            self.cb_ss.addItems(['선택 안함', '청와대', '국회/정당', '북한', '행정', '국방/외교', '정치 일반'])
        elif text == '경제':
            self.cb_ss.addItems(['선택 안함', '금융', '증권', '산업/재계', '중기/벤처', '부동산', '글로벌 경제', '생활경제', '경제 일반'])
        elif text == '사회':
            self.cb_ss.addItems(['선택 안함', '사건사고', '교육', '노동', '언론', '환경', '인권/복지', '식품/의료', '지역', '인물', '사회 일반'])
        elif text == '생활/문화':
            self.cb_ss.addItems(['선택 안함', '건강정보', '자동차/시승기', '도로/교통', '여행/레저', '음식/맛집', '패션/뷰티', '공연/전시', '책', '종교', '날씨', '생활문화 일반'])
        elif text == '세계':
            self.cb_ss.addItems(['선택 안함', '아시아/호주', '미국/중남미', '유럽', '중동/아프리카', '세계 일반'])
        elif text == 'IT/과학':
            self.cb_ss.addItems(['선택 안함', '모바일', '인터넷/SNS', '통신/뉴미디어', 'IT 일반', '보안/해킹', '컴퓨터', '게임/리뷰', '과학 일반'])
        else:
            self.cb_ss.addItem('선택 안함')
    # 섹션 콤보박스 함수
    def ssEvent(self, text):
        global sub_url
        sub_url = ss_dict.get(text)
    # 수집버튼(크롤링 시작)
    def Ser_clicked(self):
        global crawlsection
        global crawlword
        global s_date, e_date
        global url
        url = 'https://news.naver.com/main/list.nhn?mode=LS2D&mid=shm&' + sub_url + '&listType=title' # 수집 대상의 url
        self.textEdit.clear()                       # 수집 시 입력 될 텍스트박스 내용 지우기
        CStext = self.cb_ss.currentText()
        if '/' in CStext:
            print(2)
            CSlist = CStext.split('/')
            CStext = CSlist[0] + CSlist[1]
        crawlsection = CStext                       # UI 속 선택 된 섹션 값 가져오기
        crawlword = self.lineEdit.text()            # UI 속 텍스트박스에 입력된 단어 가져오기
        Adate = self.sDate.date()                   # UI 속 시작 날짜 받아오기
        Bdate = self.eDate.date()                   # UI 속 끝 날짜 받아오기
        if crawlword == '':                         # 수집 전 필요한 자료의 유무 검사
            QMessageBox.about(self, "오류", "단어를 입력해주세요!")
        elif Adate > Bdate:
            QMessageBox.about(self, "오류", "시작 날짜와 끝 날짜를 확인해주세요!")
        elif sub_url == '' or sub_url == None:
            QMessageBox.about(self, "오류", "카테고리와 섹션을 선택해주세요!")
        else:
            s_date = [Adate.year(), Adate.month(), Adate.day()]
            e_date = [Bdate.year(), Bdate.month(), Bdate.day()]
            self.Search.setEnabled(False)
            self.Process.setEnabled(False)
            self.crawlthread.start()                # 수집 스레드 시작
    # 가공버튼
    def Prc_clicked(self):
        global fname
        fname = QFileDialog.getOpenFileName(self)
        if fname[0] != '':
            self.Search.setEnabled(False)
            self.Process.setEnabled(False)
            self.processthread.start()                  # 가공 스레드 시작
# Crawling Code part====================================================================================================================================
    # 날짜 관련 함수(url 형식에 맞춰야 함으로 한자리수로 구성된 달과 일을 두자리로 표기해준다.)
    def DateNum(year, month, day):
        if month < 10:
            month = '0' + str(month)
        if day < 10:
            day = '0' + str(day)
        return str(year) + str(month) + str(day)
    # URL > BS4 형식으로 변환
    def URL2BS4(url):
        request = urllib.request.Request(url)
        response = urllib.request.urlopen(request)
        rescode = response.getcode()
        if rescode == 200:
            response_body = response.read()
            xmlsoup = BeautifulSoup(response_body, 'html.parser')
            return xmlsoup
        else:
            return None
    # 추출한 내용에서 필요없는 내용제거 함수(내용을 읽는데 불필요한 요소를 미리 제거한다.)
    def Remove_Character(wordlist):
        wordlist = re.sub('<b>','',wordlist,0)
        wordlist = re.sub('\n','',wordlist,0)
        wordlist = re.sub("</b>",'',wordlist,0)
        wordlist = re.sub('&quot;','',wordlist,0)
        wordlist = re.sub('&apos;','',wordlist,0)
        wordlist = re.sub('&lt;','',wordlist,0)
        wordlist = re.sub('&gt;','',wordlist,0)
        wordlist = re.sub("// flash 오류를 우회하기 위한 함수 추가",'',wordlist,0)
        wordlist = re.sub("function _flash_removeCallback",'',wordlist,0)
        wordlist = re.sub("\(\)",'',wordlist,0)
        wordlist = re.sub("\{\}",'',wordlist,0)
        wordlist = re.sub('\\xa0','',wordlist,0)
        wordlist = re.sub('\\u2024','',wordlist,0)
        wordlist = re.sub('\\xa9','',wordlist,0)
        wordlist = re.sub('\\u30fb','',wordlist,0)
        return wordlist
    # 기사의 내용을 추출하는 함수
    def Article_Post(link):
        request = urllib.request.Request(link)
        response = urllib.request.urlopen(request)
        response_body = response.read()
        a_html = BeautifulSoup(response_body, 'html.parser')
        try:
            article_org = a_html.find('div', {'id': 'articleBodyContents'}).get_text(strip=True)
            article = MyWindow.Remove_Character(article_org)
        except:
            print("기사 없음")
            return 0
        return article
    # 수집
    def crawlcode(self):
        s_t = time.time()
        s_d = MyWindow.DateNum(s_date[0], s_date[1], s_date[2])
        e_d = MyWindow.DateNum(e_date[0], e_date[1], e_date[2])
        dt_index = pandas.date_range(start=s_d, end=e_d)
        dt_list = dt_index.strftime("%Y%m%d").tolist()
        barValue = 0
        myWindow.pBar.setValue(barValue)
        myWindow.pBar.setMaximum(len(dt_list))
        filename = crawlsection + '_' + crawlword + '_' + dt_list[0] + '~' + dt_list[-1] + '.csv'
        with open(filename, 'w', encoding='utf-8', newline='') as f:
            wr = csv.writer(f)
            print(filename)
            for dt in dt_list:
                url_date = url + '&date=' + dt
                print(url_date)
                xmlsoup = MyWindow.URL2BS4(url_date)
                pagePart = xmlsoup.find('div', {'class': 'paging'})
                anchorNumber = pagePart.find_all({'a': 'href'})
                pageNumber = len(anchorNumber) + 1
                try:
                    while (True):  # 10페이지가 넘었을 때 페이지 수 구하기
                        if int(pageNumber / 10) != 0 and (pageNumber - 1) % 10 == 0 and len(anchorNumber) != 1:
                            imsiUrl = url_date + '&page=' + str(int(pageNumber / 10)) + '1'
                            xmlsoup = MyWindow.URL2BS4(imsiUrl)
                            pagePart = xmlsoup.find('div', {'class': 'paging'})
                            anchorNumber = pagePart.find_all({'a': 'href'})
                            pageNumber = len(anchorNumber) + (pageNumber - 1)
                        elif int(pageNumber / 10) != 0:
                            pageNumber = len(anchorNumber) + (int(pageNumber / 10) * 10)
                            break
                        else:
                            break
                    #print(pageNumber)
                    try:
                        for page in range(1, pageNumber + 1, 1):
                            newDayUrl = url_date + '&page=' + str(page)
                            xmlsoup = MyWindow.URL2BS4(newDayUrl)
                            listBody = xmlsoup.find('div', {'class': 'list_body'})
                            allList = listBody.findAll('li')
                            for alist in allList:
                                Title = alist.find('a').text
                                result = re.search(crawlword, Title)
                                if result != None:
                                    #print(Title)
                                    myWindow.textEdit.append(dt + ' - ' + str(Title))
                                    Link = alist.find('a')['href']
                                    Article = MyWindow.Article_Post(Link)
                                    if Article == 0:
                                        continue
                                    Author = alist.find('span', {'class': 'writing'}).text
                                    Date = alist.find('span', {'class': 'date'}).text
                                    wr.writerow([Author, Date, Title, Article])
                                else:
                                    continue
                    except:
                        print('기사 찾기 실패')
                except:
                    print('페이지 찾기 실패')
                barValue += 1
                myWindow.pBar.setValue(barValue)
        timecheck = time.time() - s_t
        timecheck = str((int(timecheck*100))/100)
        print('END ' + timecheck + 'second')
        myWindow.textEdit.append('자료 수집이 완료되었습니다.(수집시간 ' + timecheck + ' 초)')
        myWindow.Search.setEnabled(True)
        myWindow.Process.setEnabled(True)
    # 수집한 자료를 그래프로 표기하는 함수
    def showChart(wordInfo):
        font_location = "C:\Windows\Fonts\malgun.ttf"
        font_name = font_manager.FontProperties(fname=font_location).get_name()
        matplotlib.rc('font', family=font_name)
        plt.rcParams["figure.figsize"] = (14, 4)
        plt.xlabel('주요 단어')
        plt.ylabel('빈도수')
        plt.grid(True)
        Sorted_Dict_Values = sorted(wordInfo.values(), reverse=True)
        Sorted_Dict_Keys = sorted(wordInfo, key=wordInfo.get, reverse=True)
        plt.bar(range(len(wordInfo)), Sorted_Dict_Values, align='center')
        plt.xticks(range(len(wordInfo)), list(Sorted_Dict_Keys), rotation='70')
        fig = plt.gcf()
        plt.close()
        fig.savefig('chart.png')
    # WordCloud 그리기 함수
    def saveWordCloud(wordInfo, filename):
        taglist = pytagcloud.make_tags(dict(wordInfo).items(), maxsize=72)
        pytagcloud.create_tag_image(taglist, filename, size=(600, 400), fontname='OldBath-Bold', rectangular=False, layout=4)
    # 가공
    def datacode(self):
        global cloudImagePath
        filename = fname[0].split('/')
        f_stack = len(filename)
        taglist = filename[-1].split('_')
        searchtext = taglist[1]
        barValue = 0
        myWindow.pBar.setValue(barValue)
        myWindow.pBar.setMaximum(100)
        with open(filename[f_stack-1], 'rt', encoding='utf-8') as rfile:
            with open('Processing_' + filename[f_stack-1], 'w', newline='') as wfile:
                cw = csv.writer(wfile)
                r = csv.reader(rfile)
                for row in r:
                    result_News = ''
                    for c in row[3]:
                        if ord('가') <= ord(c) <= ord('힣') or c.isdigit() or ord('A') <= ord(c) <= ord('z') or ord(c) == ord(' '):
                            result_News += c
                        else:
                            result_News += ' '
                    print(result_News)
                    cw.writerow([result_News])
        barValue = 10
        myWindow.pBar.setValue(barValue)
        cloudImagePath = 'Processing_' + filename[f_stack-1] + '.png'
        with open('Processing_' + filename[f_stack-1], 'r') as f:
            text = f.read()
        okt = Okt()
        barValue = 30
        myWindow.pBar.setValue(barValue)
        nouns = okt.nouns(text)
        barValue = 60
        myWindow.pBar.setValue(barValue)
        count = Counter(nouns)
        wordInfo = dict()
        for tags, counts in count.most_common(75):
            if len(str(tags)) > 1:
                if tags == "뉴스" or tags == "금지" or tags == "제공" or tags == "무단" or tags == "전재"\
                    or tags == "배포" or tags == "기자" or tags == "구독" or tags == "뉴시스" or tags == "연합뉴스"\
                    or tags == "사진" or tags == "저작권" or tags == "라며" or tags == "디스패치" or tags == "노컷뉴스"\
                    or tags == "한국영" or tags == "네이버" or tags == searchtext: # 검색할 필요가 없는 단어
                    continue
                wordInfo[tags] = counts
                print("%s : %d" % (tags, counts))
        barValue = 100
        myWindow.pBar.setValue(barValue)
        MyWindow.showChart(wordInfo)
        MyWindow.saveWordCloud(wordInfo, cloudImagePath)
        myWindow.Search.setEnabled(True)
        myWindow.Process.setEnabled(True)
# Form Part=============================================================================================================================================
if __name__ == '__main__':
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    app.exec_()