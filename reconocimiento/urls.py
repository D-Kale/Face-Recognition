from django.urls import path
from .views import upload_image, compare_image, index

urlpatterns = [
    path('', index, name='index'),  # Vista principal
    path('upload/', upload_image, name='upload_image'),
    path('compare/', compare_image, name='compare_image'),
]