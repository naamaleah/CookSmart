# frontend/utils/ingredient_tag.py
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt


def create_ingredient_tag(ingredient_name: str, remove_callback) -> QFrame:
    """
    Create a styled ingredient tag widget with a removable button.

    This widget visually represents an ingredient in the UI, styled
    as a rounded tag with a label and a small ✕ button to remove it.

    Args:
        ingredient_name: The name of the ingredient to display.
        remove_callback: Function to call when the ✕ button is clicked.

    Returns:
        A QFrame containing the label and the remove button.
    """
    tag = QFrame()
    tag.setStyleSheet("""
        background-color: rgba(251, 196, 11, 100);
        border-radius: 12px;
        padding: 0px;
        margin: 0px;
    """)

    layout = QHBoxLayout(tag)
    layout.setContentsMargins(4, 2, 4, 2)
    layout.setSpacing(4)
    layout.setSizeConstraint(QHBoxLayout.SetFixedSize)

    # Label for ingredient name
    label = QLabel(ingredient_name)
    label.setStyleSheet("font-weight: bold; font-size: 13px; background-color: transparent;")
    layout.addWidget(label)

    # Remove button (✕)
    rm_btn = QPushButton("✕")
    rm_btn.setFixedSize(20, 20)
    rm_btn.setCursor(Qt.PointingHandCursor)
    rm_btn.setStyleSheet("""
        border: none;
        font-weight: bold;
        background-color: transparent;
        color: black;
    """)
    rm_btn.clicked.connect(remove_callback)
    layout.addWidget(rm_btn)

    return tag
