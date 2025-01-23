from io import BytesIO

from matplotlib import pyplot as plt
from matplotlib.figure import Figure
from PyQt5.QtGui import QPixmap


def create_pixmap(fig: Figure) -> QPixmap:
    try:
        buf = BytesIO()
        fig.savefig(buf, format="png")
        buf.seek(0)
        pixmap = QPixmap()
        pixmap.loadFromData(buf.getvalue())
        plt.close(fig)
        return pixmap
    except Exception:
        return QPixmap()
