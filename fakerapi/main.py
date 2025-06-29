import os
import time
from logger import logger
from api import API 
from duck_db import DuckDBManager

if __name__ == '__main__':
    logger.info(f'Starting FakerAPI data fetch:')
    
    start_time = time.time()
    api_client = API()

    logger.info(f'Database batch size: {api_client.db_batch_size} records')
    logger.info(f'Target total records: {api_client.total_records_needed}')
    
    try:
        with DuckDBManager("persons_data.db") as db_manager:
            total_inserted = 0
            db_batch_buffer = []
            buffer_memory_estimate = 0  # Rough memory estimation
                
            for api_batch in api_client.fetch_all_data():
                if api_batch:
                    db_batch_buffer.extend(api_batch)
                    
                    logger.info(
                        f'Buffer: {len(db_batch_buffer)} records '
                        f'Target: {api_client.db_batch_size}'
                    )
                    
                    # Insert when buffer reaches target size
                    if len(db_batch_buffer) >= api_client.db_batch_size:
                        logger.info(f'Inserting batch of {len(db_batch_buffer)} records...')
                        insert_start = time.time()
                        
                        inserted = db_manager.insert_batch(db_batch_buffer)
                        total_inserted += inserted
                        
                        insert_time = time.time() - insert_start
                        logger.info(
                            f'Inserted {inserted} records in {insert_time:.2f}s '
                            f'({inserted/insert_time:.0f} records/sec). '
                            f'Total: {total_inserted}/{api_client.total_records_needed}'
                        )
                        
                        # Clear buffer and reset memory estimate
                        db_batch_buffer.clear()
                        buffer_memory_estimate = 0
            
            # Handle remaining records
            if db_batch_buffer:
                logger.info(f'Inserting final batch of {len(db_batch_buffer)} records...')
                inserted = db_manager.insert_batch(db_batch_buffer)
                total_inserted += inserted
                logger.info(f'Final batch inserted: {inserted} records')
            
            # Final statistics
            stats = db_manager.get_german_gmail_users()
            elapsed_time = time.time() - start_time
            
            logger.info('=' * 60)
            logger.info('PROCESS COMPLETED SUCCESSFULLY')
            logger.info(f'Total time: {elapsed_time:.2f} seconds')
            logger.info(f'Total records: {total_inserted} \n')

            logger.info(f"Database statistics:")
            logger.info(f'Among the German population, {db_manager.get_german_gmail_users()}% use Gmail.')
            logger.info(f'The top 3 countries using Gmail are: {db_manager.get_top_three_gmail_users()}')
            logger.info(f'There are {db_manager.get_gmail_users_over_sixty()} people over 60 using Gmail as an email provider')
            logger.info("=" * 60)
                
    except Exception as e:
        logger.error(f'Process failed: {e}')
        raise
