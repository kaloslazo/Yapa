"""Detector opcional y local: no escribe fotos ni modifica el negocio."""
from __future__ import annotations
import hashlib
import io
import os
import threading
from pathlib import Path
from collections import defaultdict
from .domain import BusinessRuleError

MODEL_PATH = Path(__file__).with_name('modelos') / 'vegetable4-v8s.pt'
MODEL_SHA256 = 'ddcc76ea30070e9cd05baf71c5792d644c3c8edf7abea381b55483ab594144b6'
CLASSES = ('papa', 'cebolla', 'ajo', 'zanahoria')
THRESHOLD = 0.35
_lock = threading.Lock()
_model = None

def summarize(names, boxes):
    groups = defaultdict(list)
    for class_id, confidence in boxes:
        name = names.get(int(class_id))
        if name in CLASSES and THRESHOLD <= float(confidence) <= 1:
            groups[name].append(float(confidence))
    return [{'producto': name, 'cantidad': len(groups[name]), 'confianza': round(min(groups[name]), 3)}
            for name in CLASSES if groups[name]]

def _load_model():
    global _model
    if _model is None:
        try:
            os.environ['YOLO_AUTOINSTALL'] = 'False'
            import torch
            from ultralytics import YOLO
        except ImportError as error:
            raise BusinessRuleError('VISION_UNAVAILABLE', 'El análisis no está instalado en este servidor. Puedes revisar la foto manualmente.') from error
        if not MODEL_PATH.is_file() or hashlib.sha256(MODEL_PATH.read_bytes()).hexdigest() != MODEL_SHA256:
            raise BusinessRuleError('VISION_UNAVAILABLE', 'No está disponible el modelo de Yapa. Puedes continuar manualmente.')
        torch.set_num_threads(2)
        _model = YOLO(str(MODEL_PATH))
        if set(_model.names.values()) != set(CLASSES):
            _model = None
            raise BusinessRuleError('VISION_UNAVAILABLE', 'Las clases del modelo no corresponden a Yapa.')
    return _model

def analyze_photo(upload):
    if not upload or not upload[1]:
        raise BusinessRuleError('PHOTO_REQUIRED', 'Elige una foto para analizar.')
    content = upload[1]
    if len(content) > 8 * 1024 * 1024:
        raise BusinessRuleError('PHOTO_TOO_LARGE', 'La foto pesa más de 8 MB.')
    if not (content.startswith(b'\xff\xd8\xff') or content.startswith(b'\x89PNG\r\n\x1a\n')
            or (content.startswith(b'RIFF') and content[8:12] == b'WEBP')):
        raise BusinessRuleError('INVALID_PHOTO', 'Usa una foto JPG, PNG o WebP válida para analizar.')
    try:
        from PIL import Image, ImageOps, UnidentifiedImageError
    except ImportError as error:
        raise BusinessRuleError('VISION_UNAVAILABLE', 'El análisis no está instalado. Puedes continuar manualmente.') from error
    try:
        with Image.open(io.BytesIO(content)) as source:
            if source.width * source.height > 20_000_000:
                raise BusinessRuleError('PHOTO_TOO_LARGE', 'La imagen supera los 20 megapíxeles. Usa una foto más pequeña.')
            image = ImageOps.exif_transpose(source).convert('RGB')
    except (UnidentifiedImageError, OSError, ValueError, ImportError, Image.DecompressionBombError) as error:
        raise BusinessRuleError('INVALID_PHOTO', 'Usa una foto JPG, PNG o WebP válida para analizar.') from error
    if not _lock.acquire(blocking=False):
        raise BusinessRuleError('VISION_BUSY', 'Hay una foto en análisis. Intenta de nuevo en unos segundos.')
    try:
        result = _load_model().predict(image, imgsz=640, conf=THRESHOLD, device='cpu', max_det=300, verbose=False)[0]
        boxes = zip(result.boxes.cls.tolist(), result.boxes.conf.tolist())
        return {'modelo': 'Yapa YOLOv8 Small', 'umbral': THRESHOLD, 'productos': summarize(result.names, boxes),
                'aviso': 'Sugerencia de objetos visibles. Revisa producto y cantidad: el modelo puede fallar. No estima peso.'}
    except BusinessRuleError:
        raise
    except Exception as error:
        raise BusinessRuleError('VISION_UNAVAILABLE', 'No se pudo analizar la foto. Puedes completar la revisión manualmente.') from error
    finally:
        _lock.release()
