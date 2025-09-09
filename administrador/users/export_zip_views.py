import csv
import os
import zipfile
from io import BytesIO, StringIO

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from users.models import Viaje, EmpresaProfile, EmpleadoProfile, Gasto


class ExportViajesGastosZipView(APIView):
    """Exporta viajes con gastos y archivos comprobantes en formato ZIP"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        # Determinar qué viajes puede ver según el rol
        if user.role == "MASTER":
            viajes = Viaje.objects.exclude(estado="CANCELADO").select_related(
                'empresa', 'empleado'
            ).prefetch_related('dias__gastos')
            filename = "todos_los_viajes_completos.zip"
            
        elif user.role == "EMPRESA":
            try:
                empresa = EmpresaProfile.objects.get(user=user)
                viajes = Viaje.objects.filter(
                    empresa=empresa
                ).exclude(estado="CANCELADO").select_related(
                    'empleado'
                ).prefetch_related('dias__gastos')
                filename = f"{empresa.nombre_empresa}_viajes_completos.zip"
            except EmpresaProfile.DoesNotExist:
                return HttpResponse("No tienes perfil de empresa asociado", status=403)
                
        elif user.role == "EMPLEADO":
            try:
                empleado = EmpleadoProfile.objects.get(user=user)
                viajes = Viaje.objects.filter(
                    empleado=empleado
                ).exclude(estado="CANCELADO").prefetch_related('dias__gastos')
                filename = f"{empleado.nombre}_{empleado.apellido}_viajes_completos.zip"
            except EmpleadoProfile.DoesNotExist:
                return HttpResponse("No tienes perfil de empleado asociado", status=403)
        else:
            return HttpResponse("No autorizado", status=403)

        # Crear ZIP en memoria
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Crear CSV con la información
            csv_buffer = StringIO()
            writer = csv.writer(csv_buffer, delimiter=';')
            
            # Headers del CSV
            writer.writerow([
                'Empresa', 'Empleado', 'DNI', 'Destino', 'País', 'Ciudad', 
                'Fecha Inicio', 'Fecha Fin', 'Estado Viaje', 'Días Totales', 
                'Días Exentos', 'Días No Exentos', 'Concepto Gasto', 'Monto', 
                'Fecha Gasto', 'Estado Gasto', 'Archivo Comprobante'
            ])
            
            # Procesar cada viaje
            archivos_agregados = set()  # Para evitar duplicados
            
            print(f"DEBUG: Procesando {viajes.count()} viajes para usuario {user.role}")
            
            for viaje in viajes:
                print(f"DEBUG: Procesando viaje {viaje.id} - {viaje.destino}")
                
                dias_totales = viaje.dias_viajados or ((viaje.fecha_fin - viaje.fecha_inicio).days + 1)
                dias = viaje.dias.all()
                dias_exentos = dias.filter(exento=True).count()
                dias_no_exentos = dias.filter(exento=False).count()
                
                gastos = Gasto.objects.filter(viaje=viaje)
                print(f"DEBUG: Viaje {viaje.id} tiene {gastos.count()} gastos")
                
                # Crear estructura de carpetas según el rol
                if user.role == "EMPLEADO":
                    # Para empleado: estructura simple Viaje_ID_Destino/
                    viaje_folder = f"Viaje_{viaje.id}_{self._safe_filename(viaje.destino)}"
                    base_path = f"{viaje_folder}/"
                else:
                    # Para empresa/master: estructura completa
                    empresa_folder = self._safe_filename(viaje.empresa.nombre_empresa)
                    empleado_folder = self._safe_filename(f"{viaje.empleado.nombre}_{viaje.empleado.apellido}")
                    viaje_folder = f"Viaje_{viaje.id}_{self._safe_filename(viaje.destino)}"
                    base_path = f"{empresa_folder}/{empleado_folder}/{viaje_folder}/"
                
                if gastos.exists():
                    for gasto in gastos:
                        print(f"DEBUG: Procesando gasto {gasto.id} - {gasto.concepto}")
                        archivo_nombre = "Sin_comprobante"
                        
                        # Si tiene comprobante, agregarlo al ZIP
                        if gasto.comprobante:
                            print(f"DEBUG: Gasto {gasto.id} tiene comprobante: {gasto.comprobante.name}")
                            try:
                                # Verificar que el archivo existe
                                if gasto.comprobante.storage.exists(gasto.comprobante.name):
                                    # Obtener extensión del archivo
                                    archivo_original = os.path.basename(gasto.comprobante.name)
                                    extension = os.path.splitext(archivo_original)[1]
                                    archivo_nombre = f"Gasto_{gasto.id}_{self._safe_filename(gasto.concepto[:30])}{extension}"
                                    archivo_path = base_path + archivo_nombre
                                    
                                    print(f"DEBUG: Agregando archivo al ZIP: {archivo_path}")
                                    
                                    # Evitar duplicados
                                    if archivo_path not in archivos_agregados:
                                        # Leer el archivo completo
                                        with gasto.comprobante.open('rb') as f:
                                            archivo_contenido = f.read()
                                        
                                        print(f"DEBUG: Archivo leído, tamaño: {len(archivo_contenido)} bytes")
                                        
                                        # Agregar al ZIP
                                        zip_file.writestr(archivo_path, archivo_contenido)
                                        archivos_agregados.add(archivo_path)
                                        print(f"DEBUG: Archivo agregado exitosamente al ZIP")
                                else:
                                    print(f"DEBUG: Archivo no existe en storage: {gasto.comprobante.name}")
                                    archivo_nombre = f"Archivo_no_encontrado_gasto_{gasto.id}"
                                    
                            except Exception as e:
                                print(f"ERROR: procesando archivo del gasto {gasto.id}: {str(e)}")
                                archivo_nombre = f"Error_archivo_gasto_{gasto.id}"
                        else:
                            print(f"DEBUG: Gasto {gasto.id} NO tiene comprobante")
                        
                        # Escribir fila en CSV
                        writer.writerow([
                            viaje.empresa.nombre_empresa,
                            f"{viaje.empleado.nombre} {viaje.empleado.apellido}",
                            viaje.empleado.dni,
                            viaje.destino,
                            viaje.pais or '',
                            viaje.ciudad or '',
                            viaje.fecha_inicio.strftime('%Y-%m-%d'),
                            viaje.fecha_fin.strftime('%Y-%m-%d'),
                            viaje.estado,
                            dias_totales,
                            dias_exentos,
                            dias_no_exentos,
                            gasto.concepto,
                            f"{gasto.monto:.2f}",
                            gasto.fecha_gasto.strftime('%Y-%m-%d') if gasto.fecha_gasto else '',
                            gasto.estado,
                            archivo_nombre
                        ])
                else:
                    print(f"DEBUG: Viaje {viaje.id} no tiene gastos - creando directorio vacío")
                    # Si no hay gastos, crear directorio vacío y agregar información del viaje
                    # Crear un archivo placeholder en el directorio para asegurar que se cree
                    placeholder_path = base_path + "Sin_gastos_registrados.txt"
                    zip_file.writestr(placeholder_path, "Este viaje no tiene gastos registrados.")
                    
                    writer.writerow([
                        viaje.empresa.nombre_empresa,
                        f"{viaje.empleado.nombre} {viaje.empleado.apellido}",
                        viaje.empleado.dni,
                        viaje.destino,
                        viaje.pais or '',
                        viaje.ciudad or '',
                        viaje.fecha_inicio.strftime('%Y-%m-%d'),
                        viaje.fecha_fin.strftime('%Y-%m-%d'),
                        viaje.estado,
                        dias_totales,
                        dias_exentos,
                        dias_no_exentos,
                        'Sin gastos registrados',
                        '0.00',
                        '',
                        'N/A',
                        'Sin_comprobante'
                    ])
            
            # Agregar CSV al ZIP con BOM para mejor compatibilidad con Excel
            csv_content = '\ufeff' + csv_buffer.getvalue()  # BOM para UTF-8
            zip_file.writestr('resumen_viajes_gastos.csv', csv_content.encode('utf-8'))
        
        # Preparar respuesta
        zip_buffer.seek(0)
        response = HttpResponse(zip_buffer.read(), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
    
    def _safe_filename(self, filename):
        """Convierte un string en un nombre de archivo/carpeta seguro"""
        import re
        # Eliminar caracteres no válidos para nombres de archivo
        safe = re.sub(r'[<>:"/\\|?*]', '_', str(filename))
        # Eliminar espacios múltiples y reemplazar por guión bajo
        safe = re.sub(r'\s+', '_', safe)
        # Truncar si es muy largo
        return safe[:50]


class ExportEmpleadoIndividualZipView(APIView):
    """Exporta los viajes con gastos y archivos de un empleado específico en ZIP"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, empleado_id):
        user = request.user
        empleado = get_object_or_404(EmpleadoProfile, id=empleado_id)
        
        # Validar permisos
        if user.role == 'EMPLEADO':
            if empleado.user != user:
                return HttpResponse("No autorizado", status=403)
        elif user.role == 'EMPRESA':
            try:
                empresa = EmpresaProfile.objects.get(user=user)
                if empleado.empresa != empresa:
                    return HttpResponse("No autorizado", status=403)
            except EmpresaProfile.DoesNotExist:
                return HttpResponse("No tienes perfil de empresa asociado", status=403)
        # MASTER puede ver cualquier empleado
        
        # Obtener viajes del empleado
        viajes = Viaje.objects.filter(
            empleado=empleado
        ).exclude(estado="CANCELADO").prefetch_related('dias__gastos')
        
        filename = f"{empleado.nombre}_{empleado.apellido}_viajes_detallados.zip"
        
        # Crear ZIP en memoria
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            csv_buffer = StringIO()
            writer = csv.writer(csv_buffer, delimiter=';')
            
            writer.writerow([
                'Empresa', 'Empleado', 'DNI', 'Destino', 'País', 'Ciudad',
                'Fecha Inicio', 'Fecha Fin', 'Estado Viaje', 'Días Totales',
                'Días Exentos', 'Días No Exentos', 'Concepto Gasto', 'Monto',
                'Fecha Gasto', 'Estado Gasto', 'Archivo Comprobante'
            ])
            
            archivos_agregados = set()
            
            for viaje in viajes:
                dias_totales = viaje.dias_viajados or ((viaje.fecha_fin - viaje.fecha_inicio).days + 1)
                dias = viaje.dias.all()
                dias_exentos = dias.filter(exento=True).count()
                dias_no_exentos = dias.filter(exento=False).count()
                
                gastos = Gasto.objects.filter(viaje=viaje)
                viaje_folder = f"Viaje_{viaje.id}_{self._safe_filename(viaje.destino)}"
                
                if gastos.exists():
                    for gasto in gastos:
                        archivo_nombre = "Sin_comprobante"
                        
                        if gasto.comprobante:
                            try:
                                # Verificar que el archivo existe
                                if gasto.comprobante.storage.exists(gasto.comprobante.name):
                                    archivo_original = os.path.basename(gasto.comprobante.name)
                                    extension = os.path.splitext(archivo_original)[1]
                                    archivo_nombre = f"Gasto_{gasto.id}_{self._safe_filename(gasto.concepto[:30])}{extension}"
                                    archivo_path = f"{viaje_folder}/{archivo_nombre}"
                                    
                                    if archivo_path not in archivos_agregados:
                                        # Leer el archivo completo
                                        with gasto.comprobante.open('rb') as f:
                                            archivo_contenido = f.read()
                                        
                                        # Agregar al ZIP
                                        zip_file.writestr(archivo_path, archivo_contenido)
                                        archivos_agregados.add(archivo_path)
                                else:
                                    archivo_nombre = f"Archivo_no_encontrado_gasto_{gasto.id}"
                            except Exception as e:
                                print(f"Error procesando archivo del gasto {gasto.id}: {str(e)}")
                                archivo_nombre = f"Error_archivo_gasto_{gasto.id}"
                        
                        writer.writerow([
                            viaje.empresa.nombre_empresa,
                            f"{viaje.empleado.nombre} {viaje.empleado.apellido}",
                            viaje.empleado.dni,
                            viaje.destino,
                            viaje.pais or '',
                            viaje.ciudad or '',
                            viaje.fecha_inicio.strftime('%Y-%m-%d'),
                            viaje.fecha_fin.strftime('%Y-%m-%d'),
                            viaje.estado,
                            dias_totales,
                            dias_exentos,
                            dias_no_exentos,
                            gasto.concepto,
                            f"{gasto.monto:.2f}",
                            gasto.fecha_gasto.strftime('%Y-%m-%d') if gasto.fecha_gasto else '',
                            gasto.estado,
                            archivo_nombre
                        ])
                else:
                    writer.writerow([
                        viaje.empresa.nombre_empresa,
                        f"{viaje.empleado.nombre} {viaje.empleado.apellido}",
                        viaje.empleado.dni,
                        viaje.destino,
                        viaje.pais or '',
                        viaje.ciudad or '',
                        viaje.fecha_inicio.strftime('%Y-%m-%d'),
                        viaje.fecha_fin.strftime('%Y-%m-%d'),
                        viaje.estado,
                        dias_totales,
                        dias_exentos,
                        dias_no_exentos,
                        'Sin gastos registrados',
                        '0.00',
                        '',
                        'N/A',
                        'Sin_comprobante'
                    ])
            
            # Agregar CSV al ZIP con BOM para mejor compatibilidad con Excel
            csv_content = '\ufeff' + csv_buffer.getvalue()  # BOM para UTF-8
            zip_file.writestr(f'{empleado.nombre}_{empleado.apellido}_resumen.csv', csv_content.encode('utf-8'))
        
        zip_buffer.seek(0)
        response = HttpResponse(zip_buffer.read(), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
    
    def _safe_filename(self, filename):
        """Convierte un string en un nombre de archivo/carpeta seguro"""
        import re
        safe = re.sub(r'[<>:"/\\|?*]', '_', str(filename))
        safe = re.sub(r'\s+', '_', safe)
        return safe[:50]