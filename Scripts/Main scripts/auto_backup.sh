'''#!/bin/bash
# Robot de Respaldo Nocturno

cd /home/jc2/cyberdeck

# Agrega los cambios
git add .

# Crea el paquete con la fecha y hora exacta
git commit -m "Auto-backup: $(date +'%Y-%m-%d %H:%M:%S')"

# Lo sube a la nube silenciosamente
git push origin main
