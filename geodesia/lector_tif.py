# ==========================================
# LECTOR DE MODELOS TIF
# ==========================================

import rasterio

def leer_tif(nombre_archivo):

    with rasterio.open(nombre_archivo) as src:

        matriz = src.read(1)

        transform = src.transform

        # Coordenadas del origen (esquina superior izquierda)
        x_min = transform.c
        y_max = transform.f

        # Tamaño del píxel
        paso_x = transform.a
        paso_y = abs(transform.e)

    return (
        x_min,
        y_max,
        paso_x,
        paso_y,
        matriz
    )