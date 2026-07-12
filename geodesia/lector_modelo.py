import numpy as np

def leer_modelo(nombre_archivo):

    with open(nombre_archivo) as archivo:

        lineas = archivo.readlines()

    encabezado = list(map(float, lineas[0].split()))

    lat_min = encabezado[0]
    lat_max = encabezado[1]
    lon_min = encabezado[2]
    lon_max = encabezado[3]

    paso_lat = encabezado[4]
    paso_lon = encabezado[5]

    matriz = []

    for linea in lineas[1:]:

        matriz.append(list(map(float, linea.split())))

    matriz = np.array(matriz)

    return (
        lat_min,
        lat_max,
        lon_min,
        lon_max,
        paso_lat,
        paso_lon,
        matriz
    )