# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 MXXIV.net
#
# This software is released under the MIT License.
# http://opensource.org/licenses/mit-license.php

'''
my TOKYO GASのスクレイピングモジュール
'''

import os
import re
import time
import enum

from selenium import webdriver
from bs4 import BeautifulSoup

_URL_LOGIN  = 'https://members.tokyo-gas.co.jp/kaiin/login.aspx'  # ログインページ
_URL_USAGE  = 'https://members.tokyo-gas.co.jp/mytokyogas/mtgmenu/mieru/total.aspx'  # 料金/使用量のページ

_WAIT_TIME = 3  # ページ遷移時に描画を待機する時間

Page = enum.Enum('Page', 'login top usage')


class MyTokyoGas:
    """ Scraper for My TokyoGas """

    def __init__(self, username, password):
        """ インスタンスの生成とログイン処理 """
        self._driver = webdriver.PhantomJS(service_log_path=os.path.devnull)
        self._driver.timeout = 10

        # ログインページに移動
        self._driver.get(_URL_LOGIN)
        self._driver.get(_URL_LOGIN)
        self._driver.find_element_by_id('main_2_txtLoginId').send_keys(username)
        self._driver.find_element_by_id('main_2_txtPassword').send_keys(password)
        self._driver.find_element_by_id('main_2_btnSubmit').click()

        # ログインできたことを確認
        soup = self._make_soup()
        if not soup.select('.user-status'):
            self._page = Page.login
            print('Login failed.')
        else:
            self._page = Page.top

    def __enter__(self):
        """ with句の戻り値 """
        return self

    def __exit__(self, type, value, traceback):
        """ with句の後処理 """
        self.quit()

    def quit(self):
        """ ログアウト処理 """
        self._driver.execute_script("__doPostBack('main_0$lbLogoutMobile','');")
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

        self._driver.get(_URL_USAGE)
        self._page = Page.usage

        # 月別グラフをパースしてJSON形式で出力
        soup = self._make_soup()
        json_dict = self._parse_usage_monthly(soup)

        return json_dict

    def _parse_usage_monthly(self, soup):
        """ 月別グラフのパース """

        this_year = int(soup.select('.box-date span')[0].text)
        # 月別データをパース
        month = [sp.text.replace(u'月', '') for sp in soup.select('.highcharts-xaxis-labels span')]
        value = [td.text.replace(  '-', '') for td in soup.select('.graph-list td')]

        # JSON形式で出力
        monthly = []

        def month_json(month, payment):
            return {'month':   month,
                    'payment': payment.replace(',', '')}

        # 
        if month[0] == u'1':
            year = this_year - 2
        else:
            year = this_year - 3

        # 前年
        for i in range(12):
            monthly.append(month_json(str(year)+'/'+month[i], value[i+12]))
            # 年の繰り上げ
            if month[i] == u'12':
                year = year + 1

        # 当年
        for i in range(12):
            monthly.append(month_json(str(year)+'/'+month[i], value[i]))
            # 年の繰り上げ
            if month[i] == u'12':
                year = year + 1

        json_dict = {'monthly': monthly}

        return json_dict

    def screenshot(self, filename):
        """ スクリーンショット(デバッグ用) """
        self._driver.save_screenshot(filename)

if __name__ == '__main__':

    with MyTokyoGas('username', 'password') as tg:
        # 月別データを取得
        json_dict = tg.fetch_usage_monthly()
        print(json_dict)
