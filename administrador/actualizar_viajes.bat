@echo off
cd /d C:\Users\alejo\PycharmProjects\2doProyectoHectorAlejo\administrador

::  Verifica carpeta logs
if not exist logs (
    mkdir logs
    echo [%date% %time%] Carpeta 'logs' creada automáticamente. >> logs\cron_log.txt
)

::  Ejecuta el comando con entorno virtual externo
C:\Users\alejo\PycharmProjects\2doProyectoHectorAlejo\.venv\Scripts\python.exe manage.py actualizar_viajes >> logs\cron_log.txt 2>&1

echo [%date% %time%] Script ejecutado. >> logs\cron_log.txt

