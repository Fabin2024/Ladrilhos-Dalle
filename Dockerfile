FROM python:3.12-slim

# Variáveis de ambiente úteis para o Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Adiciona o ambiente virtual no PATH para não precisar chamar `uv run` dentro do container
ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Instalar o gerenciador uv via pip
RUN pip install --no-cache-dir uv

# Copiar arquivos de dependências primeiro (aproveita cache do Docker)
COPY pyproject.toml uv.lock ./

# Criar ambiente virtual e instalar dependências do projeto
RUN uv venv && uv sync

# Copiar todo o resto do projeto para o container
COPY . .

# Entrar na pasta onde fica o manage.py
WORKDIR /app/CRM

# Expor a porta 8000
EXPOSE 8000

# Comando padrão que roda as migrations e depois sobe o servidor
CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
