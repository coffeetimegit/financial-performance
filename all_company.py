import DriverClass
import pandas as pd


def main(code):
    web_elements = DriverClass.ReportDriver(driver_path="CHROMEDRIVER_PATH",
                                            driver_bin="GOOGLE_CHROME_BIN",
                                            update_date_xpath="/td[1]/div",
                                            company_xpath="/td[4]/a",
                                            pdf_xpath="/td[6]/div/a",
                                            table_row_xpath="/html/body/div/div[1]/div/div/div[2]/div/form/div/div[7]/table/tbody/tr",
                                            url_list_xpath="//*[@id='pageTop']/span/a",
                                            fund_code=code)
    driver = DriverClass.ReportDriver.webdriver_instance(web_elements)
    df = pd.DataFrame(columns=["提出書類", "提出者／ファンド", "提出日時", "pdf"])
    pages = DriverClass.ReportDriver.page_count(web_elements, driver) + 1

    reports = DriverClass.ReportDriver.get_reports(web_elements, df, pages, driver)

    driver.quit()

    return reports


if __name__ == "__main__":
    main()