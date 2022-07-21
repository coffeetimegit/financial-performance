from selenium import webdriver
import time
import pandas as pd
from datetime import datetime
import os


class ReportDriver:
    def __init__(self, driver_path, driver_bin, update_date_xpath, company_xpath, pdf_xpath, table_row_xpath, url_list_xpath, fund_code):
        self.driver_path = driver_path
        self.driver_bin = driver_bin
        self.update_date_xpath = update_date_xpath
        self.company_xpath = company_xpath
        self.pdf_xpath = pdf_xpath
        self.table_row_xpath = table_row_xpath
        self.url_list_xpath = url_list_xpath
        self.fund_code = fund_code

    def webdriver_instance(self):

        op = webdriver.ChromeOptions()
        op.binary_location = os.environ.get(self.driver_bin)
        op.add_argument("--headless")
        op.add_argument("--no-sandbox")
        op.add_argument("--disable-dev-sh-usage")
        driver = webdriver.Chrome(executable_path=os.environ.get(self.driver_path), chrome_options=op)
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

    def filter_irrelevant_rows(self, df, driver):
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

        if len(companies) == 0:
            return df

        start = time.time()
        target_df = pd.DataFrame({"提出書類": filename[1:],
                                  "提出者／ファンド": companies,
                                  "提出日時": update_date,
                                  "pdf": pdfs})

        filt = (~target_df["提出書類"].str.contains("訂正") & (target_df["提出書類"].str.contains("報告書")))
        df_filtered = target_df[filt]

        df = pd.concat([df, df_filtered], ignore_index=True)

        end = time.time()
        print(f"CPU bound operation took {round(end - start, 2)} second(s) to complete.")

        return df



    def get_url(self, index):


        url_prefix = "https://disclosure.edinet-fsa.go.jp/E01EW/BLMainController.jsp?uji.verb=W1E63011CXP001002Action" \
                     "&uji.bean=ee.bean.parent.EECommonSearchBean&TID=W1E63011&PID=W1E63011&SESSIONKEY=1657207893643" \
                     "&lgKbn=2&pkbn=0&skbn=1&dskb=&askb=&dflg=0&iflg=0&preId=1&mul="

        url_middle = "&fls=on&cal=1&era=R&yer=&mon=&pfs=4&row=100&idx="

        url_suffix = "&str=&kbn=1&flg=&syoruiKanriNo= "

        return f"{url_prefix}{self.fund_code}{url_middle}{index}{url_suffix}"

    def page_count(self, driver):
        url_prefix = "https://disclosure.edinet-fsa.go.jp/E01EW/BLMainController.jsp?uji.verb" \
                     "=W1E63011CXW1E6A011DSPSch&uji.bean=ee.bean.parent.EECommonSearchBean&TID=W1E63011&PID=W1E63011" \
                     "&SESSIONKEY=1657205483096&lgKbn=2&pkbn=0&skbn=1&dskb=&askb=&dflg=0&iflg=0&preId=1&mul="

        url_suffix = "&fls=on&cal=1&era=R&yer=&mon=&pfs=4&row=100&idx=0&str=&kbn=1&flg=&syoruiKanriNo= "

        url = f"{url_prefix}{self.fund_code}{url_suffix}"

        driver.get(url)

        return len(driver.find_elements_by_xpath(self.url_list_xpath)) - 1


    def transform_df(self, df):

        提出日時 = list(df['提出日時'])
        提出者ファンド = list(df['提出者／ファンド'])
        提出書類 = list(df['提出書類'])
        pdf = list(df['pdf'])
        size = len(提出日時)

        reports = []
        for i in range(size):
            reports.append([提出日時[i], 提出者ファンド[i], 提出書類[i], pdf[i]])
        return reports

    def get_reports(self, df, pages, driver):
        if pages == 0:
            url = self.get_url(0)
            driver.get(url)
            df = self.filter_irrelevant_rows(df, driver)

        for i in range(pages):
            print("iterate")
            url = self.get_url(i * 100)
            driver.get(url)
            df = self.filter_irrelevant_rows(df, driver)

        df = df.sort_values(by=['提出日時'], ascending=False)
        df = self.transform_df(df)

        return df