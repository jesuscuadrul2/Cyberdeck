Cyberdeck: Servidor Táctico de Taller y Nodo IoT
Arquitectura 24/7 | Edge Computing | Zero-Trust Networking | Automatización Bash


Visión General
El Cyberdeck es el cerebro central de mi ecosistema de hardware. Diseñado desde cero como una solución de infraestructura local continua (operando 24/7 desde abril de 2026), este servidor portátil orquesta la domótica del taller, aloja servicios de gestión de datos, y actúa como puente seguro hacia el exterior sin comprometer la privacidad. Es un sistema altamente replicable gracias a sus rutinas de respaldo automatizadas en la nube.


Diseño de Hardware, Manufactura y Almacenamiento
La carcasa no es comercial; fue diseñada paramétricamente en Fusion 360 para cumplir con tolerancias térmicas estrictas y portabilidad.


Core Computacional: Raspberry Pi 5 (8GB RAM).


Autonomía Energética: Integración de módulo UPS Geekworm X1202, garantizando más de 2 horas de autonomía bajo cargas intensivas para evitar corrupción de bases de datos ante cortes eléctricos.


Arquitectura de Almacenamiento Desacoplada: Para evitar la fragmentación y el desgaste por ciclos de escritura (wear-leveling), el Sistema Operativo reside en una MicroSD, mientras que el motor Docker, las bases de datos (MariaDB/Postgres) y los modelos de lenguaje (LLMs) operan desde un SSD de 2.5" externo.


Manufactura Aditiva: Chasis fabricado combinando PETG translúcido para la rigidez estructural y TPU para la amortiguación de impactos, optimizado para el ecosistema Bambu Lab.


Orquestación de Software y Scripts Nativos
Maximizar el silicio en hardware de bajo consumo requiere estrategias de optimización de grado industrial. El sistema gestiona simultáneamente más de 30 contenedores (incluyendo Home Assistant, Nextcloud, LobeChat, Pi-hole y un ERP completo para impresión 3D llamado Pragmata).


Network & Docker Maestro (Bash): Desarrollé un demonio en Bash que lee el estado físico del hardware (/sys/class/net/eth0/carrier). Si detecta conexión RJ45 local, asigna IPs estáticas vía nmcli, levanta toda la flota de contenedores y monta unidades criptográficas (Rclone). Si detecta un estado "nómada" (solo WiFi o desconectado), cambia a DHCP e hiberna los contenedores no críticos para ahorrar batería de la UPS.


Activación por Red (Socket Activation): Los servicios inactivos se suspenden y solo se levantan mediante disparadores de red cuando hay una petición entrante, reduciendo drásticamente el overhead en la memoria RAM.


Backups Automatizados (CI/CD Local): Scripts nocturnos rastrean cambios en las configuraciones críticas y realizan git push silenciosos a repositorios privados, asegurando que la infraestructura sea 100% replicable en caso de falla catastrófica.


Ciberseguridad y Redes Zero-Trust
La seguridad perimetral es estricta para proteger desde bóvedas de credenciales hasta la telemetría del robot "Robert".

Conectividad sin Port-Forwarding: Implementación de Tailscale y VPNs privadas. El servidor es accesible globalmente, pero invisible para escaneos de puertos públicos.

Almacenamiento Criptográfico al Vuelo: Sincronización de contenido a la nube con encriptación en tiempo real, previniendo análisis automatizados y bloqueos por parte de proveedores externos.
