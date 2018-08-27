from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import pandas as pd
import numpy as np
import re

def scraper(post_code,distance=5,make=None,model=None,min_price=None,max_price=None,webdriver_location='chromedriver.exe',max_page=5):
    """Function to scraper autotrader.co.uk 
    Parameters
    -----------
    post_code : string
        UK Postcode as string
    distance : int, default 5
        Distance from the postcode
        in miles. Must be multiple of 5
    make : string, default None
        car make i.e. Toyota, Honda etc
    model : string, default None
        A make must be provided in order
        to provide a model
    min_price : integer, default None
        Must be from list
        [0    500,    1000,    1500,    2000,    2500,    3000,    3500,
          4000,    4500,    5000,    5500,    6000,    6500,    7000,
          7500,    8000,    8500,    9000,    9500,   10000,   11000,
         11500,   12000,   12500,   13000,   13500,   14000,   14500,
         15000,   15500,   16000,   16500,   17000,   17500,   18000,
         18500,   19000,   19500,   20000,   22500,   25000,   27500,
         30000,   35000,   40000,   45000,   50000,   55000,   60000,
         65000,   70000,   75000,  250000,  500000, 1000000, 2000000]
    max_price : integer, default None
        Must be from list
        [0    500,    1000,    1500,    2000,    2500,    3000,    3500,
          4000,    4500,    5000,    5500,    6000,    6500,    7000,
          7500,    8000,    8500,    9000,    9500,   10000,   11000,
         11500,   12000,   12500,   13000,   13500,   14000,   14500,
         15000,   15500,   16000,   16500,   17000,   17500,   18000,
         18500,   19000,   19500,   20000,   22500,   25000,   27500,
         30000,   35000,   40000,   45000,   50000,   55000,   60000,
         65000,   70000,   75000,  250000,  500000, 1000000, 2000000]
    webdriver_location : string, default '..\\chromedriver.exe'
        location of chrome webdriver on your harddrive. 
    max_page : integer, default 5   
        """
    # Checking input & formatting
    assert distance%5==0,'distance must be multiple of 5'
    prices = np.concatenate((np.linspace(500,10000,num=20),np.linspace(11000,20000,num=19),np.linspace(22500,30000,num=4),np.linspace(35000,75000,num=9),np.array([250000*2**x for x in range(0,4)]))).astype('int')
    if min_price != None:
        assert min_price in prices or min_price==0,'Min price needs to be in: {0}'.format(list(prices))
        min_price = 'From £{:,}'.format(min_price)
    if max_price != None:
        assert max_price in prices,'Max price needs to be in: {0}'.format(list(prices))
        max_price = 'To £{:,}'.format(max_price)
    distance = 'Within {0} Miles'.format(distance)
    
    # Start up webdriver & move to autotrader website
    regular_search="https://www.autotrader.co.uk/"
    driver=webdriver.Chrome(webdriver_location)
    driver.get(regular_search)
    # Input search criteria
    if min_price != None:
        element=driver.find_element_by_xpath("//select[@name='price-from']")
        element.send_keys(min_price)
    if max_price != None:
        element=driver.find_element_by_xpath("//select[@name='price-to']")
        element.send_keys(max_price)
    if make != None:
        element=driver.find_element_by_xpath("//select[@name='make']")
        element.send_keys(make)
        if model != None:
            element=driver.find_element_by_xpath("//select[@name='model']")
            element.send_keys(model)
    element=driver.find_element_by_xpath("//select[@name='radius']")
    element.send_keys(distance)
    element=driver.find_element_by_xpath("//input[@name='postcode']")
    element.send_keys(post_code,Keys.ENTER)
    time.sleep(5)
    info_elements=[]
    price_elements=[]
    counter = 0
    cars_dictionary = {'name':[],'litre':[],'year':[],'distance':[],'drive':[],'bhp':[],'fuel':[],'price':[]}
    while len(driver.find_elements_by_class_name('pagination--right__active'))>0:
        if counter > max_page:
            break
        info_elements=driver.find_elements_by_xpath("//div[@class='information-container']")
        price_elements=driver.find_elements_by_class_name('vehicle-price')
        cars_dictionary = extract_info(info_elements,price_elements,cars_dictionary)
        click_item = driver.find_element_by_class_name('pagination--right__active')
        driver.execute_script("window.scrollTo(0, {0});".format(click_item.location['y']-100))
        click_item.click()
        if len(driver.find_elements_by_class_name('pagination--right__active'))==0:
            driver.navigate().to(driver.getCurrentUrl());
        time.sleep(5)
        counter+=1
    print('Elements returned')
    return pd.DataFrame(cars_dictionary)

def extract_info(info_elements,price_elements,cars_dictionary):
    for c,car in enumerate(info_elements):
        price_text = price_elements[c].text
        car_text = car.text
        #print(car_text)
        car_list = car_text.split('\n')
        # name
        #print(car_list)
        cars_dictionary['name'].append(car_text[:car_text.find('.')-2])
        # litre
        litre = re.findall('\d\.\dL',car_text)
        if len(litre)==0:
            cars_dictionary['litre'].append(None)
        else:
            cars_dictionary['litre'].append(litre[0])
        # year
        year = re.findall('\d\d\d\d',car_text)
        if len(year)==0:
            cars_dictionary['year'].append(None)
        else:
            cars_dictionary['year'].append(int(year[0]))
        # distance
        if len(re.findall('\d\d\d\,\d\d\d',car_text))!=0:
            distance=re.findall('\d\d\d\,\d\d\d',car_text)
        elif len(re.findall('\d\d\,\d\d\d',car_text))!=0:
            distance=re.findall('\d\d\,\d\d\d',car_text)
        else:
            distance = ['0']
        cars_dictionary['distance'].append(int(distance[0].replace(',','')))
        # drive
        car_text = car_text.lower()
        if 'manual' in car_text:
            drive = 'Manual'
        elif 'automatic' in car_text:
            drive = 'Automatic'
        else:
            drive = None
        cars_dictionary['drive'].append(drive)
        # bhp
        if len(re.findall('\d\dbhp',car_text))==0:
            bhp = None
        else:
            bhp = re.findall('\d\dbhp',car_text)[0]
        cars_dictionary['bhp'].append(bhp)
        # find petrol/diesel/hybrid
        if 'petrol' in car_text:
            fuel = 'petrol'
        elif 'diesel' in car_text:
            fuel = 'diesel'
        elif 'hybrid' in car_text:
            fuel = 'hybrid'
        else:
            fuel = None
        cars_dictionary['fuel'].append(fuel)
        #price
        if len(re.findall('\£\d\d\d\,\d\d\d',price_text))>0:
            price = re.findall('\£\d\d\d\,\d\d\d',price_text)[0].replace('£','')
        elif len(re.findall('\£\d\d\,\d\d\d',price_text))>0:
            price = re.findall('\£\d\d\,\d\d\d',price_text)[0].replace('£','')
        elif len(re.findall('\£\d\,\d\d\d',price_text))>0:
            price = re.findall('\£\d\,\d\d\d',price_text)[0].replace('£','')
        elif len(re.findall('\£\d\d\d',price_text))>0:
            price = re.findall('\£\d\d\d',price_text)[0].replace('£','')
        else:
            price = None
        cars_dictionary['price'].append(price)
    return cars_dictionary