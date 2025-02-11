# selenium 임포트
from selenium import webdriver
import schedule
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
# summary 불러오기
from summary import make_tag
# 이미지 바이트 처리
from io import BytesIO
import urllib.request as req
import datetime
# 장고 연결
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server_dy.settings')
import django
django.setup()
# django.setup() 이후 import해 주어야 한다.
from article.models import Article

# DB에 있는 모든 내용 삭제
def delete_all():
    queryset = Article.objects.all()
    queryset.delete()


def crawl_data():
    
    result = []

    now = datetime.datetime.now()
    crawl_time = now.strftime('%Y. %m. %d. %H:%M')

    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 실행 했을 때 브라우저가 실행되지 않는다.

    # webdriver 설정(Chrome, Firefox 등) - Headless 모드
    browser = webdriver.Chrome('D:\chromedriver.exe', options=chrome_options)

    # webdriver 설정(Chrome, Firefox 등) - 일반 모드
    # browser = webdriver.Chrome('D:/webdriver/chrome/chromedriver.exe')

    # 크롬 브라우저 내부 대기
    browser.implicitly_wait(5)

    # 브라우저 사이즈
    browser.set_window_size(1920, 1280)  # maximize_window(), minimize_window()

    # 페이지 이동
    browser.get('https://news.daum.net/ranking/popular')

    # 1차 페이지 내용
    # print('Before Page Contents : {}'.format(browser.page_source))

    # 현재 페이지의 기사 순서
    nth_news = 1

    # 한 페이지에서 크롤링할 기사 수
    target_crawl_news_num = 50

    while nth_news <= target_crawl_news_num:
        # 초기화
        link = None,
        category = None,
        title = None,
        article_date = None,
        img = None,
        contents = None,
        crawl_time = None,
        newspaper = None,
        headline = None

        browser.implicitly_wait(10)

        # headline 저장
        soup = BeautifulSoup(browser.page_source, 'html.parser')
        headline = soup.select('#mArticle > div.rank_news > ul.list_news2 > li:nth-of-type({}) > div.cont_thumb > div > span'.format(nth_news))[0].text.strip()
        del soup

        # 페이지 이동 클릭
        try:
            btn = browser.find_element_by_css_selector('#mArticle > div.rank_news > ul.list_news2 > li:nth-of-type({}) > div.cont_thumb > strong > a'.format(nth_news))
            browser.execute_script('arguments[0].click();', btn)
        except TimeoutException:
            nth_news += 1
            continue

        # bs4 초기화
        soup = BeautifulSoup(browser.page_source, 'html.parser')

        # 소스코드 정리
        # print(soup.prettify)

        # 필요 정보 추출(news_comp, title, date, img, contents, link)
        # 도중에 문제가 있다면 크롤링 하지 않고 넘어감.
        try:
            # 페이지 번호 출력
            print('****** {}th New ******'.format(nth_news))
            browser.implicitly_wait(10)
            # category
            category = soup.select('div#kakaoContent > h2')[0].text.strip()
            print(category)
            # newspaper
            newspaper = soup.select('div.head_view > em > a > img')[0]['alt']
            print(newspaper)
            # title
            title = soup.select('div.head_view > h3')[0].text.strip()
            print(title)
            # article_date
            article_date = soup.select(
                'div.head_view > span.info_view > span.txt_info > span.num_date')[0].text.strip()
            print(article_date)
            # contents
            contents_lists = soup.select(
                'div#harmonyContainer > section > [dmcf-ptype="general"]')
            # 여러 문장으로 나눠서 온 content들을 하나의 문장으로 합친다.
            contents = ''
            for content in contents_lists:
                contents += content.text.strip() + '\n'
            print(contents)
            # link
            link = soup.select(
                'div.copyUrl > div.sns_copyurl > a.link_copyurl > span:nth-of-type(2)')[0].text.strip()
            print(link)
            # 이미지가 없는 기사일 경우 오류처리
            try:
                img = soup.select('figure.figure_frm.origin_fig > p.link_figure > img')[
                    0]['data-org-src']
            except IndexError as e:
                img = 0
            if img:
                print(soup.select('figure.figure_frm.origin_fig > p.link_figure > img')[
                      0]['data-org-src'])
        except IndexError as e:
            nth_news += 1
            del soup
            continue

        tag = make_tag(contents)
        print(tag)
        
        item_obj = {
            'link': link,
            'category': category,
            'title': title,
            'article_date': article_date,
            'img': img,
            'contents': contents,
            'crawl_time': crawl_time,
            'newspaper': newspaper,
            'headline': headline,
            'tag' : tag
        }

        result.append(item_obj)

        # 페이지 뒤로 가기
        time.sleep(5)
        browser.back()

        nth_news += 1

        print()
        print()

        # 페이지 별 스크린 샷 저장
        # browser.save_screenshot('./target_page{}.png'.format(cur_page))

        # BeautifulSoup 인스턴스 삭제
        del soup

    # 브라우저 종료
    browser.close()

    return result

# db에 저장


def add_new_itmes(crawled_items):
    # 새로운 기사를 저장하기 전에 기존의 데이터를 모두 삭제
    delete_all()

    last_inserted_items = Article.objects.last()
    if last_inserted_items is None:
        last_inserted_link = ""
    else:
        last_inserted_link = getattr(last_inserted_items, 'link')
    items_to_insert_into_db = []
    for item in crawled_items:
        if item['link'] == last_inserted_link:
            break
        items_to_insert_into_db.append(item)
    items_to_insert_into_db.reverse()
    for item in items_to_insert_into_db:
        Article(
            link=item['link'],
            category=item['category'],
            title=item['title'],
            article_date=item['article_date'],
            img=item['img'],
            contents=item['contents'],
            crawl_time=item['crawl_time'],
            newspaper=item['newspaper'],
            headline=item['headline'],
            tag = item['tag']
        ).save()

    print("new item added!")

    return items_to_insert_into_db

schedule.every(6).hours.do(add_new_itmes, crawl_data())

while True:
    schedule.run_pending()
    time.sleep(300)