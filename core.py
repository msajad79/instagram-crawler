"""
The core of crawler
"""

from datetime import datetime
import re
import json
import csv
import time
from os import mkdir

from bs4 import BeautifulSoup
import requests

class Account():
    """Base class for manage account"""
    def __init__(self, username:str, password:str) -> str:
        self.session = requests.session()
        self.userId = None
        self.is_logged_in = False
        self.name_file = datetime.now().strftime("%Y_%M_%d_%H_%S")

        self.username = username
        self.password = password

        self.time_request = list()

    def request_safe(self, url_request_safe, method='GET', headers_request_safe=None, data_request_safe=None, params_request_safe=None, mood_looptry=False, stream_request_safe=False):
        """
        Safe request check status code and exception this is demo
        status ,data
        """
        while True:
            if method == 'GET':
                tic = time.time()
                try:
                    res_request_safe = self.session.get(
                        url_request_safe,
                        headers=headers_request_safe,
                        stream=stream_request_safe,
                        params=params_request_safe,
                        timeout=4
                    )
                except requests.exceptions.Timeout:
                    self.time_request.append(time.time()-tic)
                    print('time out request')
                    continue
                self.time_request.append(time.time()-tic)
                # status code filter
                if res_request_safe.status_code in [500,560]:
                    print(f'{res_request_safe.status_code} status code')
                    time.sleep(2)
                    continue
                return True, res_request_safe
            elif method == 'POST':
                tic = time.time()
                try:
                    res_request_safe = self.session.post(
                        url_request_safe,
                        headers=headers_request_safe,
                        data=data_request_safe,
                        stream=stream_request_safe,
                        params=params_request_safe
                    )
                except requests.exceptions.Timeout:
                    self.time_request.append(time.time()-tic)
                    print('time out request')
                    continue
                self.time_request.append(time.time()-tic)
                # status code filter
                if res_request_safe.status_code in [500]:
                    print(f'{res_request_safe.status_code} status code')
                    time.sleep(2)
                    continue
                return True, res_request_safe
    
    def get_csrf_token(self) -> str:
        """Get csrf token from login page"""
        url_csrf = 'https://www.instagram.com/accounts/login/'

        res = self.session.get(url_csrf, headers={
            'user-agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:55.0) Gecko/20100101 Firefox/55.0"#'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36'
        })
        csrf = re.findall(r"csrf_token\":\"(.*?)\"", res.text)[0]
        return csrf

    def post_login(self, csrf) -> dict:
        """Post login form"""
        url_login = 'https://www.instagram.com/accounts/login/ajax/'
        time_ = int(datetime.now().timestamp())
        data = {
            'username': self.username,
            'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:{time_}:{self.password}',
            'queryParams': {},
            'optIntoOneTap': False,
            'stopDeletionNonce': '',
            'trustedDeviceRecords': {},
        }
        header = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest',
            'x-csrftoken': csrf
        }
        res = self.session.post(url_login, data=data, headers=header)
        if res.json().get('authenticated'):
            self.is_logged_in = True
        self.userId = res.json().get('userId')
        return res.json()

    def login(self) -> dict:
        """Manage login"""
        csrf_token = self.get_csrf_token()
        ans_login = self.post_login(csrf=csrf_token)
        return ans_login

    def logout(self) -> None:
        """logout account"""
        if not self.is_logged_in:
            return
        self.session = requests.session()
        self.is_logged_in = False

    def load_target_page(self, username) -> tuple[dict, dict, dict, bool]:
        """
        Load target page and get initial scrap
        and end cursor
        """
        url_page = f'https://www.instagram.com/{username}/'


        _,res_page = self.request_safe(url_page)
        
        page_info = dict()
        posts_info = dict()

        try:
            base_data = re.findall(r'window._sharedData = ({.*});', res_page.text)[0]
        except IndexError:
            soup = BeautifulSoup(res_page.text, 'html.parser')
            elm = soup.find('div', attrs={'class':'error-container'})
            if not elm is None and "Sorry, this page isn't available." in elm.text:
                page_info['username'] = username
                page_info['status'] = "error --> Sorry, this page isn't available."
                return (dict(), page_info, posts_info, False)
            if not elm is None and "Error" in elm.text:
                raise Exception(elm.text)
            

        scrap_data = json.loads(base_data)
        if res_page.status_code != 200:
            page_info['username'] = username
            page_info['status'] = f'status code is {res_page.status_code}'
            return (scrap_data, page_info, posts_info, False)

        user = scrap_data['entry_data']['ProfilePage'][0]['graphql']['user']
        media = user['edge_owner_to_timeline_media']

        page_info['user_id']         = user['id']
        page_info['username']        = user['username']
        page_info['bio']             = user['biography']
        page_info['follower_count']  = user['edge_followed_by']['count']
        page_info['following_count'] = user['edge_follow']['count']
        page_info['is_private']      = user['is_private']
        page_info['count_posts']     = media['count']

        posts_info['edges']          = media['edges']
        posts_info['end_cursor']     = media['page_info']['end_cursor']
        posts_info['has_next_page']  = media['page_info']['has_next_page']
        page_info['status']          = 'OK'
        
        return (scrap_data, page_info, posts_info, True)

    def graphql_query(self, end_cursor, user_id) -> tuple[dict, list, tuple[str, bool]]:
        """Get data instagram post"""
        query_params = {
            'query_hash': '8c2a529969ee035a5063f2fc8602a0fd',
            'variables': json.dumps({"id":user_id,"first":8,"after":end_cursor})
        }

        url_post = 'https://www.instagram.com/graphql/query/'

        _, res_post = self.request_safe(url_post, params_request_safe=query_params)
        
        try:
            res_json = res_post.json()
        except json.JSONDecodeError:
            soup = BeautifulSoup(res_post.text, 'html.parser')
            elm = soup.find('div', attrs={'class':'error-container'})
            if not elm is None and "Error" in elm.text:
                raise Exception(elm.text)
        if res_post.json().get('message') == 'rate limited':
            raise Exception(res_post.json().get('message'))
        
        has_next_page = res_post.json()['data']['user']['edge_owner_to_timeline_media']['page_info']['has_next_page']
        end_cursor  = res_post.json()['data']['user']['edge_owner_to_timeline_media']['page_info']['end_cursor']
        edges = res_post.json()['data']['user']['edge_owner_to_timeline_media']['edges']
        return (res_post.json(), edges, (end_cursor, has_next_page))

    def init_csv(self) -> None:
        mkdir(f'database/{self.username}_{self.name_file}')
        with open(f'database/{self.username}_{self.name_file}/posts.csv', 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['user_id','username','type','timestamp','comment_count','like_count','caption'])
        with open(f'database/{self.username}_{self.name_file}/pages.csv', 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['user_id','username','follower_count','following_count','post_count','is_private','bio','status'])

    def save_time(self) -> None:
        with open(f'database/{self.username}_{self.name_file}/times.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['time'])
            for row in self.time_request:
                writer.writerow([row])

    def save_posts_data(self, edges, username, user_id) -> None:
        """save posts data in csv file"""
        with open(f'database/{self.username}_{self.name_file}/posts.csv', 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            for edge in edges:
                row = list()
                row.append(user_id)
                row.append(username)
                row.append(edge['node']['__typename'])
                row.append(edge['node']['taken_at_timestamp'])
                row.append(edge['node']['edge_media_to_comment']['count'])
                row.append(edge['node']['edge_media_preview_like']['count'])
                edges_caption = edge['node']['edge_media_to_caption']['edges']
                caption = str()
                for edge_caption in edges_caption:
                    caption += edge_caption['node']['text']
                row.append(caption)
                writer.writerow(row)

    def save_pages_data(self, page_info):
        """save pages data in csv file"""
        with open(f'database/{self.username}_{self.name_file}/pages.csv', 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            row = list()
            row.append(page_info.get('user_id'))
            row.append(page_info.get('username'))
            row.append(page_info.get('follower_count'))
            row.append(page_info.get('following_count'))
            row.append(page_info.get('count_posts'))
            row.append(page_info.get('is_private'))
            row.append(page_info.get('bio'))
            row.append(page_info.get('status'))
            writer.writerow(row)

    def get_posts(self, username) -> None:
        """Manage scrape data"""
        print('='*10)
        print(f'load page {username}...')
        _, page_info, posts_info, status = self.load_target_page(username=username)
        self.save_pages_data(page_info=page_info)
        print('Data was crawl and saved.')
        if not status:
            return
        user_id = page_info['user_id']
        end_cursor = posts_info['end_cursor']
        self.save_posts_data(edges=posts_info['edges'], username=username, user_id=user_id)
        has_next_page = posts_info['has_next_page']
        while has_next_page:
            print('get and save posts...')
            _, edges_scrap, (end_cursor, has_next_page) = self.graphql_query(end_cursor=end_cursor, user_id=user_id)
            self.save_posts_data(edges=edges_scrap, username=username, user_id=user_id)
            print('Data was crawl and saved.')



if __name__ == '__main__':
    from secret_data import TRUE_PROFILES
    profile = TRUE_PROFILES[0]
    account = Account(profile['username'], profile['password'])
    ans_login = account.login()
    account.get_posts('cristiano')



            
