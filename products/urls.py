from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, LabelViewSet

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'labels', LabelViewSet, basename='label')

urlpatterns = router.urls
