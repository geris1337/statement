import json, requests, datetime, pytest
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException

url = 'http://localhost:9999/statements'

# Account for test_search_by_account
selected_account = "Peter Peterson" 
# Date range for test_search_by_date & test_balance_before
date1 = "2020-11-16 00:00:00"
date2 = "2020-11-19 00:00:00"

def getstamp(input):
    stamp = datetime.datetime.strptime(input, '%Y-%m-%d %H:%M:%S').replace(tzinfo=datetime.timezone.utc)
    return int(stamp.timestamp())

# POST data to endpoint
with open('data.json') as json_file:
    data = json.load(json_file)
    for item in data:
        myjson = {"statement": {"account_id": item['account_id'], "amount": item['amount'], "currency": item['currency'], "date": getstamp(item['date'])} }
        requests.post(url, json = myjson)

# Browser will open and close for each def_test
@pytest.fixture(autouse=True)
def open_browser():
    global driver
    driver = webdriver.Firefox()
    driver.get(url)
    yield
    driver.quit()

def test_data_table():
    for iteration, item in enumerate(data):
        # Check id matches with table data
        pit = iteration + 1 # (since first iteration = 0)
        pid = int(driver.find_element_by_xpath("//tbody/tr[%s+1]/th[1]" % iteration).text)
        assert pit == pid
        # Check if account_id matches with table data
        account = driver.find_element_by_xpath("//tbody/tr[%s+1]/td[1]" % iteration).text
        assert item['account_id'] == account
        # Check if amount & currency matches with table data
        amount = driver.find_element_by_xpath("//tbody/tr[%s+1]/td[2]" % iteration).text
        assert item['amount'] + " " + item['currency'] == amount
        # Check if date matches with table data
        date = driver.find_element_by_xpath("//tbody/tr[%s+1]/td[3]" % iteration).text
        assert item['date'] == date

def test_search_by_account():
    driver.find_element_by_id("search_account_id").send_keys(selected_account)
    driver.find_element_by_xpath("//button[@type='submit']").click()
    counter = 0

    for item in data:
        if item['account_id'] == selected_account:
            counter += 1

    elements = driver.find_elements_by_xpath("//*[contains(text(), '%s')]" % selected_account)
    # Check if number of found account elements match counter
    assert counter == len(elements)

def test_search_by_date():
    driver.find_element_by_xpath("//input[@name='from_date']").send_keys(date1)
    driver.find_element_by_xpath("//input[@name='to_date']").send_keys(date2)
    driver.find_element_by_xpath("//button[@type='submit']").click()

    start = datetime.datetime.strptime(date1, '%Y-%m-%d %H:%M:%S').replace(tzinfo=datetime.timezone.utc)
    end = datetime.datetime.strptime(date2, '%Y-%m-%d %H:%M:%S').replace(tzinfo=datetime.timezone.utc)

    for iteration, _ in enumerate(data):

        try:
            date = driver.find_element_by_xpath("//tbody/tr[%s+1]/td[3]" % iteration).text
            dateobj = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S').replace(tzinfo=datetime.timezone.utc)

            if start <= dateobj <= end:
                # This means test pass
                assert True
            else:
                # This means wrong date filtered, test fail
                assert False

        except NoSuchElementException:
            print("No more elements")

def test_balance_before():
    balance = 0.0

    # Navigate to filtered date range to retrieve ID of filtered firstid
    driver.find_element_by_xpath("//input[@name='from_date']").send_keys(date1)
    driver.find_element_by_xpath("//input[@name='to_date']").send_keys(date2)
    driver.find_element_by_xpath("//button[@type='submit']").click()

    firstid = driver.find_element_by_xpath("//tbody/tr[1]/th[1]").text

    # Calculate sum of amounts until firstid
    for i in range(int(firstid)-1):
        balance += float(data[i]['amount'])

    # Check balance before on filtered page
    balance_before = driver.find_element_by_xpath("//div[@class='container' and contains(text(), 'Balance before')]").text
    assert "Balance before: " + str("%.2f" % balance) + " " + item['currency'] == balance_before

def test_balance_after():
    balance = 0.0
    
    # Calculate sum of amounts in whole data.json
    for item in data:
        balance += float(item['amount'])
    
    # Check balance after on main page (string comparison)
    balance_after = driver.find_element_by_xpath("//div[@class='col-sm']/..").text.splitlines()[-1]
    assert "Balance after " + str("%.2f" % balance) + " " + item['currency'] == balance_after