# ⚡ Cyberdeck: Servidor Edge 24/7 y Orquestador IoT Táctico

![Raspberry Pi](https://img.shields.io/badge/-Raspberry_Pi_5-C51A4A?style=for-the-badge&logo=Raspberry-Pi&logoColor=white)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)
![Bash](https://img.shields.io/badge/bash-%234EAA25.svg?style=for-the-badge&logo=gnu-bash&logoColor=white)
![Tailscale](https://img.shields.io/badge/Tailscale-ff5f5f?style=for-the-badge&logo=tailscale&logoColor=white)
![Home Assistant](https://img.shields.io/badge/home%20assistant-%2341BDF5.svg?style=for-the-badge&logo=home-assistant&logoColor=white)

El **Cyberdeck** es el cerebro central e infraestructura Edge de mi ecosistema de hardware. Diseñado y ensamblado desde cero como una solución de cómputo continuo local (operando ininterrumpidamente 24/7 desde abril de 2026), este servidor portátil orquesta la domótica del taller, gestiona bases de datos masivas, aloja modelos de lenguaje (LLMs) locales y actúa como una pasarela segura Zero-Trust sin comprometer la privacidad.

## 🚀 Visión General de la Infraestructura

Para maximizar el silicio en un hardware de bajo consumo, el sistema implementa estrategias de optimización de grado industrial, permitiendo la ejecución simultánea de **más de 30 contenedores Docker** (incluyendo Home Assistant, Nextcloud, LobeChat, Pi-hole y *Pragmata*, un ERP completo para manufactura aditiva).

## 🛠️ Especificaciones de Hardware y Manufactura

El chasis del dispositivo no es comercial; fue diseñado paramétricamente desde cero para cumplir con tolerancias térmicas estrictas, portabilidad y resistencia en entornos de taller.

* **🧠 Core Computacional:** Raspberry Pi 5 (8GB RAM).
* **🔋 Autonomía Energética:** Integración de un módulo UPS Geekworm X1202, garantizando más de **2 horas de autonomía** bajo uso intensivo para mitigar picos de tensión y prevenir la corrupción de datos.
* **💽 Almacenamiento Desacoplado (Wear-Leveling):** * *Sistema Operativo:* MicroSD de alta velocidad para lectura.
    * *Datos e Ingesta:* SSD externo de 2.5" dedicado exclusivamente al motor Docker, bases de datos (MariaDB/Postgres) y modelos de IA, previniendo la degradación del almacenamiento por ciclos intensivos de escritura.
* **📐 Manufactura Aditiva:** Chasis híbrido impreso en 3D optimizado para el ecosistema Bambu Lab, combinando **PETG translúcido** para la rigidez estructural y disipación térmica, junto con **TPU** para la absorción de impactos mecánicos.

## ⚙️ Automatización y Orquestación Nativa (DevOps Local)

### 🛰️ Script Network-Daemon (Bash Core)
Desarrollé un demonio en Bash corriendo en segundo plano que monitoriza el estado físico de la red a bajo nivel mediante `/sys/class/net/eth0/carrier`:
* **Modo Estacionario (RJ45 Detectado):** Configura IPs estáticas mediante `nmcli`, levanta la flota completa de microservicios y monta unidades criptográficas remotas vía `Rclone`.
* **Modo Nómada (Solo Wi-Fi o Desconectado):** Conmuta automáticamente a DHCP e ingresa en un modo de ahorro energético, hibernando contenedores no críticos para extender la autonomía de la UPS.

### 🔌 Activación por Red (Socket Activation)
Para mitigar el *overhead* de la memoria RAM, los servicios de menor concurrencia permanecen suspendidos en el *kernel* y se inicializan bajo demanda únicamente cuando se detecta un *trigger* o petición entrante en sus puertos asignados.

### 🔄 Respaldo Automatizado e Infraestructura como Código (IaC)
Rutinas nocturnas automatizadas (*cron jobs*) rastrean cambios en los archivos de configuración de Docker, entornos virtuales y configuraciones críticas de red, ejecutando *commits* y `git push` silenciosos a repositorios privados para garantizar que el servidor sea 100% replicable ante un fallo catastrófico de hardware.

## 🔐 Ciberseguridad y Redes Zero-Trust

El perímetro digital está fortificado para proteger desde bóvedas de credenciales locales hasta la telemetría del ecosistema robótico:

* **🌐 Acceso Global Seguro:** Implementación de mallas VPN privadas mediante **Tailscale**. El servidor es accesible de forma segura desde cualquier parte del mundo sin necesidad de realizar apertura de puertos (*Port-Forwarding*), volviéndolo invisible ante escaneos de puertos públicos en la WAN.
* **🔑 Criptografía al Vuelo:** Sincronización continua hacia la nube de volúmenes de datos sensibles mediante encriptación en tiempo real en el cliente, previniendo el análisis automatizado o bloqueo de archivos por proveedores externos de almacenamiento.


