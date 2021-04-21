from selenium import webdriver
import pymysql

class GovSpider(object):
  def __init__(self):
    # 设置无界面
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    # 添加参数
    self.browser = webdriver.Chrome(options=options)
    self.one_url = 'http://www.mca.gov.cn/article/sj/xzqh/2021/'
    self.db = pymysql.connect(
      'localhost','root','****','govdb',charset='utf8'
    )
    self.cursor = self.db.cursor()
    # 创建3个列表,用来executemany()往3张表中插入记录
    self.province_list = []
    self.city_list = []
    self.county_list = []

  def get_incr_url(self):
    self.browser.get(self.one_url)
    # 提取最新链接,判断是否需要增量爬
    td = self.browser.find_element_by_xpath(
      '//td[@class="arlisttd"]/a[contains(@title,"代码")]'
    )
    # 提取链接 和 数据库中做比对,确定是否需要怎俩那个抓取
    # get_attribute()会自动补全提取的链接
    two_url = td.get_attribute('href')
    sel = 'select url from version where url=%s'
    # result为返回的受影响的条数
    result = self.cursor.execute(sel,[two_url])
    if result:
      print('无须爬取')
    else:
      td.click()
      # 切换句柄
      all_handlers = self.browser.window_handles
      self.browser.switch_to.window(all_handlers[1])
      self.get_data()
      # 把URL地址存入version表
      dele = 'delete from version'
      ins = 'insert into version values(%s)'
      self.cursor.execute(dele)
      self.cursor.execute(ins,[two_url])
      self.db.commit()

  def get_data(self):
    tr_list = self.browser.find_elements_by_xpath(
      '//tr[@height="19"]'
    )
    for tr in tr_list:
      code = tr.find_element_by_xpath('./td[2]').text.strip()
      name = tr.find_element_by_xpath('./td[3]').text.strip()
      print(name,code)
      # 把数据添加到对应的表中
      if code[-4:] == '0000':
        self.province_list.append([name,code])
        if name in ['北京市','天津市','上海市','重庆市']:
          self.city_list.append([name,code,code])

      elif code[-2:] == '00':
        self.city_list.append([name,code,(code[:2]+'0000')])

      else:
        if code[:2] in ['11','12','31','50']:
          self.county_list.append([name,code,(code[:2]+'0000')])
        else:
          self.county_list.append([name,code,(code[:4]+'00')])

    # 执行数据库插入语句
    self.insert_mysql()

  def insert_mysql(self):
    # 1. 先删除原有数据
    del_province = 'delete from province'
    del_city = 'delete from city'
    del_county = 'delete from county'
    self.cursor.execute(del_province)
    self.cursor.execute(del_city)
    self.cursor.execute(del_county)
    # 2. 插入新数据
    ins_province = 'insert into province values(%s,%s)'
    ins_city = 'insert into city values(%s,%s,%s)'
    ins_county = 'insert into county values(%s,%s,%s)'
    self.cursor.executemany(ins_province,self.province_list)
    self.cursor.executemany(ins_city,self.city_list)
    self.cursor.executemany(ins_county,self.county_list)
    # 3.提交到数据库执行
    self.db.commit()

  def main(self):
    self.get_incr_url()
    self.cursor.close()
    self.db.close()
    self.browser.quit()

if __name__ == '__main__':
  spider = GovSpider()
  spider.main()














































