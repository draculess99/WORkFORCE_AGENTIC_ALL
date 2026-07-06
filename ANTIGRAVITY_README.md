# Opening this project in Antigravity

Yes, this project can be opened directly in Antigravity after unzipping.

## Recommended steps

1. Unzip the file.
2. Open Antigravity.
3. Choose **Open Folder**.
4. Select the unzipped `workforce_ai_suite` folder.
5. Open the built-in terminal.
6. Run:

```bash
python app.py
```

The launcher will create a local `.venv`, install the required packages, start Streamlit, and open the browser at:

```text
http://localhost:8501
```

## If Python is not found
Install Python 3.11, then run again:

```bash
python app.py
```

On some Windows installs, use:

```bash
py -3.11 app.py
```

## If package install fails
Try:

```bash
python app.py --reinstall
```

If you are on Python 3.13, install Python 3.11 instead. Some ML/agent packages may not yet have smooth wheels on 3.13.

## Important
This project is intentionally merged into one Streamlit service. Do not split it back into multiple Railway services unless you want separate billing/resources again.
