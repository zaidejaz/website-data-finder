# Setup Environment variables
Inside `.env` file add this variable value. You Google Sheet's id.

```bash
SHEET_ID="Your sheet id"
```

# Run the scraper
This scraper requires python3.10 or greater version to work perfectly. Run all these commands to start your scraper
```bash
pip install poetry
```

```bash
poetry init -y
```

```bash
poetry install
```

```bash
poetry shell
```

```bash
python main.py
```

Now your scraper is running.