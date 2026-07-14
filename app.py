from flask import Flask, render_template, request
from pyproj import Transformer

from geodesia.lector_modelo import leer_modelo
from geodesia.lector_tif import leer_tif

app = Flask(__name__)


# ==========================================
# CARGAR MODELO
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

            "tipo": "GeoCOL",

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

            "tipo": "GeoValle",

            "x_min": x_min,
            "y_max": y_max,

            "paso_x": paso_x,
            "paso_y": paso_y,

            "matriz": matriz

        }


# ==========================================
# CONVERSIÓN DE COORDENADAS
# ==========================================

def convertir_coordenadas(sistema, coord1, coord2):

    if sistema == "geo":

        lat = coord1
        lon = coord2

    elif sistema == "9377":

        transformer = Transformer.from_crs(
            9377,
            4326,
            always_xy=True
        )

        lon, lat = transformer.transform(
            coord2,
            coord1
        )

    elif sistema == "6249":

        transformer = Transformer.from_crs(
            6249,
            4326,
            always_xy=True
        )

        lon, lat = transformer.transform(
            coord2,
            coord1
        )

    return lat, lon


# ==========================================
# UBICACIÓN EN LA MATRIZ
# ==========================================

def obtener_indices(modelo, lat, lon):

    if modelo["tipo"] == "GeoCOL":

        fila = (
            lat - modelo["lat_min"]
        ) / modelo["paso_lat"]

        columna = (
            lon - modelo["lon_min"]
        ) / modelo["paso_lon"]

    else:

        transformer = Transformer.from_crs(
            4326,
            3115,
            always_xy=True
        )

        x, y = transformer.transform(
            lon,
            lat
        )

        columna = (
            x - modelo["x_min"]
        ) / modelo["paso_x"]

        fila = (
            modelo["y_max"] - y
        ) / modelo["paso_y"]

    return fila, columna


# ==========================================
# INTERPOLACIÓN BILINEAL
# ==========================================

def interpolacion(modelo, lat, lon):

    fila, columna = obtener_indices(
        modelo,
        lat,
        lon
    )

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
# DECIMAL A GMS
# ==========================================

def decimal_a_gms(valor, tipo):

    grados = int(abs(valor))

    minutos_decimal = (abs(valor) - grados) * 60

    minutos = int(minutos_decimal)

    segundos = (minutos_decimal - minutos) * 60

    if tipo == "lat":

        hemisferio = "N" if valor >= 0 else "S"

    else:

        hemisferio = "E" if valor >= 0 else "O"

    return f"{grados}° {minutos}' {segundos:.2f}\" {hemisferio}"


# ==========================================
# PÁGINA PRINCIPAL
# ==========================================

@app.route("/", methods=["GET", "POST"])
def inicio():

    if request.method == "POST":

        modelo_nombre = request.form["modelo"]

        sistema = request.form["sistema"]

        coord1 = float(request.form["coord1"])
        coord2 = float(request.form["coord2"])

        h = float(request.form["altura"])

        # ===========================
        # Conversión de coordenadas
        # ===========================

        lat, lon = convertir_coordenadas(
            sistema,
            coord1,
            coord2
        )

        # ===========================
        # Validaciones
        # ===========================

        if lat < -4.5 or lat > 13.5:

            return render_template(
                "index.html",
                error="La latitud está fuera del territorio colombiano."
            )

        if lon < -79.5 or lon > -66.5:

            return render_template(
                "index.html",
                error="La longitud está fuera del territorio colombiano."
            )

        if h < -50 or h > 6000:

            return render_template(
                "index.html",
                error="La altura debe estar entre -50 y 6000 metros."
            )

        # ===========================
        # Cargar modelo
        # ===========================

        modelo = cargar_modelo(modelo_nombre)

        fila, columna = obtener_indices(
            modelo,
            lat,
            lon
        )

        # ===========================
        # Cobertura
        # ===========================

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
        # ===========================
        # Cálculo
        # ===========================

        N = interpolacion(
            modelo,
            lat,
            lon
        )

        H = round(
            h - N,
            4
        )

        # ===========================
        # Año del modelo
        # ===========================

        if modelo_nombre == "GeoCOL 2004":

            fecha_modelo = "2004"

        else:

            fecha_modelo = "2015"

        # ===========================
        # Mostrar resultados
        # ===========================

        return render_template(

            "index.html",

            modelo=modelo_nombre,

            latitud=round(lat, 8),

            longitud=round(lon, 8),

            lat_gms=decimal_a_gms(lat, "lat"),
            
            lon_gms=decimal_a_gms(lon, "lon"),

            h=round(h, 4),

            N=round(N, 4),

            H=round(H, 4),

            fecha_modelo=fecha_modelo

        )

    return render_template("index.html")


# ==========================================
# EJECUTAR FLASK
# ==========================================

if __name__ == "__main__":

    app.run(debug=True)