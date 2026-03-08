import firebase_admin
from firebase_admin import credentials, auth
from core.config import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_firebase_initialized = False

def init_firebase():
    global _firebase_initialized
    if not _firebase_initialized:
        try:
            cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred)
            _firebase_initialized = True
            logger.info("Firebase Admin SDK initialized successfully.")
        except Exception as e:
            logger.warning(f"Failed to initialize Firebase Admin SDK (check credentials): {e}")
            # We don't raise here so the app can still start for demo purposes
            # Real requests requiring auth will fail later

def verify_token(token: str) -> dict | None:
    """
    Verifies a Firebase ID token.
    Returns the decoded token dictionary if successful, or None on failure.
    """
    try:
        # Ensure Firebase is initialized
        init_firebase()
        
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        logger.error(f"Error verifying Firebase token: {e}")
        return None
