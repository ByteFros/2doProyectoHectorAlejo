"""
Servicios de lógica de negocio para exportación de datos
"""
import csv
import os
import re
import zipfile
from io import BytesIO, StringIO
from typing import List, Tuple
from users.models import Viaje, Gasto, EmpresaProfile, EmpleadoProfile


# ============================================================================
# UTILIDADES
# ============================================================================

def safe_filename(filename: str, max_length: int = 50) -> str:
    """
    Convierte un string en un nombre de archivo/carpeta seguro.

    Args:
        filename: Nombre a convertir
        max_length: Longitud máxima del nombre

    Returns:
        Nombre de archivo seguro
    """
    # Eliminar caracteres no válidos
    safe = re.sub(r'[<>:"/\\|?*]', '_', str(filename))
    # Eliminar espacios múltiples
    safe = re.sub(r'\s+', '_', safe)
    # Truncar si es muy largo
    return safe[:max_length]


def calcular_dias_viaje(viaje: Viaje) -> Tuple[int, int, int]:
    """
    Calcula días totales, exentos y no exentos de un viaje.

    Args:
        viaje: Viaje a analizar

    Returns:
        Tupla (dias_totales, dias_exentos, dias_no_exentos)
    """
    dias_totales = viaje.dias_viajados or ((viaje.fecha_fin - viaje.fecha_inicio).days + 1)
    dias = viaje.dias.all()
    dias_exentos = dias.filter(exento=True).count()
    dias_no_exentos = dias.filter(exento=False).count()

    return dias_totales, dias_exentos, dias_no_exentos


# ============================================================================
# SERVICIOS DE EXPORTACIÓN CSV
# ============================================================================

def generar_csv_viajes_master(viajes_queryset) -> str:
    """
    Genera CSV de viajes para MASTER (todas las empresas).

    Args:
        viajes_queryset: QuerySet de viajes

    Returns:
        String con contenido CSV
    """
    output = StringIO()
    writer = csv.writer(output, delimiter=";")

    writer.writerow([
        "Empresa", "Empleado", "Destino", "Fecha Inicio", "Fecha Fin",
        "Días Exentos", "Días No Exentos", "Motivo"
    ])

    for viaje in viajes_queryset:
        _, dias_exentos, dias_no_exentos = calcular_dias_viaje(viaje)
        writer.writerow([
            viaje.empresa.nombre_empresa,
            f"{viaje.empleado.nombre} {viaje.empleado.apellido}",
            viaje.destino,
            viaje.fecha_inicio.strftime("%Y-%m-%d"),
            viaje.fecha_fin.strftime("%Y-%m-%d"),
            dias_exentos,
            dias_no_exentos,
            viaje.motivo.replace("\n", " ").strip(),
        ])

    return output.getvalue()


def generar_csv_viajes_empresa(viajes_queryset) -> str:
    """
    Genera CSV de viajes para EMPRESA.

    Args:
        viajes_queryset: QuerySet de viajes

    Returns:
        String con contenido CSV
    """
    output = StringIO()
    writer = csv.writer(output, delimiter=";")

    writer.writerow([
        "Empleado", "Destino", "Fecha Inicio", "Fecha Fin",
        "Días Exentos", "Días No Exentos", "Motivo"
    ])

    for viaje in viajes_queryset:
        _, dias_exentos, dias_no_exentos = calcular_dias_viaje(viaje)
        writer.writerow([
            f"{viaje.empleado.nombre} {viaje.empleado.apellido}",
            viaje.destino,
            viaje.fecha_inicio.strftime("%Y-%m-%d"),
            viaje.fecha_fin.strftime("%Y-%m-%d"),
            dias_exentos,
            dias_no_exentos,
            viaje.motivo.replace("\n", " ").strip(),
        ])

    return output.getvalue()


