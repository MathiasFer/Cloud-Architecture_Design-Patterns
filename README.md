# huellamap-lite

`huellamap-lite` es un monorepo diseñado para demostrar patrones fundamentales de resiliencia y arquitectura cloud distribuida en un entorno completamente reproducible, con código ejecutable y configuraciones mínimas en todos sus componentes.

## Arquitectura del Sistema

```mermaid
flowchart TD
    Client["Cliente / Browser / Curl"] -->|HTTP :80| Nginx["Nginx Reverse Proxy / ALB"]
    Lambda["scraper-lambda (AWS Lambda)"] -->|POST /reports| Nginx

    subgraph Internal_Network ["Red Interna Docker / AWS ECS Fargate"]
        Nginx -->|Proxy Pass :8000| ReportsAPI["reports-api (FastAPI + SQLite)"]
        ReportsAPI -->|SQLite| DB[(reports.db)]
        ReportsAPI -->|POST /ficha :8001 (Resilience: CB, Retry, Timeout)| FichaIA["ficha-ia (FastAPI Interno)"]
    end

    subgraph AWS_Cloud_Architecture ["Infraestructura Cloud (Terraform)"]
        TGW["AWS Transit Gateway"]
        HubVPC["Hub VPC (10.0.0.0/16)"]
        Bastion["Bastion Host (SSM)"] --- HubVPC
        Spoke1["Spoke VPC 1 (10.1.0.0/16)"]
        Spoke2["Spoke VPC 2 (10.2.0.0/16)"]
        ECSTasks["ECS Fargate Tasks"] --- Spoke1
        MigratedServer["Lift-and-Shift EC2 Target"] --- Spoke1

        TGW --- HubVPC
        TGW --- Spoke1
        TGW --- Spoke2
    end

    subgraph OnPremise_Environment ["Entorno On-Premises (Simulado)"]
        LegacyApp["onprem-server.py (Legacy DB)"] -->|AWS MGN Replication / migrate_sync.py| MigratedServer
    end
```

## Estado de Patrones y Temas de Arquitectura (Código Mínimo Implementado)

| # | Tema / Patrón | Estado | Ubicación en el Código | Detalle de Implementación |
|---|---------------|--------|------------------------|---------------------------|
| 1 | **Circuit Breaker** | Implemented and executed | [reports-api/main.py](reports-api/main.py) | Apertura tras 3 fallos consecutivos, ventana de 15s en `OPEN` y prueba en `HALF_OPEN`. Consulta en `/breaker`. |
| 2 | **Retry** | Implemented and executed | [reports-api/main.py](reports-api/main.py) | 3 intentos con retroceso exponencial (`exponential backoff` con cálculo `0.5 * 2^(attempt-1)`). |
| 3 | **Timeout** | Implemented and executed | [reports-api/main.py](reports-api/main.py) | Límite estricto de 2.0s en llamadas HTTP a `ficha-ia` gestionado mediante `httpx.Client(timeout=2.0)`. |
| 4 | **Serverless (Lambda) & Docker / ECS** | Implemented and executed (Docker, Lambda, ECS) | [scraper-lambda/handler.py](scraper-lambda/handler.py)<br>[docker-compose.yml](docker-compose.yml)<br>[terraform/ecs/main.tf](terraform/ecs/main.tf) | AWS Lambda para ingesta automatizada, Docker Compose multicontenedor y definición de AWS ECS Fargate Cluster/Service/Task. |
| 5 | **API Gateway, Load Balancer & Reverse Proxy** | Implemented and executed | [nginx/nginx.conf](nginx/nginx.conf)<br>[terraform/api-alb/main.tf](terraform/api-alb/main.tf) | Nginx en puerto 80 aislando servicios internos, y Terraform para AWS API Gateway HTTP API v2 + Application Load Balancer (ALB). |
| 6 | **Hub-and-Spoke Architecture** | Implemented and validated | [terraform/hub-spoke/main.tf](terraform/hub-spoke/main.tf) | Hub VPC y dos Spoke VPCs interconectadas mediante AWS Transit Gateway con VPC Attachments y tablas de enrutamiento. |
| 7 | **Lift-and-Shift Migration Strategy** | Implemented and executed | [migration/lift-and-shift/](migration/lift-and-shift/) | Servidor on-premise legado ([onprem-server.py](migration/lift-and-shift/onprem-server.py)), script de replicación bloque a bloque tipo AWS MGN ([migrate_sync.py](migration/lift-and-shift/migrate_sync.py)) e infraestructura EC2 target ([main.tf](migration/lift-and-shift/main.tf)). |
| 8 | **Bastion Host** | Implemented and validated | [terraform/bastion/main.tf](terraform/bastion/main.tf) | Instancia EC2 Bastion en subred pública del Hub VPC con IAM Role para AWS Systems Manager (SSM Session Manager) y acceso SSH restringido. |

