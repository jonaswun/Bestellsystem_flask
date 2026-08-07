FROM python:3.12-slim

WORKDIR /flask_app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev --python 3.12

COPY . .

CMD ["uv", "run", "main.py"]