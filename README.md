# Foodgram Project

## Foodgram is an online platform for publishing and sharing recipes. Users can post their own recipes, add them to favorites, generate shopping lists, and follow other authors. The project is built with Django and runs inside Docker containers for scalability and accessibility.

<img width="1280" height="715" alt="image" src="https://github.com/user-attachments/assets/b2c409c4-1a2d-4e78-a035-e46844c59e15" />
<img width="1280" height="792" alt="image" src="https://github.com/user-attachments/assets/1c638132-e24a-49af-bf78-23771781cd4d" />
<img width="1280" height="702" alt="image" src="https://github.com/user-attachments/assets/796c570d-5c0f-44f3-ab45-19f68661e017" />
<img width="1280" height="696" alt="image" src="https://github.com/user-attachments/assets/652e3716-9b82-4829-9e72-54e4472fad3c" />
<img width="1280" height="677" alt="image" src="https://github.com/user-attachments/assets/22060f95-3211-4ad2-b37f-8d0a1033b3d4" />

## Key Features:

1. **Sorting and Filtering:**
    Recipes are sorted by publication date across all pages. Tag-based filtering is supported, including on the favorites page and author-specific recipe lists.

2. **Pagination:** 
    Pagination works across all recipe views, including filtered results.

3. **Preloaded Test Data:** 
    Includes sample users and recipes for testing and demonstration.

4. **Shopping List:**
    Users can download their shopping list in .txt, .pdf, or other formats. Ingredients are summed up by type.

5. **Database:** 
    Uses PostgreSQL as the database engine.

6. **Containerized Deployment:** 
    Runs on a virtual server using three containers: Nginx, PostgreSQL, and Django+Gunicorn. The frontend is built and served from a separate container.

7. **Persistent Storage** 
    Data is stored using Docker volumes.

8. **Code Style:**
    Fully compliant with PEP 8 coding standards.

## Project Architecture

### The application is deployed in Docker containers:

### Nginx — serves static files and proxies requests to Gunicorn.

### PostgreSQL — stores application data.

### Django + Gunicorn — serves the backend.

### Frontend — built and served from a separate container.


## Technology Stack

<img src="https://img.shields.io/badge/Python-3670A0?style=for-the-badge&logo=python&logoColor=white"/>

<img src="https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white"/>

<img src="https://img.shields.io/badge/Gunicorn-2496ED?style=for-the-badge&logo=gunicorn&logoColor=white"/>

<img src="https://img.shields.io/badge/Nginx-009639?style=for-the-badge&logo=nginx&logoColor=white"/>

<img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white"/>

<img src="https://img.shields.io/badge/Djoser-2496ED?style=for-the-badge&logo=djoser&logoColor=white"/>

<img src="https://img.shields.io/badge/Django%20REST%20Framework-00796D?style=for-the-badge&logo=django&logoColor=white"/>

## How to Run the Project

1. **Clone the repository:**
    ```bash
    git clone https://github.com/closecodex/foodgram.git
    cd foodgram
    ```

3. **Create an .env file based on .env.example and fill in the required variables.**

4. **Build and run Docker containers:**
    ```bash
    docker-compose up -d --build
    ```
    
6. **Run migrations and collect static files:**
    ```bash
    docker-compose exec backend python manage.py migrate
    docker-compose exec backend python manage.py collectstatic --noinput
    ```
    
8. **Create a superuser:**
    ```bash
    docker-compose exec backend python manage.py createsuperuser
    ```

### Website URL: http://89.169.173.241/
### IP: 89.169.173.241
