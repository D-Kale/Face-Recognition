from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage
import face_recognition
import numpy as np
import os

IMAGE_DIR = 'images/'

# Asegúrate de que el directorio existe
os.makedirs(IMAGE_DIR, exist_ok=True)

def is_face_frontal(image):
    # Detectar las caras en la imagen
    face_locations = face_recognition.face_locations(image)
    
    if len(face_locations) == 0:
        return False  # No se encontró ninguna cara

    # Obtener la posición de la primera cara detectada
    top, right, bottom, left = face_locations[0]
    face_image = image[top:bottom, left:right]

    # Obtener los landmarks de la cara
    face_landmarks = face_recognition.face_landmarks(face_image)

    if not face_landmarks:
        return False  # No se encontraron landmarks

    # Obtener las posiciones de los ojos
    left_eye = face_landmarks[0]['left_eye']
    right_eye = face_landmarks[0]['right_eye']

    # Calcular la distancia entre los ojos
    eye_distance = np.linalg.norm(np.array(left_eye).mean(axis=0) - np.array(right_eye).mean(axis=0))

    # Calcular la altura de la cara
    face_height = bottom - top

    # Verificar si la relación de la distancia de los ojos a la altura de la cara es adecuada
    return eye_distance / face_height < 0.5  # Ajusta este valor según sea necesario

@csrf_exempt
def upload_image(request):
    if request.method == 'POST' and request.FILES.get('image'):
        file = request.FILES['image']
        name = request.POST.get('name')  # Obtener el nombre enviado desde el frontend

        if not name:
            return JsonResponse({'error': 'Name parameter is required'}, status=400)

        image = face_recognition.load_image_file(file)

        # Verificar si la cara está de frente
        if not is_face_frontal(image):
            return JsonResponse({'error': 'Face is not frontal'}, status=400)

        # Obtener los embeddings de la cara
        face_encodings = face_recognition.face_encodings(image)

        if len(face_encodings) == 0:
            return JsonResponse({'error': 'No face found in the image'}, status=400)

        # Guardar la imagen usando el nombre proporcionado
        face_encoding = face_encodings[0]
        filename = f"{name}.npy"
        file_path = os.path.join(IMAGE_DIR, filename)

        # Sobrescribir si ya existe
        np.save(file_path, face_encoding)

        return JsonResponse({'message': f'Image uploaded successfully as {filename}'}, status=200)
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def compare_image(request):
    if request.method == 'POST' and request.FILES.get('image'):
        file = request.FILES['image']
        image = face_recognition.load_image_file(file)
        face_encodings = face_recognition.face_encodings(image)

        if len(face_encodings) == 0:
            return JsonResponse({'error': 'No face found in the image'}, status=400)

        input_encoding = face_encodings[0]
        results = []

        # Comparar con las imágenes guardadas
        for filename in os.listdir(IMAGE_DIR):
            saved_encoding = np.load(os.path.join(IMAGE_DIR, filename))
            matches = face_recognition.compare_faces([saved_encoding], input_encoding)
            if matches[0]:
                results.append({'filename': filename, 'similarity': 100.0})  # 100% de similitud

        # Si no hay coincidencias exactas, calcular la similitud
        if not results:
            for filename in os.listdir(IMAGE_DIR):
                saved_encoding = np.load(os.path.join(IMAGE_DIR, filename))
                distance = face_recognition.face_distance([saved_encoding], input_encoding)[0]
                similarity = max(0, (1 - distance) * 100)  # Convertir distancia a porcentaje
                results.append({'filename': filename, 'similarity': round(similarity, 2)})

        return JsonResponse({'results': results}, status=200)

    return JsonResponse({'error': 'Invalid request'}, status=400)


def index(request):
    return render(request, 'index.html')