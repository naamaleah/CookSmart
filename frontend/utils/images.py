# frontend/utils/images.py
import requests
from PySide6.QtGui import QPixmap, QPainter, QPainterPath, QPen
from PySide6.QtCore import Qt

# Local fallback image used when a remote image fails to load
DEFAULT_IMG_PATH = "frontend/images/default_recipe_image.png"


def download_pixmap(url: str | None, timeout: int = 6) -> QPixmap | None:
    """
    Download an image from a given URL and return it as a QPixmap.

    Args:
        url: The remote image URL to download.
        timeout: Timeout in seconds for the HTTP request.

    Returns:
        QPixmap if the image was successfully downloaded and loaded,
        otherwise None.
    """
    if not url:
        return None
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        pix = QPixmap()
        if pix.loadFromData(resp.content):
            return pix
    except Exception:
        return None
    return None


def get_pixmap_or_default(url: str | None, size: tuple[int, int] = (250, 250)) -> QPixmap:
    """
    Try to load an image from a URL, with a fallback to a local default image.

    Args:
        url: Remote image URL to load.
        size: Target width and height for scaling (maintains aspect ratio).

    Returns:
        QPixmap scaled to the specified size (from URL if successful,
        otherwise the default local placeholder).
    """
    pixmap = download_pixmap(url)
    if not pixmap:
        pixmap = QPixmap(DEFAULT_IMG_PATH)
    return pixmap.scaled(size[0], size[1], Qt.KeepAspectRatio, Qt.SmoothTransformation)


def rounded_pixmap_with_border(
    pixmap: QPixmap,
    size: int = 240,
    radius: int = 22,
    stroke: int = 2,
    color: Qt.GlobalColor = Qt.black,
) -> QPixmap:
    """
    Return a QPixmap cropped into a rounded rectangle with a border.

    Args:
        pixmap: The source QPixmap to render.
        size: The output square size (width = height).
        radius: Corner radius for rounded edges.
        stroke: Border thickness (in pixels).
        color: Border color.

    Returns:
        A new QPixmap rendered as a rounded rectangle with a border.
    """
    result = QPixmap(size, size)
    result.fill(Qt.transparent)

    painter = QPainter(result)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.SmoothPixmapTransform)

    # Define clipping mask for rounded rectangle
    path = QPainterPath()
    path.addRoundedRect(0, 0, size, size, radius, radius)
    painter.setClipPath(path)

    # Draw scaled image inside clipping region
    scaled = pixmap.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
    painter.drawPixmap(0, 0, scaled)

    # Draw border
    painter.setClipping(False)
    pen = QPen(color)
    pen.setWidth(stroke)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)
    inset = stroke / 2.0
    painter.drawRoundedRect(inset, inset, size - stroke, size - stroke, radius, radius)

    painter.end()
    return result
