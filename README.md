# Google Sheets exporter

[Instructions on finding sheet ID](https://developers.google.com/sheets/api/guides/concepts#sheet_id)

```
python3 -m pip install -r requirements.txt

gardnr add driver google-sheets google_sheets.driver:GoogleSheets -c sheet_id=<sheet ID>
```

**NOTE**
To use this driver, you must place a `credentials.json` file in the same directory as `driver.py`. See the [API client docs](https://developers.google.com/sheets/api/quickstart/python) for how to create a `credentials.json` file. Next, you need to execute the driver manually (ex. `$ gardnr read -i google-sheets`) and follow the instructions to authorize GARDNR.
