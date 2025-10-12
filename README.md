# MRP_mongoose


## Run the app
1) Make sure you have docker installed
2) Setup a `.env` file with all of your keys and such
3) Build the image with `docker compose build`
4) Run this from the commandline `docker compose run --rm python_app`
5) Look for a line like this in the terminal: `* Running on http://172.18.0.2:5000` and go there to see your cut list

## Run Tests
```bash
python -m pytest --cov=bags --cov-report=term-missing tests/
```

```bash
python -m pytest tests/ -v --cov=. --cov-report=html
$BROWSER htmlcov/index.html
```