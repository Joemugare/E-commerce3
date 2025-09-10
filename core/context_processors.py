# core/context_processors.py
import logging
from django.conf import settings
from core.models import SiteSettings  # Hypothetical model

logger = logging.getLogger('ecommerce')

def site_settings(request):
    logger.debug("Running site_settings context processor")
    try:
        settings_obj = SiteSettings.objects.first()
        return {
            'SITE_NAME': settings_obj.name if settings_obj else 'Transdigital',
            'SITE_URL': settings_obj.url if settings_obj else 'https://transdigitalsystem.it.com',
            'COPYRIGHT_YEAR': 2025,
        }
    except Exception as e:
        logger.error(f"Error in site_settings: {str(e)}")
        return {
            'SITE_NAME': 'Transdigital',
            'SITE_URL': 'https://transdigitalsystem.it.com',
            'COPYRIGHT_YEAR': 2025,
        }