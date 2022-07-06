from selenium import webdriver
import time
import pandas as pd
from datetime import datetime
import os

class ReportDriver:
    def __init__(self, driver_path, update_date_xpath, company_xpath, pdf_xpath, table_row_xpath, url_list_xpath):
        self.driver_path = driver_path
        self.update_date_xpath = update_date_xpath
        self.company_xpath = company_xpath
        self.pdf_xpath = pdf_xpath
        self.table_row_xpath = table_row_xpath
        self.url_list_xpath = url_list_xpath

    def webdriver_instance(self):

        op = webdriver.ChromeOptions()
        op.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
        op.add_argument("--headless")
        op.add_argument("--no-sandbox")
        op.add_argument("--disable-dev-sh-usage")
        driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=op)
        return driver

    def convert_date(self, jpn_date):
        if jpn_date[0] == "R":
            year = 2019
        elif jpn_date[0] == "H":
            year = 1989
        elif jpn_date[0] == "S":
            year = 1926
        else:
            raise Exception

        year += int(jpn_date.split(".")[0][1:]) - 1
        modular = "".join(jpn_date.split(".")[1:])
        update_date = str(year) + modular

        return datetime.strptime(update_date, "%Y%m%d %H:%M")

    def filter_irrelevant_rows(self, df, company_list, driver):
        start = time.time()
        filenames = driver.find_elements_by_xpath(self.table_row_xpath)
        filename = [i.text.split()[2] for i in filenames]
        companies = driver.find_elements_by_xpath(f"{self.table_row_xpath}{self.company_xpath}")
        companies = [company.text for company in companies]
        update_date = driver.find_elements_by_xpath(f"{self.table_row_xpath}{self.update_date_xpath}")[1:]
        update_date = [self.convert_date(update.text) for update in update_date]
        pdfs = driver.find_elements_by_xpath(f"{self.table_row_xpath}{self.pdf_xpath}")
        pdfs = [pdf.get_attribute("href") for pdf in pdfs]
        end = time.time()
        print(f"IO bound operation took {round(end - start, 2)} second(s) to complete.")

        # vectorize with pandas
        start = time.time()
        target_df = pd.DataFrame({"filename": filename[1:],
                                  "company": companies,
                                  "update_date": update_date,
                                  "pdf_report": pdfs})
        filt = ((target_df["filename"].str.contains("有価証券報告書")) & (~target_df["filename"].str.contains("訂正")) & (
            ~target_df["company"].isin(company_list)))
        df_filtered = target_df[filt]
        df_filtered.drop_duplicates(subset=["company"], inplace=True)
        df_filtered.drop("filename", axis=1, inplace=True)
        df = pd.concat([df, df_filtered], ignore_index=True)

        end = time.time()
        print(f"CPU bound operation took {round(end - start, 2)} second(s) to complete.")
        # print(df_filtered)
        # df_filtered.to_csv(f"{time.time()}.csv", index=False)

        companies_unique = set(companies)
        if company_list:
            for i in companies_unique:
                if i not in company_list:
                    company_list.add(i)
            # print(f"if clause: {company_list}")

        else:
            company_list = set(companies)
            # print(f"else clause: {company_list}")

        # print(df_filtered)

        end = time.time()

        return [df, company_list]





    def output(self, filtered_list):
        for k, v in filtered_list.items():
            print(k, v[0], v[1])


    def get_url(self, index):
        url_prefix = "https://disclosure.edinet-fsa.go.jp/E01EW/BLMainController.jsp?uji.verb=W1E63011CXP001002Action&uji.bean=ee.bean" \
                     ".parent.EECommonSearchBean&TID=W1E63011&PID=W1E63011&SESSIONKEY=1656758727065&lgKbn=2&pkbn=0&skbn=1&dskb=&askb" \
                     "=&dflg=0&iflg=0&preId=1&mul=&fls=on&cal=2&yer=&mon=&pfs=4&row=100&idx="
        url_suffix = "&str=&kbn=1&flg=&syoruiKanriNo= "

        return f"{url_prefix}{index}{url_suffix}"


    def page_count(self, driver):
        url = "https://disclosure.edinet-fsa.go.jp/E01EW/BLMainController.jsp?uji.verb=W1E63011CXP001002Action&uji.bean" \
              "=ee.bean.parent.EECommonSearchBean&TID=W1E63011&PID=W1E63011&SESSIONKEY=1656759278844&lgKbn=2&pkbn=0&skbn" \
              "=1&dskb=&askb=&dflg=0&iflg=0&preId=1&mul=&fls=on&cal=2&yer=&mon=&pfs=4&row=100&idx=0&str=&kbn=1&flg" \
              "=&syoruiKanriNo= "
        driver.get(url)
        print(len(driver.find_elements_by_xpath(self.url_list_xpath)) - 1)
        return len(driver.find_elements_by_xpath(self.url_list_xpath)) - 1


    def get_reports(self, df, company_list, pages, driver):
        for i in range(pages-27):
            url = self.get_url(i * 100)
            driver.get(url)
            df, company_list = self.filter_irrelevant_rows(df, company_list, driver)

        return df

"""
op = webdriver.ChromeOptions()
op.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
op.add_argument("--headless")
op.add_argument("--no-sandbox")
op.add_argument("--disable-dev-sh-usage")
driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=op)
"""


"""
path = '/Users/yutakaobi/PycharmProjects/CompanyProfile/edgedriver_mac64 2/msedgedriver'
print(path)
desired_cap = {}
driver = webdriver.Edge(executable_path=path, capabilities=desired_cap)

ReportDriver
update_date_xpath = "/td[1]/div"
company_xpath = "/td[4]/a"
pdf_xpath = "/td[6]/div/a"
table_row_xpath = "//*[@id='control_object_class1']/div/div[8]/table/tbody/tr"
url_list_xpath = "//*[@id='pageTop']/span/a"

pages = page_count(url_list_xpath)
df = pd.DataFrame(columns=["company", "update_date", "pdf_report"])

company_list = set()

df = get_reports(df, company_list, pages)
df.to_csv("company_performance.csv", index=False)
print(df)

driver.quit()
"""

