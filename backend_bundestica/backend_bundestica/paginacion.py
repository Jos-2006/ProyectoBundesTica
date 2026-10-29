from rest_framework.pagination import PageNumberPagination


class PaginacionEstandar(PageNumberPagination):
    #crea el tamaño de paginas que va a tener cada lista

    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
