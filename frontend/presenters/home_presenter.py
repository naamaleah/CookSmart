# frontend/presenters/home_presenter.py
from PySide6.QtCore import QThreadPool
from services.api import requests
from utils.ai_tip_worker import AITipWorker
from utils.images import get_pixmap_or_default
from config import API_BASE_URL


class HomePresenter:
    """
    Presenter for the Home screen.
    Responsible for:
    - Loading personalized recommendations.
    - Fetching and displaying a short AI tip.
    - Managing callbacks for recipe detail navigation.
    """
    def __init__(self, view, token, userid, open_recipe_detail_callback):
        self.view = view
        self.token = token
        self.userid = userid
        self.open_recipe_detail = open_recipe_detail_callback
        self.threadpool = QThreadPool()

    def init_ui(self):
        """Initialize the home view with recommendations and an AI tip."""
        self.load_recommendations()
        self.load_tip()

    def load_tip(self):
        """Run the AI tip worker in a background thread and display its result."""
        worker = AITipWorker()
        worker.signals.finished.connect(self.view.tip_label.setText)
        self.threadpool.start(worker)

    def load_recommendations(self):
        """Fetch recommended recipes from the API and display them with thumbnails."""
        self.view.clear_recommendations()

        try:
            resp = requests.get(
                f"{API_BASE_URL}/recipes/recommendations/{self.userid}",
                timeout=8
            )
            resp.raise_for_status()
            recipes = resp.json()
        except Exception as e:
            self.view.add_error_label(f"Error loading recipes: {e}")
            return

        # Render recommendation cards in the view
        for recipe in recipes:
            pix = get_pixmap_or_default(recipe.get("thumbnail_url"), size=(240, 240))
            self.view.add_recommendation_card(recipe, pix, on_click=self.open_recipe_detail)
