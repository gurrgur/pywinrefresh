from pathlib import Path
import json
import subprocess
import logging
from io import StringIO
import re
import urllib

import pandas as pd
from bs4 import BeautifulSoup
import requests


def query(query):
    url = f"https://www.catalog.update.microsoft.com/Search.aspx?q={urllib.parse.quote(query)}"
    soup = BeautifulSoup(requests.get(url).content, 'html.parser')
    table = soup.find(id="ctl00_catalogBody_updateMatches")
    parse_result = pd.read_html(StringIO(str(table)))
    if not parse_result:
        raise RuntimeError("Failed parsing Windows Update Catalog")
    else:
        df = parse_result[0]

    rows = table.find_all('tr')
    header_row = ["guid"] + [ele.text.strip() for ele in rows[0].find_all('th')]
    data = []
    for row in rows[1:]:
        update_id = row.get("id").split("_", maxsplit=1)[0]
        data.append([update_id] + [ele.text.strip() for ele in row.find_all('td')])
        
    df = pd.DataFrame(columns=header_row, data=data)
    if not df.empty:
        latest_update = df.iloc[0]
        logging.info(f"    result: {latest_update.Title}")
        return latest_update
    else:
        raise RuntimeError(f"Empty result for query \"{query}\".")


def get_download_urls(guid):
    url = "https://www.catalog.update.microsoft.com/DownloadDialog.aspx"
    post_data = {
        "size": 0,
        "updateID": guid,
        "uidInfo": guid
    }
    body = {"updateIDs": json.dumps([post_data])}
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(url, data=body, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Request failed with status code {response.status_code}")
    content = response.text.replace("www.download.windowsupdate", "download.windowsupdate")
    
    pattern = re.compile(r'https://catalog\.s\.download\.windowsupdate\.com[^\s\'"]+')
    urls = pattern.findall(content)
    return urls


def extract_filtered(iso, destination, filt):
    res = subprocess.run(f"7z l {iso} -o{destination} {filt}", capture_output=True)
    # print(res.stdout)
    files = []
    for l in res.stdout.rsplit(b"\r\n\r\n", maxsplit=1)[-1].splitlines()[2:-2]:
        file_path = Path(destination) / l.decode().rsplit(" ", maxsplit=1)[-1]
        files.append(file_path)
        print(file_path)
    subprocess.run(f"7z x {iso}  -o{destination} -aoa {filt}", capture_output=True)
    return files