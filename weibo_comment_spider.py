from bs4 import BeautifulSoup
import requests
import re
import urllib3
import hashlib

cookie = {"Cookie": "your_cookies"}
urllib3.disable_warnings()
headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:66.0) Gecko/20100101 Firefox/66.0'
}

def create_table(url):
    table_name = url[25:34]
    create_comment_sql = """CREATE TABLE %s_comment (
    `id` INT NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(45) NULL,
    `content` LONGTEXT CHARACTER SET 'utf8mb4' NULL,
    `name_content_md5` VARCHAR(45) NULL,
    `time_device` VARCHAR(45) NULL,
    `up_num` INT NULL,
    PRIMARY KEY (`id`))
    ENGINE = InnoDB
    DEFAULT CHARACTER SET = utf8mb4;\n""" % table_name
    return create_comment_sql

def get_pagenum(url):
    html = requests.get(url, headers=headers, cookies=cookie, verify=False).content
    soup = BeautifulSoup(html, 'lxml')
    # print(soup.prettify())
    pagenum = int(soup.find(attrs={'id': 'pagelist'}).find(attrs={'type': 'hidden'})['value'])
    print('Total page number is', pagenum)
    return pagenum

def get_content(url, f):
    table_name = url[25:34]
    pagehtml = requests.get(url, cookies=cookie, verify=False).content
    soup = BeautifulSoup(pagehtml, 'lxml')
    author = soup.find(attrs={'id': 'M_'}).div.a.string
    content = soup.find(attrs={'id': 'M_'}).div.span.get_text().strip(':')
    insert_sql = """INSERT INTO items (`serial_num`, `author`, `content`) VALUES ('%s', '%s', '%s');\n""" % (table_name, author, content)
    f.write(insert_sql)

def get_comment_sql(url, f):
    table_name = url[25:34]
    pagehtml = requests.get(url, cookies=cookie, verify=False).content
    soup = BeautifulSoup(pagehtml, 'lxml')
    creg = re.compile('C_\d{16}')
    content = soup.find_all(attrs={'id': creg})
    for con in content:
        name = con.a.string
        content = con.find_all(attrs={'class': 'ctt'})[0].get_text().replace("'", "''")
        name_content_md5 = hashlib.md5((name + content).encode("utf-8"))
        time_device = con.find_all(attrs={'class': 'ct'})[0].get_text().replace(u'\xa0', u' ')
        if re.findall("\d+", con.find_all(attrs={'class': 'cc'})[0].a.string):
            up_num = int(re.findall("\d+", con.find_all(attrs={'class': 'cc'})[0].a.string)[0])
        else:
            up_num = int(re.findall("\d+", con.find_all(attrs={'class': "cmt"})[0].string)[0])
        insert_sql = """INSERT INTO %s_comment (`name`, `content`, `name_content_md5`, `time_device`, `up_num`) VALUES ('%s', '%s', '%s', '%s', %d);\n""" % (table_name, name, content, name_content_md5.hexdigest(), time_device, up_num)
        f.write(insert_sql)

if __name__ == '__main__':
    url = 'https://weibo.cn/comment/Hsj1Cj3iO?uid=1907214345&rl=0'
    page_num = get_pagenum(url)
    table_name = url[25:34]
    f = open('%s.sql' % table_name, 'w', encoding='utf-8')
    f.write('use weibo;\n')
    f.write('/* ==============CREATE============== */\n')
    create_sql = create_table(url)
    f.write(create_sql)
    f.write('/* ==============INSERT============== */\n')
    get_content(url, f)
    for i in range(1, page_num+5):
        pageurl = url + '&page=' + str(i)
        get_comment_sql(pageurl,f)
        print("page %d/%d completed" % (i, page_num))
