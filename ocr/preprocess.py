import os
from typing import List

import cv2
import numpy as np


def _auto_deskew(gray: np.ndarray) -> np.ndarray:
    # бинаризация для поиска наклона
    bw = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    coords = np.column_stack(np.where(bw == 0))
    if coords.size == 0:
        return gray
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    (h, w) = gray.shape[:2]
    M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
    return cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)


def _unsharp(img: np.ndarray) -> np.ndarray:
    blur = cv2.GaussianBlur(img, (0, 0), 1.0)
    sharp = cv2.addWeighted(img, 1.5, blur, -0.5, 0)
    return sharp


def _find_doc_warp(img: np.ndarray) -> np.ndarray | None:
    """Ищем четырёхугольник документа и делаем перспективную коррекцию."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(gray, 60, 160)
    cnts, _ = cv2.findContours(edged, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:10]
    for c in cnts:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4:
            pts = approx.reshape(4, 2).astype(np.float32)
            # упорядочим точки
            s = pts.sum(axis=1)
            diff = np.diff(pts, axis=1).reshape(-1)
            rect = np.zeros((4, 2), dtype=np.float32)
            rect[0] = pts[np.argmin(s)]     # TL
            rect[2] = pts[np.argmax(s)]     # BR
            rect[1] = pts[np.argmin(diff)]  # TR
            rect[3] = pts[np.argmax(diff)]  # BL

            (tl, tr, br, bl) = rect
            wA = np.linalg.norm(br - bl)
            wB = np.linalg.norm(tr - tl)
            hA = np.linalg.norm(tr - br)
            hB = np.linalg.norm(tl - bl)
            maxW = int(max(wA, wB))
            maxH = int(max(hA, hB))
            if maxW < 100 or maxH < 100:
                continue
            dst = np.array([[0, 0], [maxW - 1, 0], [maxW - 1, maxH - 1], [0, maxH - 1]], dtype=np.float32)
            M = cv2.getPerspectiveTransform(rect, dst)
            warped = cv2.warpPerspective(img, M, (maxW, maxH))
            return warped
    return None


def _enhance_bgr(bgr: np.ndarray) -> np.ndarray:
    # если маленькое изображение — увеличим ×2
    h, w = bgr.shape[:2]
    if min(h, w) < 900:
        bgr = cv2.resize(bgr, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)

    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    lab = cv2.merge([l, a, b])
    bgr = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    gray = _auto_deskew(gray)
    gray = _unsharp(gray)
    # лёгкая адаптивная бинаризация для улучшения текстов
    th = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                               cv2.THRESH_BINARY, 31, 5)
    # смешаем с исходным для сохранения деталей
    mix = cv2.addWeighted(gray, 0.7, th, 0.3, 0)
    return cv2.cvtColor(mix, cv2.COLOR_GRAY2BGR)


def _save_jpg(path: str, img: np.ndarray) -> None:
    cv2.imwrite(path, img, [int(cv2.IMWRITE_JPEG_QUALITY), 94])


def enhance_save_variants(src_jpg_path: str, out_dir: str) -> List[str]:
    """
    Делает набор улучшенных вариантов и поворотов для повышения шансов OCR.
    Возвращает список путей к JPEG-файлам.
    """
    os.makedirs(out_dir, exist_ok=True)
    img = cv2.imread(src_jpg_path)
    if img is None:
        raise RuntimeError("Не удалось прочитать изображение для препроцесса")

    variants = []

    # базовый enhance
    enh = _enhance_bgr(img)
    p0 = os.path.join(out_dir, "enhanced.jpg")
    _save_jpg(p0, enh)
    variants.append(p0)

    # повороты base
    for i, angle in enumerate((90, 180, 270), start=1):
        rot = cv2.rotate(enh, {90: cv2.ROTATE_90_CLOCKWISE,
                               180: cv2.ROTATE_180,
                               270: cv2.ROTATE_90_COUNTERCLOCKWISE}[angle])
        pi = os.path.join(out_dir, f"enhanced_rot{angle}.jpg")
        _save_jpg(pi, rot)
        variants.append(pi)

    # попытка найти документ и сделать warp
    warped = _find_doc_warp(img)
    if warped is not None:
        w_enh = _enhance_bgr(warped)
        pw = os.path.join(out_dir, "warp_enhanced.jpg")
        _save_jpg(pw, w_enh)
        variants.append(pw)

        for angle in (90, 180, 270):
            rot = cv2.rotate(w_enh, {90: cv2.ROTATE_90_CLOCKWISE,
                                     180: cv2.ROTATE_180,
                                     270: cv2.ROTATE_90_COUNTERCLOCKWISE}[angle])
            pi = os.path.join(out_dir, f"warp_enhanced_rot{angle}.jpg")
            _save_jpg(pi, rot)
            variants.append(pi)

    return variants
