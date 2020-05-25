import random
import re
import time
import requests

from functools import partial
from lxml import etree


class ReMethod(object):
    """
    提取歌曲id 和 专辑id的通用封装正则类
    """
    def __init__(self, component='song'):
        self.component = component

    def remethod(self, id):
        try:
            id = re.findall(r'^/{0}\?id=(.*)'.format(self.component), id)[0]
        except IndexError as e:
            pass
        else:
            if id:
                return id


class Wyy(object):
    def __init__(self, song_set_id='', picture_path='.', song_path='.'):
        self.song_set_id = song_set_id
        if self.song_set_id is '':
            raise NotImplementedError('请传入目标歌单id')

        if picture_path.endswith('/'):
            self.picture_path = picture_path[:-1]
        else:
            self.picture_path = picture_path

        if song_path.endswith('/'):
            self.song_path = song_path[:-1]
        else:
            self.song_path = song_path

        self.song_dict = {}
        self.header = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36',
          'referer': 'https://music.163.com/'}
        cookies = '_ntes_nnid=fac62bbf875fb02f052d4c8f9208aaa8,1584367126994; _ntes_nuid=fac62bbf875fb02f052d4c8f9208aaa8; WM_TID=haU%2FshAPPVdBQFEFRUcrBewPzQ6kotTa; P_OINFO=b642e58dcee1a8ed3031dad05bd6e62e@tencent.163.com|1586263505|0|cc|00&99|null#0|null|cc|b642e58dcee1a8ed3031dad05bd6e62e@tencent.163.com; WM_NI=8gqWW7Fh8seBka1NsZ53NYSajk%2Bhfd%2F3agK4oLvbZGHCb%2BVECnNm1Ny9bG6TDSL8rGQANKP1Zwjv8TXuPN1IwirIz8Dw5uCAITmGMWBGkwDsYMyBwT7RsjopynAqgz4JdzI%3D; WM_NIKE=9ca17ae2e6ffcda170e2e6ee99f46092e8acb1b845ba9a8fa7d44a868a9eaaf84487e8fcadb280b7aef9acb32af0fea7c3b92afcb9bfb8d63d86b8f894e84aa9bfffaff252f7ed82bad26baab5e589e570ededaf88ca40ad94ba83d94d8c9daeccd54f81b2828eb446bbe7aea8b560888d84d9f14d939f82acd33b9aa9a697bb609caba0afb443b5b7beaaf93488a9fb96c24b8b8ca3a8d05d8299a598c7799b93b7a3f660f58ebd8bee7cbbb28f92e672f896ac9bcc37e2a3; ntes_kaola_ad=1; JSESSIONID-WYYY=8X%5CqKwNwTomIV6QE6Z1mST%2FKq7Nt%2FegT53pWytXMOKdJbU%2FVPrIqddYtBoIRJ3xTDFa0egD6IbGyoqiD6%5CFJfVGPtOm7PSOPbg2ONpp%2Fjz%5CsgqolscknqbDoFcsOiRRa04anz8Z6O%2BSjBCgXYbxVGbhR6lvHZek18%2FgKpVu%2FbpK1vIyY%3A1590067066478; _iuqxldmzr_=32; MUSIC_U=c5c4ca656f95be51db37118f7899bc39a5710b23d401f2fc1be080adbcf4e18133a649814e309366; __remember_me=true; __csrf=c3cc540bdf30eb173394589bd545c5ff'
        self.cookie_dict = {cookie.split('=')[0]: cookie.split('=')[1] for cookie in cookies.split(';')}

    def _make_song_url(self, method, content, key):
        """
        构造爬虫url通用方法
        :param method: 通过调用某个方法获取单首歌曲字典详情列表
        :param content: 通过关键字参数确定构造url的类型 song:解析歌曲信息  album:解析歌曲专辑信息
        :param key: 根据不同的content参数需要传入不同类型的参数id song_id: 歌曲id  album_id:专辑id
        :return: 利用生成器返回构造完成的待解析url
        """
        song_dicts = method()
        for song_dict in song_dicts:
            url = 'https://music.163.com/{0}?id={1}'.format(content, song_dict[key])
            yield url

    def parse_song_id(self):
        """
        爬虫的起始方法,根据实例化传入的歌单id批量抓取该歌单中所有的歌曲id
        :return: 返回初始歌单字典{'歌曲id' , '歌曲名称'}
        """
        resp = requests.get('https://music.163.com/playlist?id={}'.format(self.song_set_id), headers=self.header, cookies=self.cookie_dict)
        html = etree.HTML(resp.text)
        ids = html.xpath('//ul[@class="f-hide"]//li/a/@href')
        ids = map(ReMethod().remethod, ids)
        names = html.xpath('//ul[@class="f-hide"]//li/a/text()')
        for k, v in dict(zip(names, list(ids))).items():
            self.song_dict['歌名'] = k
            self.song_dict['歌曲id'] = v
            self.song_dict['时长'] = '未知'
            yield self.song_dict

    def parse_song_detail(self):
        """
        根据上层获取的歌曲id 通过make_song_url制作出每首歌曲目标url深度爬取歌曲详情
        :return: 返回新生成的字典向下传递
        """
        song_urls = self._make_song_url(self.parse_song_id, 'song', '歌曲id')
        for song_url in song_urls:
            resp = requests.get(song_url, headers=self.header)
            html = etree.HTML(resp.text)
            img = html.xpath('//img[@class="j-img"]/@data-src')[0]
            singer = html.xpath('//a[@class="s-fc7"]/text()')[0]
            special_edition = html.xpath('//a[@class="s-fc7"]/text()')[1]
            special_edition_id = map(ReMethod(component='album').remethod, html.xpath('//a[@class="s-fc7"]/@href')[1:5])
            special_edition_id = [i for i in special_edition_id if i is not None][0]
            self.song_dict['歌手'] = singer
            self.song_dict['所属专辑'] = special_edition
            self.song_dict['专辑id'] = special_edition_id
            self.song_dict['图片url'] = img
            yield self.song_dict

    def parse_special_detail(self):
        """
        根据上层抓取的专辑id 通过make_song_url制作出每首歌曲所属专辑目标url深度爬取专辑详情
        :return: 返回完整的数据字典
        """
        special_detail_urls = self._make_song_url(self.parse_song_detail, 'album', '专辑id')
        for special_detail_url in special_detail_urls:
            resp = requests.get(special_detail_url, headers=self.header)
            html = etree.HTML(resp.text)
            song_detail_list = html.xpath('//p[@class="intr"]/text()')
            song_release = song_detail_list[0]
            if len(song_detail_list) >= 2:
                record_company = song_detail_list[1].replace('\n', '')
            else:
                record_company = '未知'
            self.song_dict['发行时间'] = song_release
            self.song_dict['唱片公司'] = record_company
            self.song_dict['语种'] = '华语&外语'
            yield self.song_dict

    def down_load_picture(self):
        """
        根据字典中的图片地址, 抓取歌曲的图片信息保存本地
        :return:
        """
        song_dicts = self.parse_song_detail()
        for song_dict in song_dicts:
            with open('{0}/{1}'.format(self.picture_path, song_dict['歌名']) + '.jpg', 'wb') as f:
                resp = requests.get(song_dict['图片url'], headers=self.header)
                f.write(resp.content)
            print('图片--{}--下载完成'.format(song_dict['歌名'] + '.jpg'))

    def down_load_song(self):
        """
        根据字典中的歌曲id, 下载歌曲保存本地
        :return:
        """
        song_dicts = self.parse_song_detail()
        for song_dict in song_dicts:
            try:
                with open('{0}/{1}'.format(self.song_path, song_dict['歌名']) + '.mp3', 'wb') as f:
                    resp = requests.get('https://music.163.com/song/media/outer/url?id={}'.format(song_dict['歌曲id']), headers=self.header)
                    f.write(resp.content)
                    print('歌曲--{}--下载成功'.format(song_dict['歌名']))
            except Exception as e:
                print('歌曲--{}--下载失败!!!'.format(song_dict['歌名']))

    def post_web(self):
        """个人搭配web项目使用的接口, 可忽略"""
        detail_dicts = self.parse_special_detail()
        for info in detail_dicts:
            data = {'csrfmiddlewaretoken': 'r9rlD4MbFkZ3nk7tcFRFPIxJLr7ijCbhCbaxfcxU552GLXQ5We8vRU4Bv2GqIljB',
                    'song_name': info['歌名'],
                    'song_singer': info['歌手'],
                    'song_time': '未知',
                    'song_album': info['所属专辑'],
                    'song_languages': info['语种'],
                    'song_company': info['唱片公司'],
                    'song_release': info['发行时间'],
                    'song_img': info['歌名'] + '.jpg',
                    'song_lyrics': '暂无歌词',
                    'song_file':  info['歌名'] + '.mp3',
                    'label': int(random.randint(1, 8)),
                    '_save': '保存'}
            cookie = 'csrf_token=ImIzNzNkMWRjMTRlODY4NjhiOTE5YmI3MjQyMjYzMzEzNjNhMjAyNzUi.EalR1Q.MGW0kp-GA9DaPLMCoKVlyhKX0Mk; session=8f4f21ce-8040-4514-9532-ca38121e7232.d0ze0E2wV-NUboMJxj3sltzq2vc; csrftoken=GOLz0aaT2QliCyP3fplpFMHgjSEItH1uRQuLCiVCsBoV0byFZYCfHYe83tdQSq9O; sessionid=0qnu8bpd2zhp6rswpzh2t8tant46xa6n'
            cookie_dict = {cookie.split('=')[0]: cookie.split('=')[1] for cookie in cookie.split(';')}
            url = 'http://个人web网站地址:8080/admin/index/song/add/'
            import requests
            resp = requests.post(url, data=data, cookies=cookie_dict, headers=self.header)
            if resp.status_code == 200:
                print('歌曲 {} 上传成功'.format(info['歌名']))

    def main(self):
        """启动函数, 需要调用的接口可以在此处编写"""
        # song_dicts = self.parse_special_detail()
        # for song_dict in song_dicts:
        #     print(song_dict)
        self.down_load_picture()
        # self.parse_song_id()
        # self.post_web()
        pass


if __name__ == '__main__':
    song = Wyy(song_set_id='2829883282', picture_path='./')
    song.main()
    pass



