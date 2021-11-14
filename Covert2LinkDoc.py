# coding:utf-8
import base64
import os.path

from bs4 import BeautifulSoup
import re


class Covert2LinkDoc:
    def __init__(self,fold_name, fileName, export_path = 'export'):

        true_path = f"{fold_name}/{fileName}"
        if not os.path.isfile(true_path):
            print(true_path,'为文件夹，不处理')
            return

        self.exclude_name = set(
            {'Procedure Specification Principles', 'Description','Definitions and Abbreviations', 'Abbreviations', 'Definitions',
             'Successful', 'Conditions', 'General', 'Unsuccessful', 'Abnormal Conditions', 'Operation',
             'Successful Operation', 'Unsuccessful Operation', 'Abnormal'})
        self.dict_for_index_title = dict()
        self.fold_name = fold_name


        print('处理',fileName)
        # fileName = 'O-RAN.WG3.E2AP-v01.01.htm'
        with open(true_path) as f:
            data = f.read()
        soup = self.preprocessing(data)

        #获取所有的标题
        self.get_index_title(self.dict_for_index_title, soup)

        # 替换所有的段落标题
        data = self.replace_all_text_title(soup)

        soup = BeautifulSoup(data, "html.parser")
        #设置头部id
        self.set_head_id(soup)

        #替换所有的表格标题
        self.replace_table_index(soup)

        #处理图片
        self.handler_word_img(soup)

        #设置html style
        self.set_html_style(soup)

        data = soup.__str__()
        # fileName.split('.')
        export_p = f"{fold_name}/{export_path}"
        if not os.path.exists(export_p) :
            # str_arr = export_p.split("/");
            # str_arr.pop()
            os.makedirs(export_p)
        with open(f'{export_p}/{fileName}', 'w', encoding='utf-8') as testfile:
            testfile.write(data)
            testfile.close()
            print('finish')

    #preprocessing
    def preprocessing(self, data):
        data = " ".join(data.split())
        soup = BeautifulSoup(data, "html.parser")
        soup = BeautifulSoup(soup.__str__().replace('\n',' ').replace('\r',''), "html.parser")
        return soup

    #拿到所有的标题
    def get_index_title(self, dict_for_index_title,soup):
        print("提取标题...")
        pattern = re.compile(r'^\d')
        def change(tag):
            for h in soup.find_all(tag):
                head_t = h.text.strip()
                if pattern.match(head_t) == None:
                    continue
                head = head_t.split()
                if len(head) == 1:
                    continue

                id_n = head[0].strip()
                id_t = ' '.join(head_t.replace(id_n, '').split())

                if id_t in self.exclude_name or pattern.match(id_t) is not None:
                    continue
                # h.attrs['id'] = id_t
                dict_for_index_title[id_n] = id_t

        for tag in ('h1', 'h2', 'h3', 'h4', 'h5'):
            change(tag)

        # 4级标题，不是在h标签中
        span_all = soup.find_all('span', {'lang': "EN-US"})
        pattern2 = re.compile('\d\\.\d\\.\d\\.\d')
        for span in span_all:
            # print(p.text.strip())

            if pattern2.match(span.text.strip()) is not None:
                p_t = span.text.strip()
                if pattern.match(p_t) == None:
                    continue
                # pattern = re.compile(r'hello')
                head = p_t.split()
                if len(head) == 1:
                    continue

                id_n = head[0].strip()
                id_t = ' '.join(p_t.replace(id_n, '').split())

                if id_t in self.exclude_name or pattern.match(id_t) is not None:
                    continue

                dict_for_index_title[id_n] = id_t

    def set_head_id(self, soup):
        print("设置标题链接ID...")
        pattern = re.compile(r'^\d')
        def change(tag):
            for h in soup.find_all(tag):
                head_t = h.text.strip()
                if pattern.match(head_t) == None:
                    continue
                head = head_t.split()
                if len(head) == 1:
                    continue

                id_n = head[0].strip()
                id_t = head_t.replace(id_n, '').strip()

                if id_t in self.exclude_name or pattern.match(id_t) is not None:
                    continue
                h.attrs['id'] = '-'.join(id_t.split())
                # dict_for_index_title[id_n] = id_t

        for tag in ('h1', 'h2', 'h3', 'h4', 'h5'):
            change(tag)

        # 4级标题，不是在h标签中
        span_all = soup.find_all('span', {'lang': "EN-US"})
        patternFor4head = re.compile('\d\\.\d\\.\d\\.\d')
        for span in span_all:
            # print(p.text.strip())
            if patternFor4head.match(span.text.strip()) is not None:
                p_t = span.text.strip()
                if pattern.match(p_t) == None:
                    continue
                # pattern = re.compile(r'hello')
                head = p_t.split()
                if len(head) == 1:
                    continue

                id_n = head[0].strip()
                id_t = p_t.replace(id_n, '').strip()

                if id_t in self.exclude_name or pattern.match(id_t) is not None:
                    continue

                span.attrs['id'] = '-'.join(id_t.split())

    #替换表格里面的序号
    def replace_table_index(self,soup):
        print("替换表格里面的序号...")
        soup = BeautifulSoup(soup.__str__(), "html.parser")
        tables = soup.find_all('table')
        pattern2 = re.compile(r"(\d\.)+\d*$")
        for t in tables:
            # print(p.text.strip())
            spans = t.find_all('span')
            for sp in spans:
                if pattern2.match(sp.text) is not None:
                    text = sp.text
                    sp.clear()
                    # print(text)
                    try :
                        id = '-'.join(self.dict_for_index_title[text].split())
                    except KeyError as e:
                        print("warning",e.__str__())
                    sp.append(BeautifulSoup(f'<a href="#{id}">{text}</a>', "html.parser"))

    def set_html_style(self,soup):
      soup.html['style'] = 'margin-left: 10%;margin-right: 10%;'

    def handler_word_img(self,soup):
        # 处理图片
        imgs = soup.find_all('img')
        title_png = 'data:image/png;base64,'
        title_jpg = 'data:image/jpeg;base64,'
        for img in imgs:
            src = img.attrs['src']
            title = title_png if src.find('png') != -1 else title_jpg
            with open(f"{fold_name}/{src}",'rb') as f:
                d_img = f.read()
                base64_data = base64.b64encode(d_img)
                # print(base64_data.decode())
            img.attrs['src'] = f'{title}{base64_data.decode()}'
        print("图片转化完成")

    def replace_all_text_title(self, soup):
        print("替换所有的段落标题...")
        data = soup.__str__()
        for id_n in self.dict_for_index_title.keys():
            id_t = self.dict_for_index_title[id_n]
            id_t_id = '-'.join(id_t.split())
            data = re.sub(id_t, f'<a href="#{id_t_id}">{id_t}</a>', data, flags=re.IGNORECASE)
        return data


fold_name = 'html'

for fileName in os.listdir(fold_name):
    Covert2LinkDoc(fold_name ,fileName)