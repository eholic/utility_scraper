# -*- coding: utf-8 -*-
# 
# Copyright (c) 2017 MXXIV.net
#
# This software is released under the MIT License.
# http://opensource.org/licenses/mit-license.php

'''
でんき家計簿のスクレイピングモジュール
'''

import os
import re
import time
import enum

from selenium import webdriver
from bs4 import BeautifulSoup

_URL_LOGIN  = 'https://www.kakeibo.tepco.co.jp/dk/aut/login/'  # ログインページ
_URL_LOGOUT = 'https://www.kakeibo.tepco.co.jp/dk/doLogout'    # ログアウトアドレス
_URL_TOP    = 'https://www.kakeibo.tepco.co.jp/dk/com/menu/'   # ログイン後のトップページ
_WAIT_TIME = 3  # ページ遷移時に描画を待機する時間

Page = enum.Enum('Page', 'login top monthly halfhour')


class DenkiKakeibo:
    """ Scraper for DenkiKakeibo """

    def __init__(self, username, password):
        """ インスタンスの生成とログイン処理 """
        self._driver = webdriver.PhantomJS(service_log_path=os.path.devnull)
        self._driver.timeout = 10

        # ログインページに移動
        self._driver.get(_URL_LOGIN)
        self._driver.find_element_by_id('idId').send_keys(username)
        self._driver.find_element_by_id('idPassword').send_keys(password)
        self._driver.find_element_by_id('idLogin').click()

        # ログインできたことを確認
        soup = self._make_soup()
        if soup.title.string == 'でんき家計簿　会員ホーム':
            self._page = Page.top
        else:
            self._page = Page.login

    def __enter__(self):
        """ with句の戻り値 """
        return self

    def __exit__(self, type, value, traceback):
        """ with句の後処理 """
        self.quit()

    def quit(self):
        """ ログアウト処理 """
        self._driver.get(_URL_LOGOUT)
        self._page = Page.login

        self._driver.quit()

    def _make_soup(self):
        """ htmlのパース """
        markup = self._driver.page_source.encode('utf-8')
        soup = BeautifulSoup(markup, 'lxml')

        return soup

    def fetch_usage_monthly(self):
        """ 月別使用量のスクレイピング """

        if self._page == Page.login:
            return False

        self._driver.get(_URL_TOP)
        self._driver.execute_script("submitForm(fnjdoc.forms['com_menuActionForm'], '/dk/com/menu/goElectricUsageAmount', null);")
        time.sleep(_WAIT_TIME)
        self._page = Page.monthly

        # 月別グラフをパースしてJSON形式で出力
        soup = self._make_soup()
        json_dict = self._parse_usage_monthly(soup)

        return json_dict

    def _parse_usage_monthly(self, soup):
        """ 月別グラフのパース """

        # 月別データをパース
        month = [th.text for th in soup.select('.view_table th')]
        value = [td.text for td in soup.select('.view_table td')]
        # 空の値を削除
        value = [v.replace('---', '') for v in value]
      
        # ヘッダを削除
        dellist = lambda items, indexes: [item for index, item in enumerate(items) if index not in indexes]
        month = dellist(month, [i*13 for i in range(2)])
        value = dellist(value, [i*13 for i in range(6)])

        # JSON形式で出力
        def month_json(month, day, kWh, payment):
            return {'month':  month,
                    'value': {'day': day,
                              'kWh': kWh.replace(',', ''),
                              'payment': payment.replace(',', '')
                              }}
        monthly = []
        for i in range(12):
            monthly.append(month_json(month[i], value[i], value[i+12], value[i+24]))
        for i in range(12):
            monthly.append(month_json(month[i+12], value[i+36], value[i+12+36], value[i+24+36]))

        json_dict = {'monthly': monthly}

        return json_dict



    def fetch_usage_30Min(self, previous=0):
        """ 時間別グラフのスクレイピング """

        if self._page == Page.login:
            return False

        if self._page != Page.halfhour or previous == 0:
            # 時間別グラフに移動
            self._driver.get(_URL_TOP) # 念のためトップページに移動
            self._driver.execute_script("submitForm(fnjdoc.forms['com_menuActionForm'], '/dk/com/menu/goElectricUsageAmount', null);")
            time.sleep(_WAIT_TIME)
            self._driver.execute_script("submitForm(fnjdoc.forms['syo_electricUsageAmountActionForm'], '/dk/syo/electricUsageAmount/goElectricUsage30minGraph', null);")
            time.sleep(_WAIT_TIME)
            self._page = Page.halfhour

        # 前日に移動
        for i in range(previous):
            self._driver.find_element_by_id('doPrevious').click()
            time.sleep(_WAIT_TIME)

        # 時間別グラフをパースしてJSON形式で出力
        soup = self._make_soup()
        json_dict = self._parse_usage_30Min(soup)

        return json_dict

    def _parse_usage_30Min(self, soup):
        """ 時間別グラフのパース """
        json_dict = {}

        # 日付をパース
        date_text = soup.select('.graph_head_table td')[1].text
        m = re.search(r"[\d/]{8,10}", date_text)

        if m:
            json_dict['day'] = m.group()
        else:
            return False

        # 電気使用量データをパース
        # <script> ...  vbar_usage_grp() { var items = [["日次", 0.10, 0.10, 0.00, 0.10, 0.10, 0.10, 0.00, 0.10, 0.10, 0.00, 0.10, 0.10, 0.10, 0.60, 0.30, 0.50, 0.20, 0.00, 0.10, 0.10, 0.00, 0.10, 0.00, 0.10, 0.10, 0.00, 0.10, 0.10, 0.00, 0.10, 0.10, 0.00, 0.10, 0.00, 0.10, 0.10, 0.00, 0.10, 0.10, 0.00, 0.10, 0.10, 0.30, 0.10, 0.00, 0.10, 0.10, 0.00, 0]];
        s = soup.find("script", text=lambda t: t and "vbar_usage_grp" in t)
        m = re.search(r'\[\["日次", (.+?)\]\];', s.text)
        if m:
            json_dict['value'] = m.group(1)
        else:
            return False
        return json_dict

    def screenshot(self, filename):
        """ スクリーンショット(デバッグ用) """
        self._driver.save_screenshot(filename)

if __name__ == '__main__':

    with DenkiKakeibo('username', 'password') as dk:
        # 最新の時間データを取得
        json_dict = dk.fetch_usage_30Min()
        print(json_dict)

        # 前日の時間データを取得
        json_dict = dk.fetch_usage_30Min(previous=1)
        print(json_dict)

        # 月別データを取得
        json_dict = dk.fetch_usage_monthly()
        print(json_dict)