def generar_csv_viajes_con_gastos(viajes_queryset) -> str:
    """
    Genera CSV de viajes con sus gastos asociados.

    Args:
        viajes_queryset: QuerySet de viajes

    Returns:
        String con contenido CSV
    """
    output = StringIO()
    writer = csv.writer(output, delimiter=";")

    writer.writerow([
        "Empresa", "Empleado", "DNI", "Destino", "País", "Ciudad",
        "Fecha Inicio", "Fecha Fin", "Estado Viaje", "Días Totales",
        "Días Exentos", "Días No Exentos", "Concepto Gasto", "Monto",
        "Fecha Gasto", "Estado Gasto", "Tiene Comprobante"
    ])

    for viaje in viajes_queryset:
        dias_totales, dias_exentos, dias_no_exentos = calcular_dias_viaje(viaje)
        gastos = Gasto.objects.filter(viaje=viaje)

        if gastos.exists():
            for gasto in gastos:
                writer.writerow([
                    viaje.empresa.nombre_empresa,
                    f"{viaje.empleado.nombre} {viaje.empleado.apellido}",
                    viaje.empleado.dni,
                    viaje.destino,
                    viaje.pais or "",
                    viaje.ciudad or "",
                    viaje.fecha_inicio.strftime("%Y-%m-%d"),
                    viaje.fecha_fin.strftime("%Y-%m-%d"),
                    viaje.estado,
                    dias_totales,
                    dias_exentos,
                    dias_no_exentos,
                    gasto.concepto,
                    f"{gasto.monto:.2f}",
                    gasto.fecha_gasto.strftime("%Y-%m-%d") if gasto.fecha_gasto else "",
                    gasto.estado,
                    "Sí" if gasto.comprobante else "No",
                ])
        else:
            writer.writerow([
                viaje.empresa.nombre_empresa,
                f"{viaje.empleado.nombre} {viaje.empleado.apellido}",
                viaje.empleado.dni,
                viaje.destino,
                viaje.pais or "",
                viaje.ciudad or "",
                viaje.fecha_inicio.strftime("%Y-%m-%d"),
                viaje.fecha_fin.strftime("%Y-%m-%d"),
                viaje.estado,
                dias_totales,
                dias_exentos,
                dias_no_exentos,
                "Sin gastos registrados",
                "0.00",
                "",
                "N/A",
                "No",
            ])

    return output.getvalue()


# ============================================================================
# SERVICIOS DE EXPORTACIÓN ZIP
# ============================================================================

def agregar_comprobante_a_zip(zip_file, gasto: Gasto, archivo_path: str, archivos_agregados: set) -> str:
    """
    Agrega el comprobante de un gasto al archivo ZIP.

    Args:
        zip_file: Objeto ZipFile
        gasto: Gasto con comprobante
        archivo_path: Ruta donde guardar en el ZIP
        archivos_agregados: Set de archivos ya agregados

    Returns:
        Nombre del archivo agregado o mensaje de error
    """
    if not gasto.comprobante:
        return "Sin_comprobante"

    try:
        if not gasto.comprobante.storage.exists(gasto.comprobante.name):
            return f"Archivo_no_encontrado_gasto_{gasto.id}"

        # Obtener extensión
        archivo_original = os.path.basename(gasto.comprobante.name)
        extension = os.path.splitext(archivo_original)[1]
        archivo_nombre = f"Gasto_{gasto.id}_{safe_filename(gasto.concepto[:30])}{extension}"
        archivo_path_completo = archivo_path + archivo_nombre

        # Evitar duplicados
        if archivo_path_completo not in archivos_agregados:
            with gasto.comprobante.open('rb') as f:
                archivo_contenido = f.read()

            zip_file.writestr(archivo_path_completo, archivo_contenido)
            archivos_agregados.add(archivo_path_completo)

        return archivo_nombre

    except Exception as e:
        return f"Error_archivo_gasto_{gasto.id}"


