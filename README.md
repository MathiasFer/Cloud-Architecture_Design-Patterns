# huellamap-lite

`huellamap-lite` es un monorepo minimalista diseñado para demostrar patrones fundamentales de resiliencia y arquitectura cloud distribuida en un entorno completamente simulado, reproducible y libre de dependencias externas.

## Arquitectura del Sistema

```mermaid
flowchart TD
    Client["Cliente / Browser / Curl"] -->|HTTP :80| Nginx["Nginx Reverse Proxy"]
    Lambda["scraper-lambda (AWS Lambda Simulado)"] -->|POST /reports| Nginx

    subgraph Internal_Network ["Red Interna Docker"]
        Nginx -->|Proxy Pass :8000| ReportsAPI["reports-api (FastAPI + SQLite)"]
        ReportsAPI -->|SQLite| DB[(reports.db)]
        ReportsAPI -->|POST /ficha :8001 (Resilience: CB, Retry, Timeout)| FichaIA["ficha-ia (FastAPI Interno)"]
    end

    subgraph AWS_Cloud_Architecture ["Infraestructura Cloud (Terraform)"]
        TGW["AWS Transit Gateway"]
        HubVPC["Hub VPC (10.0.0.0/16)"]
        Spoke1["Spoke VPC 1 (10.1.0.0/16)"]
        Spoke2["Spoke VPC 2 (10.2.0.0/16)"]

        TGW --- HubVPC
        TGW --- Spoke1
        TGW --- Spoke2
    end
```

## Estado de Patrones y Temas de Arquitectura

| # | Tema / Patrón | Estado | Detalle de Implementación |
|---|---------------|--------|---------------------------|
| 1 | **Circuit Breaker** | Implemented and executed | Apertura tras 3 fallos consecutivos, ventana de 15s en OPEN y estado HALF_OPEN de prueba. |
| 2 | **Retry** | Implemented and executed | 3 intentos con retroceso exponencial (`exponential backoff`). |
| 3 | **Timeout** | Implemented and executed | Límite estricto de 2.0s en llamadas HTTP a `ficha-ia`. |
| 4 | **Lambda / Docker** | Implemented, validated, not deployed (Lambda) / Implemented and executed (Docker) | Contenedores orquestados con Compose y función Lambda minimalista en `/scraper-lambda`. |
| 5 | **API Gateway / LB / Reverse Proxy** | Implemented and executed | Reverse Proxy Nginx en puerto 80 que aísla `ficha-ia` de accesos externos. |
| 6 | **Hub-and-Spoke** | Implemented, validated, not deployed | Topología VPC Hub y 2 Spokes conectadas mediante AWS Transit Gateway en `/terraform/hub-spoke`. |
| 7 | **Lift-and-Shift** | Roadmap | Estrategia de migración hacia AWS EC2/ECS preservando configuración local. |
| 8 | **Bastion** | Roadmap | Acceso seguro SSH/SSM a subredes privadas en Spoke VPCs a través de Bastion Host en Hub. |

## Cómo Ejecutar el Proyecto

### 1. Requisitos Previos
- Docker y Docker Compose
- cURL o cliente HTTP

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

## Evidencias de Ejecución

Los resultados y trazas de ejecución se encuentran guardados en el directorio `/evidence`:
- [evidence/01_ok.txt](evidence/01_ok.txt): Despliegue de servicios y creación exitosa de reportes con `CHAOS_MODE=none`.
- [evidence/02_timeout_retry.txt](evidence/02_timeout_retry.txt): Ejecución con `CHAOS_MODE=slow` mostrando logs de `[TIMEOUT]`, `[RETRY n/3]` y activación de `[FALLBACK]`.
- [evidence/03_circuit_breaker.txt](evidence/03_circuit_breaker.txt): Ejecución con `CHAOS_MODE=fail` mostrando transición a `[CIRCUIT OPEN]`, degradación elegante a `[FALLBACK]`, recuperación con `[CIRCUIT HALF_OPEN]` y cierre con `[CIRCUIT CLOSED]`.
- [evidence/04_terraform_validate.txt](evidence/04_terraform_validate.txt): Validación sintáctica y de configuración de la arquitectura Hub-and-Spoke de Terraform.

## Next Steps (Roadmap)

1. **API Gateway + ALB on AWS:**
   - Reemplazar Nginx local por un AWS Application Load Balancer (ALB) público integrado con AWS API Gateway para autenticación y throttling granular.
2. **ECS Fargate:**
   - Empaquetar y desplegar `reports-api` y `ficha-ia` como tareas sin servidor en Amazon Elastic Container Service (ECS Fargate) con políticas de auto-escalado horizontal basadas en CPU y latencia.
3. **Lift-and-Shift:**
   - Diseñar pipelines de migración usando AWS Application Migration Service (MGN) para migrar cargas legacy a instancias EC2 antes de su modernización a contenedores.
4. **Bastion Host / AWS Systems Manager:**
   - Implementar un Bastion Host seguro en la subred pública del Hub VPC con acceso auditado vía AWS Systems Manager Session Manager (sin puertos 22 abiertos a internet).
