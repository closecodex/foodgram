# Foodgram Project

## Foodgram is an online platform for publishing and sharing recipes. Users can post their own recipes, add them to favorites, generate shopping lists, and follow other authors. The project is built with Django and runs inside Docker containers for scalability and accessibility.

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

1. **Django**

2. **PostgreSQL**

3. **Gunicorn**

4. **Nginx**

5. **Docker**

6. **Django Rest Framework**

7. **Djoser для аутентификации пользователей**

## How to Run the Project

1. **Clone the repository:**
    git clone https://github.com/username/foodgram-project.git
    cd foodgram-project

2. **Create an .env file based on .env.example and fill in the required variables.**

3. **Build and run Docker containers:**
    docker-compose up -d --build

4. **Run migrations and collect static files:**
    docker-compose exec backend python manage.py migrate
    docker-compose exec backend python manage.py collectstatic --noinput

5. **Create a superuser:**
    docker-compose exec backend python manage.py createsuperuser

### Website URL: http://89.169.173.241/
### IP: 89.169.173.241