def generar_zip_viajes_con_gastos(viajes_queryset, rol_usuario: str, empresa_nombre: str = None) -> BytesIO:
    """
    Genera un archivo ZIP con viajes, gastos y comprobantes.

    Args:
        viajes_queryset: QuerySet de viajes
        rol_usuario: Rol del usuario (MASTER, EMPRESA, EMPLEADO)
        empresa_nombre: Nombre de empresa (opcional, para estructurar carpetas)

    Returns:
        BytesIO con el contenido del ZIP
    """
    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        csv_buffer = StringIO()
        writer = csv.writer(csv_buffer, delimiter=';')

        # Headers
        writer.writerow([
            'Empresa', 'Empleado', 'DNI', 'Destino', 'País', 'Ciudad',
            'Fecha Inicio', 'Fecha Fin', 'Estado Viaje', 'Días Totales',
            'Días Exentos', 'Días No Exentos', 'Concepto Gasto', 'Monto',
            'Fecha Gasto', 'Estado Gasto', 'Archivo Comprobante'
        ])

        archivos_agregados = set()

        for viaje in viajes_queryset:
            dias_totales, dias_exentos, dias_no_exentos = calcular_dias_viaje(viaje)
            gastos = Gasto.objects.filter(viaje=viaje)

            # Estructura de carpetas según rol
            if rol_usuario == "EMPLEADO":
                viaje_folder = f"Viaje_{viaje.id}_{safe_filename(viaje.destino)}"
                base_path = f"{viaje_folder}/"
            else:
                empresa_folder = safe_filename(viaje.empresa.nombre_empresa)
                empleado_folder = safe_filename(f"{viaje.empleado.nombre}_{viaje.empleado.apellido}")
                viaje_folder = f"Viaje_{viaje.id}_{safe_filename(viaje.destino)}"
                base_path = f"{empresa_folder}/{empleado_folder}/{viaje_folder}/"

            if gastos.exists():
                for gasto in gastos:
                    archivo_nombre = agregar_comprobante_a_zip(
                        zip_file, gasto, base_path, archivos_agregados
                    )

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
                # Crear directorio vacío con placeholder
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

        # Agregar CSV al ZIP con BOM para Excel
        csv_content = '\ufeff' + csv_buffer.getvalue()
        zip_file.writestr('resumen_viajes_gastos.csv', csv_content.encode('utf-8'))

    zip_buffer.seek(0)
    return zip_buffer


# ============================================================================
# QUERIES PARA EXPORTACIÓN
# ============================================================================

def obtener_viajes_para_exportacion(usuario, empleado_id: int = None):
    """
    Obtiene viajes según el rol del usuario para exportación.

    Args:
        usuario: Usuario que solicita la exportación
        empleado_id: ID de empleado específico (opcional)

    Returns:
        Tuple (viajes_queryset, filename)
    """
    if empleado_id:
        empleado = EmpleadoProfile.objects.get(id=empleado_id)
        viajes = Viaje.objects.filter(
            empleado=empleado
        ).prefetch_related('dias__gastos')
        filename_base = f"{empleado.nombre}_{empleado.apellido}"
        return viajes, filename_base

    if usuario.role == "MASTER":
        viajes = Viaje.objects.select_related(
            'empresa', 'empleado'
        ).prefetch_related('dias__gastos')
        return viajes, "todos_los_viajes"

    elif usuario.role == "EMPRESA":
        empresa = EmpresaProfile.objects.get(user=usuario)
        viajes = Viaje.objects.filter(
            empresa=empresa
        ).select_related(
            'empleado'
        ).prefetch_related('dias__gastos')
        return viajes, safe_filename(empresa.nombre_empresa)

    elif usuario.role == "EMPLEADO":
        empleado = EmpleadoProfile.objects.get(user=usuario)
        viajes = Viaje.objects.filter(
            empleado=empleado
        ).prefetch_related('dias__gastos')
        return viajes, f"{empleado.nombre}_{empleado.apellido}"

    return Viaje.objects.none(), "sin_datos"
