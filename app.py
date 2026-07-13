from flask import Flask, render_template, request
from pyproj import Transformer

from geodesia.lector_modelo import leer_modelo
from geodesia.lector_tif import leer_tif

app = Flask(__name__)


# ==========================================
# FUNCIONES
# ==========================================

def cargar_modelo(opcion):

    if opcion == "GeoCOL 2004":

        (
            lat_min,
            lat_max,
            lon_min,
            lon_max,
            paso_lat,
            paso_lon,
            matriz
        ) = leer_modelo("modelos/Geocol2004.txt")

        return {
            "sistema": "geografico",
            "lat_min": lat_min,
            "lat_max": lat_max,
            "lon_min": lon_min,
            "lon_max": lon_max,
            "paso_lat": paso_lat,
            "paso_lon": paso_lon,
            "matriz": matriz
        }

    else:

        (
            x_min,
            y_max,
            paso_x,
            paso_y,
            matriz
        ) = leer_tif("modelos/Geovalle2015.tif")

        return {
            "sistema": "3115",
            "x_min": x_min,
            "y_max": y_max,
            "paso_x": paso_x,
            "paso_y": paso_y,
            "matriz": matriz
        }


def obtener_indices(modelo, lat, lon):

    if modelo["sistema"] == "geografico":

        fila = (lat - modelo["lat_min"]) / modelo["paso_lat"]
        columna = (lon - modelo["lon_min"]) / modelo["paso_lon"]

    else:

        transformer = Transformer.from_crs(
            4326,
            3115,
            always_xy=True
        )

        x, y = transformer.transform(lon, lat)

        columna = (x - modelo["x_min"]) / modelo["paso_x"]
        fila = (modelo["y_max"] - y) / modelo["paso_y"]

    return fila, columna


def interpolacion(modelo, lat, lon):

    fila, columna = obtener_indices(modelo, lat, lon)

    i = int(fila)
    j = int(columna)

    dx = columna - j
    dy = fila - i

    matriz = modelo["matriz"]

    Q11 = matriz[i, j]
    Q21 = matriz[i, j + 1]
    Q12 = matriz[i + 1, j]
    Q22 = matriz[i + 1, j + 1]

    N = (
        Q11 * (1 - dx) * (1 - dy)
        + Q21 * dx * (1 - dy)
        + Q12 * (1 - dx) * dy
        + Q22 * dx * dy
    )

    return round(float(N), 4)


# ==========================================
# RUTA PRINCIPAL
# ==========================================

@app.route("/", methods=["GET", "POST"])
def inicio():

    if request.method == "POST":

        modelo_nombre = request.form["modelo"]
        lat = float(request.form["latitud"])
        lon = float(request.form["longitud"])
        h = float(request.form["altura"])

        modelo = cargar_modelo(modelo_nombre)

        fila, columna = obtener_indices(modelo, lat, lon)

        if (
            fila < 0
            or columna < 0
            or fila >= modelo["matriz"].shape[0] - 1
            or columna >= modelo["matriz"].shape[1] - 1
        ):

            return render_template(
                "index.html",
                error="El punto está fuera de la cobertura del modelo."
            )

        N = interpolacion(modelo, lat, lon)

        H = round(h - N, 4)

        return render_template(
            "index.html",
            modelo=modelo_nombre,
            latitud=lat,
            longitud=lon,
            h=h,
            N=N,
            H=H
        )

    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)