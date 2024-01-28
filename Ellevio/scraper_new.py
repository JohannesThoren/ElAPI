# Copyright 2024 johannes. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import time
import json
import logging
from typing import List

from PIL import Image

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement

ROOT_URL = "https://avbrottskarta.ellevio.se/"
COUNTY_URL = "https://avbrottskarta.ellevio.se/län/"
MUNICIPALITY_URL = "https://avbrottskarta.ellevio.se/kommun/"

# log setup


class EllevioScraper:
    def __init__(self) -> None:
        firefox_options = Options()
        firefox_options.add_argument("--headless")
        self.Driver = webdriver.Firefox(options=firefox_options)
        self.CountiesWithOutage: List[str] = []
        self.MunicipalitiesWithOutage = []
        self.Outages = []
        self.Driver.implicitly_wait(10)

        pass

    def __CreateOutageDict(
        self,
        municipality: str,
        startTime: str,
        endTime: str,
        infoText: str,
        lastUpdate: str,
        affected_customers: int
    ) -> dict:
        outage = {
            "municipality": municipality,
            "start_time": startTime,
            "end_time": endTime,
            "info_text": infoText,
            "last_update": lastUpdate,
            "affected_customers": affected_customers
        }

        logging.info(f"Outage dict created: {outage}")
        return outage

    def __GetPlaceNameWithOutages(self, rows: List[WebElement]) -> List[str]:
        rowsWithOutages = []

        for row in rows:
            cells = row.find_elements(by=By.TAG_NAME, value="td")
            logging.debug(f"{cells[0].text} {cells[1].text} {cells[2].text}")
            if cells[1].text != "0" or cells[2].text != "0":
                logging.info(f"Found outages in {cells[0].text}")
                if cells[0].text == "V Götalands län":
                    rowsWithOutages.append("västragötaland")
                else:
                    rowsWithOutages.append(cells[0].text)

        return rowsWithOutages

    def __TakeScreenShot(self, fileName, x, y, w, h):
        logging.info("Taking ScreenShot")

        self.Driver.save_screenshot(fileName + ".png")
        im = Image.open(fileName + ".png")
        im = im.crop((x, y, w, h))
        im.save(fileName + ".png")

    def __Sleep(self, secs: int):
        logging.info("Sleeping 1 sec so the page can load")
        time.sleep(secs)

    def __DriverGet(self, url: str):
        logging.info(f"GET request sent to {url}")
        self.Driver.get(url)

    def __GetCountyTableRows(self):
        logging.info("Getting the county table")

        self.__DriverGet(ROOT_URL)
        self.__Sleep(1)

        county_table_element = self.Driver.find_element(
            by=By.CLASS_NAME, value="InfoBox_locationList__1AKS1"
        )

        rows = county_table_element.find_elements(by=By.TAG_NAME, value="tr")

        # ta bort det förtsta elementet (titel texten)
        rows.pop(0)

        # spara undan och ta bort totala avbrott från listan
        rows.pop(len(rows) - 1)
        return rows

    def GetCountiesWithOutage(self):
        logging.info("Checking for counties with outages")
        rows = self.__GetCountyTableRows()

        for county in self.__GetPlaceNameWithOutages(rows):
            county = county.split(" ")[0].rstrip("s").lower()
            self.CountiesWithOutage.append(county)


        logging.info(
            f"There are a total of {len(self.CountiesWithOutage)} counties with outages"
        )

    def GetMunicipalitiesWithOutage(self) -> list:
        logging.info("Getting Municipalities with outages")

        for county in self.CountiesWithOutage:
            logging.debug("Getting Municipalities with outages in " + county)
            self.__DriverGet(f"{COUNTY_URL}{county}/idag")
            self.__Sleep(1)

            municipality_table_element = self.Driver.find_element(
                by=By.CLASS_NAME, value="InfoBox_locationList__1AKS1"
            )

            municipality_rows = municipality_table_element.find_elements(
                by=By.TAG_NAME, value="tr"
            )
            municipality_rows.pop(0)
            municipality_rows.pop(len(municipality_rows) - 1)


            for municipality in self.__GetPlaceNameWithOutages(municipality_rows):
                    self.MunicipalitiesWithOutage.append(municipality.lower())
        
        logging.info(
            f"There are a total of {len(self.MunicipalitiesWithOutage)} municipalities with outages"
        )

    def GetOutages(self):
        for municipality in self.MunicipalitiesWithOutage:
            self.__DriverGet(MUNICIPALITY_URL + municipality)
            self.__Sleep(2)

            # acceptera kakor
            self.__AcceptCookies()

            # ta en skärmdump
            self.Driver_window_size = self.Driver.get_window_size()

            self.__TakeScreenShot(
                municipality,
                370,
                40,
                self.Driver_window_size.get("width") - 100,
                self.Driver_window_size.get("height") - 200,
            )

            info_container = self.Driver.find_element(
                by=By.CLASS_NAME, value="InterruptInfo_timestampsContainer__3f5L_"
            )

            # det finns en nästlad div i diven med klassnamn InterruptInfo_timestampsContainer__3f5L_ som har all data
            info_container = info_container.find_element(by=By.TAG_NAME, value="div")

            # hämta raderna
            info_container_divs = info_container.find_elements(
                by=By.TAG_NAME, value="div"
            )

            start_time, end_time, affected_customers, info_text, last_update = self.__ExtractOutageInfo(info_container_divs)

            self.Outages.append(
                self.__CreateOutageDict(
                    municipality, start_time, end_time, info_text, last_update, affected_customers
                )
            )

    def __ExtractOutageInfo(self, info_container_divs):
        start_time = info_container_divs[0].text.split(":")[1].strip(" ")
        end_time = info_container_divs[1].text.split(":")[1].strip(" ")
        affected_customers = info_container_divs[2].text.split(":")[1].strip(" ").split(" ")[0]

        info_text = self.Driver.find_element(
                by=By.CLASS_NAME, value="InterruptInfo_customerInformationText__2hO59"
            ).text

        last_update = self.Driver.find_element(
                by=By.CLASS_NAME, value="InfoBox_lastUpdatedText__1-6ip"
            ).text
        
        logging.debug(f'start_time={start_time} end_time={end_time} affected_customers={affected_customers} info_text={info_text} last_update={last_update}')
        return start_time,end_time,int(affected_customers),info_text,last_update

    def __AcceptCookies(self):
        try:
            accept_btn = self.Driver.find_element(
                    by=By.ID,
                    value="CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll",
                )
            accept_btn.click()

            logging.info("Waiting 1 sec for cookie popup to go away")
            time.sleep(1)
        except NoSuchElementException:
            logging.debug("self.Driver has already accepted cookies")

    def SaveOutagesToFile(self):
        logging.info("Creating a outages dict")
        outagesDict = {"outages": self.Outages}

        logging.info("Converting outages dict to json")
        jsonData = json.dumps(outagesDict, ensure_ascii=False)

        f = open("outdata.json", "wb")

        logging.info("writing outages json data to the file outages.json")
        f.write(jsonData.encode("utf-8"))
        f.close()

    def RunScraper(self, interval: int = 60):
        if interval < 60:
            interval = 60
            logging.warning(
                f"Run interval is less then 60 seconds, setting to {interval}!"
            )

        while True:
            # RESET
            logging.info("Clearing stored data before next run")
            self.CountiesWithOutage = []
            self.MunicipalitiesWithOutage = []
            self.Outages = []

            logging.info("Starting to fetch data from ELLEVIO")
            self.GetCountiesWithOutage()
            self.GetMunicipalitiesWithOutage()
            self.GetOutages()
            self.SaveOutagesToFile()

            logging.info(f"Sleeping for {interval} seconds to not get rate limited")
            time.sleep(interval)


import sys
from datetime import datetime

if __name__ == "__main__":
    now = datetime.now()
    formatted_date = now.strftime('%Y-%m-%d-%H:%M:%S')


    

    logging.basicConfig(
        format="[%(asctime)s] %(levelname)-8s line:%(lineno)-4s %(funcName)-30s  - %(message)s",
        datefmt="%d-%b-%y %H:%M:%S",
        level=logging.INFO,
        filename=f'{formatted_date}.log',
    )

    interval = 60

    if len(sys.argv) > 1:
        interval = int(sys.argv[1])

    es = EllevioScraper()
    es.RunScraper(interval)
