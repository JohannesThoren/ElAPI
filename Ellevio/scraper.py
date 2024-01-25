import time
import json

from PIL import Image

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException

ROOT_URL = "https://avbrottskarta.ellevio.se/"
COUNTY_URL = "https://avbrottskarta.ellevio.se/län/"
MUNICIPALITY_URL = "https://avbrottskarta.ellevio.se/kommun/"

ff_options = Options()
ff_options.add_argument("--headless")

driver = webdriver.Firefox(options=ff_options)

driver.get(ROOT_URL)

driver.implicitly_wait(3)


# hämta listan med län från ellevios avbrottskarta
county_table_element = driver.find_element(
    by=By.CLASS_NAME, value="InfoBox_locationList__1AKS1"
)
rows = county_table_element.find_elements(by=By.TAG_NAME, value="tr")

# ta bort det förtsta elementet (titel texten)
rows.pop(0)

# spara undan och ta bort totala avbrott från listan
county_rows = rows.pop(len(rows) - 1)

# län med strömavbrott
county_with_outage = []

# loopa igenom alla rader med län
for row in rows:
    cells = row.find_elements(by=By.TAG_NAME, value="td")
    if cells[1].text != "0" or cells[2].text != "0":
        if cells[0].text != "V Götalands län":
            tmp = cells[0].text.split(" ")[0].lower().rstrip("s")
            county_with_outage.append(tmp)
        else:
            county_with_outage.append("västragötaland")

municipality_with_outage = []

# loopa igenom alla län med ett avbrott
for county in county_with_outage:
    driver.get(COUNTY_URL + county + "/idag")

    municipality_table_element = driver.find_element(
        by=By.CLASS_NAME, value="InfoBox_locationList__1AKS1"
    )

    municipality_rows = municipality_table_element.find_elements(
        by=By.TAG_NAME, value="tr"
    )
    municipality_rows.pop(0)
    municipality_rows.pop(len(municipality_rows) - 1)

    for municipality_row in municipality_rows:
        cells = municipality_row.find_elements(by=By.TAG_NAME, value="td")
        if cells[1].text != "0" or cells[2].text != "0":
            municipality_with_outage.append(cells[0].text.lower())

outages = []

for municipality in municipality_with_outage:
    print(
        "[ELLEVIO SCRAPER] fetching data from",
        municipality,
        MUNICIPALITY_URL + municipality + "/idag",
    )
    driver.get(MUNICIPALITY_URL + municipality)
    print("[ELLEVIO SCRAPER] Waiting 1 sec for page to load")
    time.sleep(1)

    # acceptera kakor
    try:
        accept_btn = driver.find_element(
            by=By.ID, value="CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"
        )
        accept_btn.click()
    except NoSuchElementException:
        print("[ELLEVIO SCRAPER] Cookies Already Accepted")

    print("[ELLEVIO SCRAPER] Waiting 1 sec for cookie popup to go away")
    time.sleep(2)

    # ta en skärmdump
    driver.save_screenshot(municipality + ".png")
    driver_window_size = driver.get_window_size()
    x = 370
    y = 40
    w = driver_window_size.get("width") - 100
    h = driver_window_size.get("height") - 200

    im = Image.open(municipality + ".png")
    im = im.crop((x, y, w, h))
    im.save(municipality + ".png")

    info_container = driver.find_element(
        by=By.CLASS_NAME, value="InterruptInfo_timestampsContainer__3f5L_"
    )

    # det finns en nästlad div i diven med klassnamn InterruptInfo_timestampsContainer__3f5L_ som har all data
    info_container = info_container.find_element(by=By.TAG_NAME, value="div")

    # hämta raderna
    info_container_divs = info_container.find_elements(by=By.TAG_NAME, value="div")

    start_time = info_container_divs[0].text.split(":")[1].strip(" ")
    end_time = info_container_divs[1].text.split(":")[1].strip(" ")
    affected_customers = info_container_divs[2].text.split(":")[1].strip(" ")

    info_text = driver.find_element(
        by=By.CLASS_NAME, value="InterruptInfo_customerInformationText__2hO59"
    ).text

    last_update = driver.find_element(
        by=By.CLASS_NAME, value="InfoBox_lastUpdatedText__1-6ip"
    ).text

    outage = {
        "municipality": municipality,
        "start_time": start_time,
        "end_time": end_time,
        "info_text": info_text,
        "last_update": last_update,
    }

    outages.append(outage)


x = {"outages": outages}

json_data = json.dumps(x, ensure_ascii=False)


f = open("outdata.json", "wb")
f.write(json_data.encode("utf-8"))
f.close()

driver.close()
