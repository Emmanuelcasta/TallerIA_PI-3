from openai import OpenAI
import numpy as np
import os
from dotenv import load_dotenv
from .models import Movie

def recommend(request):
    recommended_movie = None
    prompt = request.GET.get('prompt', '').lower()
    
    if prompt:
        # Lista de géneros comunes para buscar en el prompt
        genres = ['acción', 'aventura', 'comedia', 'drama', 'terror', 'sci-fi', 
                 'romance', 'fantasía', 'animación', 'documental', 'guerra']
        
        # Detectar si hay un año en el prompt (4 dígitos)
        import re
        year_match = re.search(r'\b\d{4}\b', prompt)
        year = year_match.group(0) if year_match else None
        
        # Detectar géneros mencionados en el prompt
        mentioned_genres = [genre for genre in genres if genre in prompt]
        
        # Construir la consulta base
        query = Movie.objects.all()
        
        # Filtrar por año si se especificó
        if year:
            query = query.filter(year=year)
            
        # Filtrar por género si se mencionó alguno
        if mentioned_genres:
            for genre in mentioned_genres:
                query = query.filter(genre__icontains=genre)
        
        # Buscar en título y descripción
        movies = query.filter(description__icontains=prompt) | \
                query.filter(title__icontains=prompt) | \
                query.filter(genre__icontains=prompt)
        
        if movies.exists():
            # Tomamos la primera película que coincida
            recommended_movie = movies.first()
        else:
            # Si no encontramos nada específico, buscamos de forma más general
            movies = Movie.objects.filter(description__icontains=prompt) | \
                    Movie.objects.filter(title__icontains=prompt) | \
                    Movie.objects.filter(genre__icontains=prompt)
            if movies.exists():
                recommended_movie = movies.first()
    
    return render(request, "recommend.html", {
        "recommended_movie": recommended_movie,
        "prompt": prompt
    })
from django.shortcuts import render
from django.http import HttpResponse

from .models import Movie

import matplotlib.pyplot as plt
import matplotlib
import io
import urllib, base64

def home(request):
    #return HttpResponse('<h1>Welcome to Home Page</h1>')
    #return render(request, 'home.html')
    #return render(request, 'home.html', {'name':'Paola Vallejo'})
    searchTerm = request.GET.get('searchMovie') # GET se usa para solicitar recursos de un servidor
    if searchTerm:
        movies = Movie.objects.filter(title__icontains=searchTerm)
    else:
        movies = Movie.objects.all()
    return render(request, 'home.html', {'searchTerm':searchTerm, 'movies':movies})


def about(request):
    #return HttpResponse('<h1>Welcome to About Page</h1>')
    return render(request, 'about.html')

def signup(request):
    email = request.GET.get('email') 
    return render(request, 'signup.html', {'email':email})


def statistics_view0(request):
    matplotlib.use('Agg')
    # Obtener todas las películas
    all_movies = Movie.objects.all()

    # Crear un diccionario para almacenar la cantidad de películas por año
    movie_counts_by_year = {}

    # Filtrar las películas por año y contar la cantidad de películas por año
    for movie in all_movies:
        year = movie.year if movie.year else "None"
        if year in movie_counts_by_year:
            movie_counts_by_year[year] += 1
        else:
            movie_counts_by_year[year] = 1

    # Ancho de las barras
    bar_width = 0.5
    # Posiciones de las barras
    bar_positions = range(len(movie_counts_by_year))

    # Crear la gráfica de barras
    plt.bar(bar_positions, movie_counts_by_year.values(), width=bar_width, align='center')

    # Personalizar la gráfica
    plt.title('Movies per year')
    plt.xlabel('Year')
    plt.ylabel('Number of movies')
    plt.xticks(bar_positions, movie_counts_by_year.keys(), rotation=90)

    # Ajustar el espaciado entre las barras
    plt.subplots_adjust(bottom=0.3)

    # Guardar la gráfica en un objeto BytesIO
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close()

    # Convertir la gráfica a base64
    image_png = buffer.getvalue()
    buffer.close()
    graphic = base64.b64encode(image_png)
    graphic = graphic.decode('utf-8')

    # Renderizar la plantilla statistics.html con la gráfica
    return render(request, 'statistics.html', {'graphic': graphic})

def statistics_view(request):
    matplotlib.use('Agg')
    # Gráfica de películas por año
    all_movies = Movie.objects.all()
    movie_counts_by_year = {}
    for movie in all_movies:
        print(movie.genre)
        year = movie.year if movie.year else "None"
        if year in movie_counts_by_year:
            movie_counts_by_year[year] += 1
        else:
            movie_counts_by_year[year] = 1

    year_graphic = generate_bar_chart(movie_counts_by_year, 'Year', 'Number of movies')

    # Gráfica de películas por género
    movie_counts_by_genre = {}
    for movie in all_movies:
        # Obtener el primer género
        genres = movie.genre.split(',')[0].strip() if movie.genre else "None"
        if genres in movie_counts_by_genre:
            movie_counts_by_genre[genres] += 1
        else:
            movie_counts_by_genre[genres] = 1

    genre_graphic = generate_bar_chart(movie_counts_by_genre, 'Genre', 'Number of movies')

    return render(request, 'statistics.html', {'year_graphic': year_graphic, 'genre_graphic': genre_graphic})


def generate_bar_chart(data, xlabel, ylabel):
    keys = [str(key) for key in data.keys()]
    plt.bar(keys, data.values())
    plt.title('Movies Distribution')
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.xticks(rotation=90)
    plt.tight_layout()
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close()
    image_png = buffer.getvalue()
    buffer.close()
    graphic = base64.b64encode(image_png).decode('utf-8')
    return graphic