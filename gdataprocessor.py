import gspread
from google.oauth2.service_account import Credentials
import asyncio

#==logger settings==
import logging
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
# disable DEBUG від google auth
logging.getLogger("google").setLevel(logging.WARNING)

#===================

import gspread
from google.oauth2.service_account import Credentials
from google.auth.exceptions import TransportError
import requests

scopes = ["https://www.googleapis.com/auth/spreadsheets"]

print("[ARDUINO PROJECT] Trying to connect with GoogleAPI...")
try:
    creds = Credentials.from_service_account_file("googleapi/gcp_key.json", scopes=scopes)
    client = gspread.authorize(creds)
    sheet_id = "1gxcOsmZcY2xBEWzQYvl9wngf4XXO80p74RAxIFocits"
    mainSheet = client.open_by_key(sheet_id)
    print('[ARDUINO PROJECT] Connected!')
except (requests.exceptions.ConnectionError, TransportError) as e:
    print("[ARDUINO PROJECT] Connection error while initializing Google Sheets:", e)
    mainSheet = None

async def loadGoogleData(self, rowsToLoad):
    rowsInTable = len(self.mainTable.row_data)
    insertToTop = False
    print('[ARDUINO PROJECT] Rows loaded:', str(rowsInTable))

    if not mainSheet:
        print("[ARDUINO PROJECT] Google Sheet not available.")
        return

    if rowsToLoad == 0:
        rowsToLoad = 5

    try:

        totalRowsInSheet = len(mainSheet.get_worksheet(0).col_values(1))

        if (self.totalRows == 0):
            self.totalRows = totalRowsInSheet

        rowEnd = totalRowsInSheet - rowsToLoad - rowsInTable
        rowStart = totalRowsInSheet - rowsInTable

        if (totalRowsInSheet > self.totalRows):
            rowEnd = self.totalRows
            self.totalRows = totalRowsInSheet
            rowStart = totalRowsInSheet
            insertToTop = True

        print(f'[ARDUINO PROJECT] Rows in Google Sheet: {totalRowsInSheet}')
        print(f'[ARDUINO PROJECT] TotalRows: {self.totalRows}')

        dataToAdd = []
        if (rowEnd < 2):
            rowEnd = 2

        print('[ARDUINO PROJECT] RowStart:', str(rowStart), ' RowEnd:', str(rowEnd))

        for i in range(rowStart, rowEnd, -1):  # bottom to top
            valuesList = mainSheet.get_worksheet(0).get(f"A{i}:F{i}")
            print('[ARDUINO PROJECT] Values from sheet1:', str(valuesList))
            if valuesList:
                dataToAdd.append(valuesList[0])

        print('[ARDUINO PROJECT] Data to add:', str(len(dataToAdd)))

        if len(dataToAdd) > 0:
            for listInside in dataToAdd:

                try:
                    # Clean up non-breaking spaces and commas for float conversion
                    for i in range(2, 6):
                        listInside[i] = listInside[i].replace('\xa0', '').replace(',', '.')

                    # Convert and format values
                    listInside[2] = str(int(float(listInside[2]))) + ' C'
                    listInside[3] = str(int(float(listInside[3]))) + '%'
                    listInside[4] = str(int(float(listInside[4])))

                    try:
                        rain_value = int(float(listInside[5]))

                        if rain_value >= 1000:
                            listInside[5] = 'Опадів немає'
                        elif rain_value > 600:
                            listInside[5] = 'Легкий дощ'
                        elif rain_value > 300:
                            listInside[5] = 'Помірний дощ'
                        else:
                            listInside[5] = 'Сильний дощ'

                    except (IndexError, ValueError) as e:
                        print(f"[ARDUINO PROJECT] Failed to process rain value: {e}")
                        listInside[5] = 'Невідомо'  # fallback label if data missing or corrupted

                except (ValueError, IndexError) as e:
                    print(f"[ERROR] Error processing row {listInside}: {e}")

            if (insertToTop == False):
                # add data to the end of table
                for listInside in dataToAdd:
                    try:
                        self.mainTable.add_row(listInside)
                    except Exception as e:
                        print(f"[ERROR] Error adding row {listInside}: {e}")
            else:
                dataFormatted = []

                # or add before first value
                for listInside in dataToAdd:
                    try:
                        dataFormatted.append(listInside)
                    except Exception as e:
                        print(f"[ARDUINO PROJECT] Error adding row {listInside}: {e}")

                existing_rows = list(self.mainTable.row_data)
                self.mainTable.row_data = []
                # insert to top
                self.mainTable.row_data = dataFormatted + existing_rows


        highestTempData = ['', '', '']
        highestHumData = ['', '', '']
        # highest values
        try:
            highestTempData = mainSheet.get_worksheet(1).get("A3:C3")
            highestHumData = mainSheet.get_worksheet(1).get("E3:G3")

        except (gspread.exceptions.APIError,
                requests.exceptions.RequestException,
                TransportError,
                AttributeError,
                Exception) as e:
            print("[ARDUINO PROJECT] Failed to fetch highest temperature or humidity data:", str(e))

        # print("[ARDUINO PROJECT] Raw Temp: ", str(highestTempData),
        #      '\n[ARDUINO PROJECT] Raw Humidity: ', str(highestHumData))

        highestTempData = highestTempData[0]
        highestHumData = highestHumData[0]

        # process highest value
        try:
            highestTempData[0] = str(int(float(highestTempData[0].replace(',', '.')))) + ' C'
            highestHumData[0] = str(int(float(highestHumData[0].replace(',', '.')))) + '%'
        except (ValueError, IndexError) as e:
            print(f"Error processing data: {e}")

        self.rootWidget.ids.high_temp_value.text = highestTempData[0]
        self.rootWidget.ids.high_temp_time.text = highestTempData[1]
        self.rootWidget.ids.high_temp_date.text = highestTempData[2]

        self.rootWidget.ids.high_hum_value.text = highestHumData[0]
        self.rootWidget.ids.high_hum_time.text = highestHumData[1]
        self.rootWidget.ids.high_hum_date.text = highestHumData[2]

        # print("[ARDUINO PROJECT] Highest Temp: ", str(highestTempData),
        #       '\n[ARDUINO PROJECT] Highest Humidity: ', str(highestHumData))

        try:
            self.loadMoreIsPressed = False
            self.tableSpinner.opacity = 0
        except AttributeError as e:
            print("[ARDUINO PROJECT] UI component missing or not initialized:", e)
        except Exception as e:
            print("[ARDUINO PROJECT] Unexpected error while updating UI state:", e)


    except (requests.exceptions.RequestException, TransportError) as e:
        print("[ARDUINO PROJECT] Failed to load data from Google Sheets:", e)

        self.loadMoreIsPressed = False
        self.tableSpinner.opacity = 0


