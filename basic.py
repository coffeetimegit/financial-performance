from flask import Flask, render_template
import static_data
import all_company

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("home.html")

@app.route("/industry_list")
def industry_list():
    industry_list = [k for k, v in static_data.industry_dict.items()]
    return render_template("industries.html", industry_list=industry_list)


@app.route("/fund_list")
def fund_list():
    return render_template("companies.html", company_list=static_data.fund_dict)


@app.route("/company_list/<company>")
def company_list(company):
    company_list = static_data.industry_dict[company]
    return render_template("companies.html", company_list=company_list)


@app.route("/performance_report/<code>")
def company_performance(code):
    reports = all_company.main(code)
    return render_template('report.html', reports=reports)


if __name__ == "__main__":
    print("hello")
    app.run(debug=True)
