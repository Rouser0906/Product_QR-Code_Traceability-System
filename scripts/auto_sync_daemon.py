import time, logging, os, sys
sys.path.append('.')
from auto_sync.auto_sync_service import AutoSyncService

os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/auto_sync.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('auto_sync.daemon')

if __name__ == '__main__':
    svc = AutoSyncService()
    logger.info('Starting AutoSyncService from daemon...')
    if not svc.start_service():
        logger.error('Failed to start AutoSyncService. Exiting with code 1.')
        raise SystemExit(1)
    logger.info('AutoSyncService started. Entering supervise loop...')
    try:
        while True:
            time.sleep(5)
            # We could add health checks here and restart if necessary
    except KeyboardInterrupt:
        logger.info('Daemon interrupted. Stopping service...')
        svc.stop_service()
        logger.info('Stopped.')
