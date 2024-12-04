document.addEventListener('DOMContentLoaded', () => {
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    const ctx = canvas.getContext('2d');
    const status = document.getElementById('status');
    const successMessage = document.getElementById('successMessage');
    const compareResults = document.getElementById('compareResults');
    const startButton = document.getElementById('startButton');
    const stopButton = document.getElementById('stopButton');
    const uploadRadio = document.getElementById('uploadRadio');
    const compareRadio = document.getElementById('compareRadio');
    const nameSection = document.getElementById('nameSection');
    const imageNameInput = document.getElementById('imageName');

    let intervalId;
    let stream;

    // Actualizar la visibilidad del campo de nombre según la acción seleccionada
    uploadRadio.addEventListener('change', updateNameSectionVisibility);
    compareRadio.addEventListener('change', updateNameSectionVisibility);

    function updateNameSectionVisibility() {
        nameSection.style.display = uploadRadio.checked ? 'block' : 'none';
    }

    async function startRecording() {
        try {
            stream = await navigator.mediaDevices.getUserMedia({ video: true });
            video.srcObject = stream;

            intervalId = setInterval(captureAndSendFrame, 1000); // Capturar frames cada 1 segundo
        } catch (err) {
            console.error('Error al acceder a la cámara:', err);
        }
    }

    async function captureAndSendFrame() {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

        canvas.toBlob(async (blob) => {
            const formData = new FormData();
            formData.append('image', blob, 'frame.jpg');

            // Si es "Subir Persona", incluye el nombre
            if (uploadRadio.checked) {
                const imageName = imageNameInput.value.trim();
                if (!imageName) {
                    alert("Por favor, ingresa un nombre para la imagen.");
                    stopRecording();
                    return;
                }
                formData.append('name', imageName);
            }

            // Seleccionar endpoint según la acción
            const endpoint = uploadRadio.checked
                ? '/reconocimiento/upload/'
                : '/reconocimiento/compare/';

            // Enviar la imagen al backend
            try {
                const response = await fetch(endpoint, {
                    method: 'POST',
                    body: formData
                });

                if (response.ok) {
                    const data = await response.json();
                    if (uploadRadio.checked) {
                        // Respuesta para "Subir Persona"
                        status.innerText = "Estado: Imagen válida detectada";
                        successMessage.innerText = "¡Éxito! Persona guardada.";
                    } else {
                        // Respuesta para "Comprobar Persona"
                        const results = data.results;
                        compareResults.innerText = results.length
                            ? "Resultado de comparación: " + JSON.stringify(results)
                            : "No se encontraron coincidencias.";
                    }
                    stopRecording();
                } else {
                    const error = await response.json();
                    status.innerText = `Estado: ${error.error}`;
                }
            } catch (error) {
                console.error('Error al enviar la imagen:', error);
                status.innerText = "Estado: Error al procesar la imagen";
            }
        }, 'image/jpeg');
    }

    function stopRecording() {
        clearInterval(intervalId);
        if (stream) {
            const tracks = stream.getTracks();
            tracks.forEach((track) => track.stop());
        }
        video.srcObject = null;
        startButton.disabled = false;
        stopButton.disabled = true;
    }

    startButton.addEventListener('click', () => {
        startButton.disabled = true;
        stopButton.disabled = false;
        successMessage.innerText = "";
        compareResults.innerText = "";
        startRecording();
    });

    stopButton.addEventListener('click', () => {
        stopRecording();
        status.innerText = "Estado: Grabación detenida";
    });

    // Inicializar la visibilidad del campo de nombre
    updateNameSectionVisibility();
});