## Cómo Ejecutar el Proyecto

### 1. Requisitos Previos
- Docker y Docker Compose
- cURL o cliente HTTP
- Python 3.10+ (opcional para scripts de simulación y migración)

### 2. Despliegue con Docker Compose
```bash
docker compose up -d --build
```

### 3. Pruebas de Resiliencia y Comandos de Verificación
- **Creación de reportes normales:**
  ```bash
  curl -X POST http://localhost/reports \
    -H "Content-Type: application/json" \
    -d '{"title": "Mascota 1", "description": "Perro encontrado"}'
  ```
- **Consultar estado del Circuit Breaker:**
  ```bash
  curl http://localhost/breaker
  ```
- **Simular latencia (Timeout & Retry):**
  Editar `CHAOS_MODE=slow` en el servicio `ficha-ia` de `docker-compose.yml` y reiniciar.
- **Simular caída del servicio (Circuit Breaker & Fallback):**
  Editar `CHAOS_MODE=fail` en `ficha-ia` y enviar 3 o más reportes consecutivos.
- **Simular migración Lift-and-Shift:**
  ```bash
  python migration/lift-and-shift/migrate_sync.py
  ```

## Evidencias de Ejecución

Los resultados y trazas de ejecución se encuentran guardados en el directorio `/evidence`:
- [evidence/01_ok.txt](evidence/01_ok.txt): Despliegue de servicios y creación exitosa de reportes con `CHAOS_MODE=none`.
- [evidence/02_timeout_retry.txt](evidence/02_timeout_retry.txt): Ejecución con `CHAOS_MODE=slow` mostrando logs de `[TIMEOUT]`, `[RETRY n/3]` y activación de `[FALLBACK]`.
- [evidence/03_circuit_breaker.txt](evidence/03_circuit_breaker.txt): Ejecución con `CHAOS_MODE=fail` mostrando transición a `[CIRCUIT OPEN]`, degradación elegante a `[FALLBACK]`, recuperación con `[CIRCUIT HALF_OPEN]` y cierre con `[CIRCUIT CLOSED]`.
- [evidence/04_terraform_validate.txt](evidence/04_terraform_validate.txt): Validación sintáctica y de configuración de la arquitectura Hub-and-Spoke de Terraform.

## Next Steps (Roadmap)

1. **Despliegue Multi-Región Activo-Activo:**
   - Expandir el Transit Gateway con interconexión inter-región (TGW Peering) y Route 53 con enrutamiento por latencia o failover.
2. **Observabilidad Distribuida:**
   - Integrar AWS X-Ray y OpenTelemetry en `reports-api` y `ficha-ia` para trazar el ciclo de vida completo de las peticiones a través de API Gateway, ALB y contenedores.
3. **Automatización de Cutover con AWS MGN:**
   - Automatizar el lanzamiento de instancias de prueba y cutover final usando la API de AWS Application Migration Service dentro de pipelines CI/CD.
