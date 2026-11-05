# Laboratorio 1 — GitHub, Docker y API REST

## Integrantes
- Alejandro Hernández Carpio — Carpio360
- Nombre completo — usuario GitHub

## Descripción
API REST sencilla para gestionar notas.

## Tecnologías
- Python 3.12 + FastAPI
- PostgreSQL 16
- Docker y Docker Compose

## Cómo ejecutar
```bash
cp .env.example .env      # cambiar al menos DB_PASSWORD
docker compose up --build
```
La API queda en http://localhost:8000 (documentación interactiva en /docs).
