from fastapi import FastAPI, HTTPException
import pandas as pd
import os

# Definir la ruta de los archivos CSV
resultado_cast_actores_path = os.path.join(os.path.dirname(__file__), 'ResultadoCastActores.csv')
funcion_actor_path = os.path.join(os.path.dirname(__file__), 'FuncionActor.csv')
lista_actores_path = os.path.join(os.path.dirname(__file__), 'ListaActores.csv')

app = FastAPI()

# Cargar los datasets
try:
    ResultadoCastActores = pd.read_csv(resultado_cast_actores_path)
    funcion_actor = pd.read_csv(funcion_actor_path)
    lista_actores = pd.read_csv(lista_actores_path)
except FileNotFoundError as e:
    raise HTTPException(status_code=500, detail=f"Error al cargar los archivos: {str(e)}")

@app.get("/")
def welcome_message():
    return {
        "message": "Bienvenido a la API de Análisis de Actores de Cine",
        "description": "Esta API permite obtener información sobre el rendimiento financiero de actores en películas. Puedes consultar el retorno total y promedio de un actor en base a sus películas.",
        "endpoints": {
            "/actor/{actor_name}": {
                "description": "Obtiene el rendimiento financiero del actor especificado.",
                "example": "http://localhost:8000/actor/Leonardo%20DiCaprio",
                "parameters": {
                    "actor_name": "El nombre del actor que deseas consultar. Asegúrate de reemplazar los espacios con '%20'."
                }
            },
            "/actores": {
                "description": "Lista todos los actores disponibles en la base de datos.",
                "example": "http://localhost:8000/actores"
            }
        },
        "notes": "Para obtener resultados, asegúrate de que el nombre del actor esté correctamente escrito."
    }

@app.get("/actor/{actor_name}")
def obtener_retorno_actor(actor_name: str):
    if not actor_name:
        raise HTTPException(status_code=400, detail="El nombre del actor no puede estar vacío.")
    
    # Convertir el nombre del actor a minúsculas para la comparación
    actor_name_normalizado = actor_name.lower()
    
    # Filtrar las películas del actor
    peliculas_actor = ResultadoCastActores[ResultadoCastActores['name'].str.lower() == actor_name_normalizado]
    
    if peliculas_actor.empty:
        raise HTTPException(status_code=404, detail="Actor no encontrado")

    # Obtener los IDs de las películas
    movie_ids = peliculas_actor['movie_id'].tolist()
    
    # Filtrar las ganancias de las películas en FuncionActor
    ganancias_actor = funcion_actor[funcion_actor['id'].isin(movie_ids)]
    
    # Calcular el retorno total
    retorno_total = ganancias_actor['return'].sum()
    
    # Filtrar las ganancias donde el retorno es mayor que 0
    ganancias_validas = ganancias_actor[ganancias_actor['return'] > 0]
    cantidad_peliculas_validas = len(ganancias_validas)

    if cantidad_peliculas_validas > 0:
        retorno_promedio = round(ganancias_validas['return'].mean(), 2) * 100  # Multiplicado por 100
    else:
        retorno_promedio = 0.0  # Si no hay películas válidas, el retorno promedio es 0

    # Formatear los retornos con signo de dólar y multiplicar por 100
    retorno_total_formateado = f"{retorno_total * 100:,.2f}%"  # Multiplicado por 100
    retorno_promedio_formateado = f"{retorno_promedio:,.2f}%"  # Ya está multiplicado por 100
    
    # Obtener películas con retorno de 0
    peliculas_con_return_zero = ganancias_actor[ganancias_actor['return'] == 0]['id'].tolist()
    peliculas_con_return_zero_count = len(peliculas_con_return_zero)

    return {
        "actor": actor_name,
        "cantidad_de_peliculas_en_que_actuó": len(ganancias_actor),
        "cantidad_de_peliculas_con_return_0": peliculas_con_return_zero_count,
        "return_total": retorno_total_formateado,
        "return_promedio": retorno_promedio_formateado,
        "return_promedio_contando_zeros": f"{round(retorno_total / len(ganancias_actor) * 100, 2):,.2f}%"  # Multiplicado por 100
    }

@app.get("/actores")
def listar_actores():
    # Extraer la lista de actores y normalizarlos a minúsculas
    actores_lista = lista_actores['name'].str.lower().tolist()  # Asegúrate de que la columna se llama 'name'
    
    return {
        "actores": actores_lista
    }