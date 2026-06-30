# GymSystem

Sistema de gestión integral para gimnasios desarrollado con Flask + SQLAlchemy.

## Instalación

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # editar variables
python app.py
```

## Estructura
- `app.py` — punto de entrada
- `config.py` — configuración central
- `database/models/` — modelos SQLAlchemy
- `controllers/` — lógica de controladores
- `services/` — lógica de negocio
- `routes/` — blueprints Flask
- `templates/` — plantillas Jinja2
- `static/` — CSS, JS, imágenes
- `utils/` — herramientas auxiliares

## Zona horaria
Todas las fechas y horas usan **America/Bogota (UTC-5)**.

## Roles
- **Administrador** — acceso total
- **Recepcionista** — clientes, pagos, ventas
- **Entrenador** — consulta clientes y asistencia

## Tests
```bash
pytest tests/
```
