import numpy as np
import os


class Queue():
    # def __int__(self):
    candidates = [] # 保存候选的请求列表
    # has_viewed = set() # 保存已经被处理过的请求
    # self.max_num = max_num # 保存最多可
    save_every = 100 # has_viewed每100次执行一次保存以记录
    # 初始化时需要添加若干个入口请求
    candidates.append('https://www.baidu.com')
    candidates.append('https://zh.wikipedia.org/wiki/Category:%E8%AE%A1%E7%AE%97%E6%9C%BA%E7%BC%96%E7%A8%8B')

    def __init__(self):
        self.has_viewed = set()

    def load_npy(self):
        if not os.path.exists('../origin_page/has_viewed.npy'):
            self.save_has_viewed()
        with open('../origin_page/has_viewed.npy', 'rb') as f:
            self.has_viewed = np.load(f, allow_pickle=True).tolist()

    def save_has_viewed(self):
        if not os.path.exists('../origin_page'):
            os.mkdir('../origin_page')
        with open('../origin_page/has_viewed.npy', 'wb+') as f:
            np.save(f, self.has_viewed, allow_pickle=True)

    def add_candidate(self, url):
        # 注意，执行该函数说明获得了一个新的请求，需要待处理（从分类或内容页面解析得到的链接）
        if url not in self.candidates and url not in self.has_viewed:
            self.candidates.append(url)

    def add_candidates(self, url_list):
        # 批量添加注意，执行该函数说明获得了一个新的请求，需要待处理（从分类或内容页面解析得到的链接）
        for url in url_list:
            self.add_candidate(url)

    def delete_candidate(self, url):
        # 注意，执行该函数时，说明有进程已经收到该请求，在处理前需要将候选列表中该请求删除，表示已有进程已经拿到该请求
        if url in self.candidates:
            self.candidates.remove(url)

    def add_has_viewed(self, url):
        # 注意，执行该函数时，说明有进程已经收到请求，并进行了相关处理，现需要更新队列状态
        if url is not None:
            self.has_viewed.add(url)

