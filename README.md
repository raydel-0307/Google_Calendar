# Documentación de la API

Esta API provee tres servicios principales relacionados a la disponibilidad de días y horas, así como la creación de eventos en Google Calendar:

1. **Listado de días disponibles**: Permite obtener una lista de fechas en las que hay disponibilidad.
2. **Listado de horas disponibles**: Dados un día y una zona horaria, lista las horas en las que se puede agendar una cita.
3. **Creación de eventos**: Permite crear un evento en Google Calendar basado en la fecha y hora seleccionadas.

## Requerimientos e Instalación

**Dependencias mínimas:**

- Python 3.11 (o versión compatible)
- [Poetry](https://python-poetry.org/) o `pip` para gestionar dependencias
- [MongoDB](https://www.mongodb.com/) para el almacenamiento de configuraciones y citas
- Variables de entorno para configurar el acceso a Google Calendar (CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, MONGO_URI)

**Instalación:**

1. Clonar el repositorio:
   ```bash
   git clone https://tu-repositorio.git
   cd tu-repositorio
   ```
2. Crear y activar un entorno virtual (opcional pero recomendado):

```bash
python3 -m venv venv
source venv/bin/activate
```
Instalar dependencias
```bash
pip install -r requirements.txt
```


```bash
export CLIENT_ID="tu_client_id"
export CLIENT_SECRET="tu_client_secret"
export REDIRECT_URI="http://localhost:8000/callback"
export MONGO_URI="mongodb://usuario:password@host:puerto/db"
```
Levantar el Proyecto
Con las dependencias instaladas y las variables configuradas:

```bash
uvicorn main:app --reload --port 8000
```
La aplicación correrá por defecto en http://localhost:8000.

Endpoints Principales
Obtener días disponibles
> GET /availability/days?name_company={company_name}&time_zone={tz}

Devuelve una lista de cadenas YYYY-MM-DD con los días habilitados.
Ejemplo:



> GET /availability/days?name_company=ktch&time_zone=America/Bogota
Respuesta:

```json

[
  "2024-12-16",
  "2024-12-17",
  "2024-12-18"
]
```
Obtener horas disponibles para un día
> GET /availability/hours?name_company={company_name}&date_select={YYYY-MM-DD}&time_zone={tz}

Devuelve una lista con objetos que representan las horas disponibles.
Ejemplo:



> GET /availability/hours?name_company=ktch&date_select=2024-12-16&time_zone=America/Bogota
Respuesta:

```json

[
  {
    "id": 1,
    "hora": "08:00:00",
    "horaFormat": "08:00 AM"
  },
  {
    "id": 2,
    "hora": "09:00:00",
    "horaFormat": "09:00 AM"
  }
]
```
Crear un evento
> POST /events?name_company={company_name}

Cuerpo (JSON):

```json

{
  "start_time": "2024-12-16T08:00:00-05:00",
  "assistant_email": "assistant@example.com",
  "usuario": "593962206252",
  "nombre": "Kerly"
}
```
Crea el evento en Google Calendar y devuelve detalles del evento creado.
Ejemplo:

http

> POST /events?name_company=ktch
Content-Type: application/json
```json
{
  "start_time": "2024-12-16T17:00:00-05:00",
  "assistant_email": "bec2.aldeberan@gmail.com",
  "usuario": "593962206252",
  "nombre": "Kerly"
}
```
Respuesta (ejemplo):

```json

{
  "kind": "calendar#event",
  "etag": "\"3468219048810000\"",
  "id": "0qjl1g6417bt2c3ghg29ue24b8",
  "status": "confirmed",
  "htmlLink": "https://www.google.com/calendar/event?eid=MHFqbDFnNjQxN2J0MmMzZ2hnMjl1ZTI0Yjgga2VybHllbGl6MTlAbQ",
  "created": "2024-12-13T17:05:23.000Z",
  "updated": "2024-12-13T17:05:24.405Z",
  "summary": "Pediatra",
  "description": "Evento creado automaticamente\n\nEnlace del evento: https://www.google.com/calendar/event?eid=MHFqbDFnNjQxN2J0MmMzZ2hnMjl1ZTI0Yjgga2VybHllbGl6MTlAbQ",
  "creator": {
    "email": "kerlyeliz19@gmail.com",
    "self": true
  },
  "organizer": {
    "email": "kerlyeliz19@gmail.com",
    "self": true
  },
  "start": {
    "dateTime": "2024-12-16T17:00:00-05:00",
    "timeZone": "America/Caracas"
  },
  "end": {
    "dateTime": "2024-12-16T18:00:00-05:00",
    "timeZone": "America/Caracas"
  },
  "iCalUID": "0qjl1g6417bt2c3ghg29ue24b8@google.com",
  "sequence": 0,
  "attendees": [
    {
      "email": "bec2.aldeberan@gmail.com",
      "responseStatus": "needsAction"
    }
  ],
  "reminders": {
    "useDefault": true
  },
  "eventType": "default"
}
```
### Flujo de Uso
* Llamar a /availability/days para obtener las fechas disponibles.
* Escoger una fecha de esa lista y llamar a /availability/hours para obtener las horas disponibles de ese día.
* Escoger una hora y llamar a /events (POST) con la start_time resultante para crear el evento en el calendario.
De esta forma, el usuario primero ve qué días puede agendar, * luego elige el día y ve qué horas están disponibles, y finalmente crea el evento escogiendo la hora deseada.

En la base de datos se tienes las credenciales correctas, la base de datos configurada y las colecciones con la información necesaria. 