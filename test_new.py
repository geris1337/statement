import json, requests, datetime, pytest, re
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
url = 'http://localhost:9999/statements'

# Browser will open and close for each def_test
@pytest.fixture(autouse=True)
def open_browser():
    global driver
    driver = webdriver.Firefox()
    driver.get(url)
    yield
    driver.quit()

def getstamp(input):
    stamp = datetime.datetime.strptime(input, '%Y-%m-%d %H:%M:%S').replace(tzinfo=datetime.timezone.utc)
    return int(stamp.timestamp())

# POST data to endpoint
with open('data.json') as json_file:
    data = json.load(json_file)
    for item in data:
        myjson = {"statement": {"account_id": item['account_id'], "amount": item['amount'], "currency": item['currency'], "date": getstamp(item['date'])} }
        requests.post(url, json = myjson)

def scrape_data():
    global scraped_data, scraped_data_comp, scraped_arr
    scraped_data = []
    scraped_data_comp = [] 
    scraped_arr = []
    
    # Scrape table data into array (multi-page)
    while True:
        try:
            rows = driver.find_elements_by_xpath("//tbody/tr")
            for row in rows:
                for th in row.find_elements_by_xpath(".//th"):
                    scraped_arr.append(th.text)
                for item in row.find_elements_by_xpath(".//td"):
                    scraped_arr.append(item.text)

            button = driver.find_element_by_xpath("//a[@rel='next']")
            button.click()
        except NoSuchElementException:
            print("No more elements")
            break

    # Group array by 4 elements
    scraped_group_arr = [scraped_arr[n:n+4] for n in range(0, len(scraped_arr), 4)]

    # Prepare grouped array data for json
    for item in scraped_group_arr:
        scraped_data.append({
            'id': item[0],
            'account_id': item[1],
            'amount': str(re.findall(r"[-+]?\d*\.\d+|\d+", item[2])).strip("[']"),
            'currency': item[2].split(" ")[1:][0],
            'date': item[3]
        })

    # Write scraped data to json
    with open('scraped.json', 'w') as outfile:
        json.dump(scraped_data, outfile, indent=2)

    # Create new array without first index for comparison
    scraped_data_comp = scraped_data
    for scraped_item in scraped_data_comp:
        scraped_item.pop('id', None)

def test_data_table():
    scrape_data()

    for item in data:
        if item in scraped_data_comp:
            # Posted data exists in scraped table
            print("SUCCESS")
            assert True
        else:
            # Posted data does not exist in scraped table
            print("FAIL")
            assert False, "The following data does not exist in scraped table \n %s" % item

def test_search_by_account():
    accounts = []

    for item in data:
        accounts.append(item['account_id'])

    # Create a set for iteration of unique accounts
    account_set = set(accounts)

    for selected_account in account_set:
        print("------------------------------")
        print("Currently iterating: " + selected_account)

        driver.find_element_by_id("search_account_id").clear()
        driver.find_element_by_id("search_account_id").send_keys(selected_account)
        driver.find_element_by_xpath("//button[@type='submit']").click()

        scrape_data()
        
        for item in data:
            if item['account_id'] == selected_account:
                if item in scraped_data_comp:
                    # Posted data exists in scraped table
                    print("SUCCESS")
                    assert True
                else:
                    # Posted data does not exist in scraped table
                    print("FAIL")
                    assert False, "The following data does not exist in scraped table \n %s" % item
            else:
                print("%s is not the selected_account in this iteration, will not compare" % item['account_id'])

def test_search_by_date():
    for item in data:
        # Generate start and end dates from date in data.json
        dateobj = datetime.datetime.strptime(item['date'], '%Y-%m-%d %H:%M:%S').replace(tzinfo=datetime.timezone.utc)
        start = dateobj - datetime.timedelta(days=1)
        end = dateobj + datetime.timedelta(days=1)
        
        driver.find_element_by_xpath("//input[@name='from_date']").clear()
        driver.find_element_by_xpath("//input[@name='from_date']").send_keys(str(start))
        driver.find_element_by_xpath("//input[@name='to_date']").clear()
        driver.find_element_by_xpath("//input[@name='to_date']").send_keys(str(end))
        driver.find_element_by_xpath("//button[@type='submit']").click()

        scrape_data()

        if item in scraped_data_comp:
            # Posted date exists in scraped table
            print("SUCCESS")
            assert True
        else:
            # Posted date does not exist in scraped table
            print("FAIL")
            assert False, "The following data does not exist in scraped table \n %s" % item

def test_balance_before():
    scrape_data()

    for item in data:
        balance = 0.0
        # Generate start and end dates from date in data.json
        dateobj = datetime.datetime.strptime(item['date'], '%Y-%m-%d %H:%M:%S').replace(tzinfo=datetime.timezone.utc)
        start = dateobj - datetime.timedelta(days=1)
        end = dateobj + datetime.timedelta(days=1)

        # Navigate to filtered date range to see balance_before
        driver.find_element_by_xpath("//input[@name='from_date']").clear()
        driver.find_element_by_xpath("//input[@name='from_date']").send_keys(str(start))
        driver.find_element_by_xpath("//input[@name='to_date']").clear()
        driver.find_element_by_xpath("//input[@name='to_date']").send_keys(str(end))
        driver.find_element_by_xpath("//button[@type='submit']").click()

        # Calculate sum of amounts in whole scraped_data_comp
        for number in scraped_data_comp:
            date_comp = datetime.datetime.strptime(number['date'], '%Y-%m-%d %H:%M:%S').replace(tzinfo=datetime.timezone.utc)

            # Only sum elements with previous date
            if (date_comp <= start):
                balance += float(number['amount'])
                print("Element: " + str(number))

        print("Balance: " + str(balance))

        # Check balance before on filtered page
        balance_before = driver.find_element_by_xpath("//div[@class='container' and contains(text(), 'Balance before')]").text
        assert "Balance before: " + str("%.2f" % balance) + " " + item['currency'] == balance_before

def test_balance_after():
    balance = 0.0

    scrape_data()

    # Calculate sum of amounts in whole scraped_data_comp
    for item in scraped_data_comp:
        balance += float(item['amount'])

    # Check balance after on last available page (string comparison)
    balance_after = driver.find_element_by_xpath("//div[@class='col-sm']/..").text.splitlines()
    
    for line in balance_after:
        if line.startswith('Balance after'):
            assert "Balance after " + str("%.2f" % balance) + " " + item['currency'] == line